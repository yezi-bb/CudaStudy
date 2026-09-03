# Week08 / Day01 — 学习记录（源码填充版）

> 主题：自动回拉造影剂（介质）检测——`VGPU_Contrast_MediumCheck5` vs `VGPU_Contrast_MediumCheck_Afd` 的触发时机与参数差异。

## 1. 今日目标（回顾）
搞清两类造影剂检测 API 在哪两种“冲洗验证”状态下被调、用同一张图、为什么 AFD 走 8 参版、公开侧如何用“管腔带亮度/间隙统计”做等价 CPU 学习实现。

## 2. API 原型（真实声明，行号已核对，VGPU_Process.cuh）
```cpp
// L303  10 版新介质冲洗识别算法（阈值内聚，只留 3 个输入）
bool VGPU_Contrast_MediumCheck5(float ground_noise, double catheterCutHeight, int currentFrames);
// L305-306 AFD 版：isSmoke 区分普通冲洗/烟雾冲洗，4 个外部阈值便于调参与 UI
bool VGPU_Contrast_MediumCheck_Afd(float ground_noise, double catheterCutHeight, int currentFrames, bool isSmoke,
    float bright_threshold, float gap_threshold1, float gap_threshold2, float gap_threshold3);
// L297 配套：CheckImageInfo() 返回 0=算法阈值问题 / 1=硬件问题
```
解读：
- `ground_noise`：宿主固定传 0（底噪以内部估计为准，公开版可换成输入图 min/低分位）。
- `catheterCutHeight`：跳过导管区（近场不参与介质判别，W07 先验复用）。
- `currentFrames`：宿主传递增的 `m_check_frame_index`（算法可能做多帧确认）。

## 3. 宿主触发时机（真实，HandleDataOfRecording，L674 起）
| 状态 | 判定 | 图来源 | 调用 | 结果去向 |
| --- | --- | --- | --- | --- |
| 冲洗验证 `EVerifyPurgeState` | TriggerType=="Automatic" && !m_is_verifypurge_success | `VGPU_Transpose_CheckImage(…, 0, m_gpu_imagme_points_number_after_fft_length, …)`（L762，**全 FFT 深度**而非 cut 带） | AFD&&use→`Contrast_MediumCheck_Afd(0,cutH,m_check_frame_index,false,bright,gap1..3)`（L767）；否则 `Check5(0,cutH,m_check_frame_index)`（L772） | `m_is_verifypurge_success`（L773），`m_check_frame_index++`（L774） |
| 烟雾冲洗 `ESmokeTestCheckState` | 同上（另一状态） | 同样 Transpose_CheckImage 全深度（L794） | Afd：`isSmoke=true` + Smoke 阈值组（L799-800）；否则 Check5（L805） | 同 L808 `++` |
> 每次检测完（L779/L813）仍会走正常 `VGPU_Transpose(cut)` → DSC(L849) → 增强，即**检测不单独占一条链，而是借当前帧同步做**。

## 4. 设计意图
- **为什么 AFD 要多 4 个参数**：`isSmoke + bright + gap1/2/3`——同一内核不同场景（普通生理盐水/烟雾介质）只是阈值不同，避免复制两套 CUDA 代码；UI/配置层可调（GetGlobalSmokeBrightThreshold() 等）。
- **为什么 Check5 只留 3 参**：稳定场景收敛出的“少接口版本”，阈值内聚到 DLL——接口演进两种路线并存（W07 已见同款：枚举收敛 + _cs 测试版）。
- **gap 的含义（公开推理）**：介质/造影剂在管腔内形成的“间隙”结构（血液/介质液柱间暗带）宽度与数量，bright 是整体亮度基线——组合成“当前冲洗程度”的分类特征。

## 5. 开源学习实现（cpu_medium_check，落点 OCTCudaProject）
```cpp
// 输入：全深度 transpose 方图（H=FFT点数, W=线数, float log 后）
struct MediumResult { bool ok; double bright_mean; double gap_stat; };

MediumResult cpu_medium_check(const std::vector<float>& mat, int H, int W, int catheter_cut_px) {
    double s = 0; size_t n = 0;
    std::vector<double> col_mean(W);
    for (int c = 0; c < W; ++c) {          // 管腔带：跳过导管区
        double m = 0; int cnt = 0;
        for (int r = catheter_cut_px; r < H; ++r) { m += mat[r*W+c]; cnt++; }
        col_mean[c] = m / std::max(1,cnt);
        s += col_mean[c]; n++;
    }
    double bright_mean = s / std::max<size_t>(1,n);
    // gap_stat：亮度低于 bright_mean*k 的“暗列/暗带”占比（公开简化，阈值 k 自定义）
    int dark = 0; for (double v : col_mean) if (v < bright_mean * 0.5) dark++;
    return { /*ok=*/ dark < W/10, bright_mean, (double)dark / W };
}
```
**学习点**：内核内部在算“整帧聚合标量 + 局部分类”，公开版用列均值近似；产品阈值=黑盒（合规，00 §7），开源只保“可跑、可解释、可测”。

## 6. 自测（用合成数据）
1. 造“全透亮”介质帧（管腔带高亮、无暗带）→ ok=true；
2. 造“造影剂残留”（把一半列调暗）→ ok=false；
3. 改 catheter_cut_px 从 0→真实导管高：对比排除导管前后分类稳定性（导管本身高亮会污染 bright_mean）。

## 7. 自测 Q&A
1. 为什么用“全深度”Transpose_CheckImage 而普通链用 cut 带？→ 检测要看管腔内完整介质柱，cut 带只服务成像视野，二者窗口不同（L762 vs L779）。
2. Automatic 触发限定意义？→ 只有自动冲洗程序才需要算法验收；手动流程由操作者目视（GetTriggerType()=="Automatic"）。
3. m_is_verifypurge_success 何时被清零？→ 进入对应冲洗状态时置 false（状态机驱动），成功后置 true 推进下一状态。
4. 失败会阻塞实时链吗？→ 不会死锁：__except 捕获结构化异常仅 return 当前帧，下帧照常；但若一直失败，宿主停留在验证状态，由 UI 提示。
5. AFD 与 Check5 怎么选？→ 运行时开关 `GetIsNeedAFD() && GetGlobalCurrentUseAfdStatus()`，其余帧同路径——配置驱动分支而非两套代码。

## 8. DoD 打卡
- [ ] cpu_medium_check 实现 + 两组合成帧自测通过
- [ ] 能口述 L755-786 完整时序（图源→选 API→结果→自增帧号→继续出图）

## 明日预告
导管折断检测 `VGPU_CheckCatheterBreakDetection`（Scan 态，L541-555）与公开的“异常能量/结构特征”。
