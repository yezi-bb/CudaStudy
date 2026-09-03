# Week08 / Day03 — 学习记录（源码填充版）

> 主题：回拉 guiding 检测 `VGPU_guidingDetectOneFrame`——判定回拉时导管是否已到达“引导位”，只用于 AFD 回拉。

## 1. 今日目标（回顾）
搞清 guiding 检测为什么用“逐帧累积向量 avgPixels + 阈值/窗口 + 总帧数”这种接口设计；写 CPU 公开版“滑动均值到达检测”。

## 2. API 原型（真实声明，VGPU_Process.cuh L313）
```cpp
bool VGPU_guidingDetectOneFrame(int startRow, double threshold, int window,
    std::vector<double>& avgPixels, int totalFrame);
```
解读（公开推理，与宿主用法互证）：
- `startRow=10`（宿主实传）：跳过转置图最上面 10 行（导管/起始沿区）；
- `threshold` / `window`：宿主取 `GetGlobalGuidingDetectThreshold() / GetGlobalGuidingDetectWindow()`；
- `avgPixels`：**宿主持久的“逐帧统计累积”容器**——GPU 端每帧把当前帧某窗口均值 push_back 进来，多帧序列形成信号曲线；
- `totalFrame`：宿主取 `m_pullback_total_frame_numer`（按回拉长度类型设定的帧总数，如 40/55/60/75/80mm 对应不同总帧，宿主 SetCurrentPullbackLengthType L1091 附近取 `g_pullbackXX_total_frams_number_`）——用于把“当前在第几帧”归一化，判定到达位置。

## 3. 宿主调用（真实，HandleDataOfRecording 内 EPullbackRecordState 分支，L821-836）
```cpp
else { // 非造影剂状态（含 EPullbackRecordState）
    if (EPullbackRecordState == m_image_processing_state) {
        // 仅 AFD 回拉且本次需要 guiding 判定
        if (GetIsNeedAFD() && GetGlobalCurrentUseAfdStatus() && m_is_need_guidingDetect) {
            if (VGPU_guidingDetectOneFrame(10,
                    GetGlobalGuidingDetectThreshold(), GetGlobalGuidingDetectWindow(),
                    m_avgPixels, m_pullback_total_frame_numer))   // L828
            {
                m_avgPixels.clear();
                vector<double>().swap(m_avgPixels);               // 释放容器（L831）
                m_is_guidingDetect_success = true;                // 全局置成功
                m_is_need_guidingDetect = false;                  // 只判一次（L833）
            }
        }
    }
    /* 仍继续正常 Transpose(cut)→DSC→增强出图（L838+）*/
}
```
三个关键设计：
1. **“到达”是过程事件**：不是单帧特征，而是连续帧信号（帧序列）的形态变化 → 用累积向量 + 到达判定；
2. **成功即释放**：`vector<double>().swap` 释放容器内存（不阻塞、不残留）；
3. **与造影剂检测同构**：都“嵌在 EPullbackRecordState 帧链里同步算”，都不重复触发。

## 4. 物理意义（公开推理）
回拉开始后导管位置不断推进；guiding 是导管到达某参考标记/目标起点的时刻。光信号在该时刻附近发生**可量化的窗均值抬升/突变**。`window` 决定观察窗长、`threshold` 决定触发电平，GPU 端逐帧压缩出一维 `avgPixels` 曲线，检测其“越过阈值”。

## 5. 开源学习实现（cpu_guiding_detect，落点 OCTCudaProject）
```cpp
// 单帧推入 → 由“曲线”判到达。公开版用滑动窗均值近似 GPU 端逐帧统计
struct GuidingState {
    std::vector<double> avg;          // 累积序列（对照宿主 m_avgPixels）
    int totalFrame;
};

// 每帧调用：计算当前帧“第 startRow 行以下、宽度 window 的窗亮度均值”推入 avg
void push_guiding_frame(GuidingState& s, const std::vector<float>& mat,
                        int H, int W, int startRow, int window)
{
    double sum = 0; int cnt = 0;
    for (int r = startRow; r < std::min(H, startRow + window); ++r)
        for (int c = 0; c < W; ++c) { sum += mat[(size_t)r * W + c]; cnt++; }
    s.avg.push_back(sum / std::max(1, cnt));
}

// 到达判定：序列尾部超过基线 threshold（公开简化；totalFrame 用于约束必须在合理帧段内到达）
bool cpu_guiding_detect(GuidingState& s, double threshold, int /*totalFrame*/)
{
    if (s.avg.size() < 30) return false;                 // 数据不足
    double base = s.avg[s.avg.size()-30];                 // 参考基线（最早端）
    double cur  = *std::max_element(s.avg.end()-5, s.avg.end()); // 最近 5 帧峰值
    return (cur - base) > threshold;
}
```
> 说明：此实现示意“跨帧信号形态检测”，不做产品级曲线拟合；`m_avgPixels` 的内部统计结构与 GPU 端不等价，仅方法公开。

## 6. 自测
1. 合成 120 帧：前 60 帧低均值，第 61 帧起均值抬升 2× → 在第 61+5 帧附近应判到达；
2. 全程平稳（无 guiding）→ 始终 false；
3. 观察 `m_avgPixels.clear()+swap` 的语义：到达后重置，防止下一段回拉复用旧曲线。

## 7. 自测 Q&A
1. 为什么需要 totalFrame 参数？→ 不同长度回拉帧数不同，到达判定需知道“总时长”以把绝对帧号变成进度/归一化位置。
2. avgPixels 为什么放宿主而非常量？→ 它是**跨帧状态**（逐帧追加），必须存活于宿主对象生命周期，API 只负责读写该容器（引用传入）。
3. guiding 检测为什么只在 AFD 回拉启用？→ 条件 L825 `GetIsNeedAFD() && GetGlobalCurrentUseAfdStatus()`——AFD 流程对到达时机敏感，普通回拉不需要。
4. 为何成功要 swap 清空而不是 reset size？→ 显式释放内部缓冲区归还内存（`vector<double>().swap` 惯用法），低内存足迹设计。
5. 检测失败会怎样？→ 不置位 success、`m_is_need_guidingDetect` 仍 true，下一帧继续判，直到到达或人工中止。

## 8. DoD 打卡
- [ ] push/cpu_guiding_detect 实现 + 3 组合成序列自测
- [ ] 对比 W08D1/D2：三个检测“何时判、判什么、判完置什么位”各一句说清

## 明日预告
把三个检测整理成“链上检测 hooks”总览（写 notes/W08_detect_hooks.md）并设计开源版 `pre_dsc_checks()`。
