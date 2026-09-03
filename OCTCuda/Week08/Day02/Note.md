# Week08 / Day02 — 学习记录（源码填充版）

> 主题：导管折断检测 `VGPU_CheckCatheterBreakDetection`——实时 Scan 态的“安全哨兵”，上升沿式单次判定。

## 1. 今日目标（回顾）
搞清导管折断检测在实时扫描链的位置、三级门控（只报一次）、公开默认阈值来自何处；写公开版“能量 + 结构一致性”异常检测。

## 2. API 原型（真实声明，VGPU_Process.cuh L310）
```cpp
bool VGPU_CheckCatheterBreakDetection(float ground_noise, float threshold,
    double condition1, double condition2, cv::Mat& out_CheckImage, bool is_device_to_host);
```
- 与造影剂版不同：**带 `out_CheckImage` 输出**（可选检查图，`is_device_to_host=false` 时不回拷），便于把“算法看到的异常”呈现给工程/算法排查——可测性设计同款（W02/W07 见 `is_device_to_host`）。

## 3. 宿主调用（真实，HandleDataOfScanning 内 Scan 态分支，L541-555）
```cpp
// 三层门控：处于 Scan 成像态 && 功能开启 && 尚未报过折断
if (EScanState == m_image_processing_state
    && GetGlobalIsCheckCatheterBreakStatues()          // 功能开关
    && !GetGlobalCurrentCatheterBreakStatues()) {      // 尚未置位 → 只判一次（上升沿）
    __try {
        // L546 给检查图分配宿主 Mat（FFT点数 × pullback线数）
        m_check_image = cv::Mat::zeros(GetGlobalPointsNumberPerLineAfterFFTlength(),
                                       g_pullback_lines_number_, CV_32FC1);
        // L549 调 GPU：ground_noise=0 + 三个阈值条件（h 文件默认值见下）
        if (!VGPU_CheckCatheterBreakDetection(0, m_threshold, m_condition1, m_condition2,
                                              m_check_image, m_is_save_check_scan_image)) {
            // L552 检出折断 → 全局置位（一次报警，之后不再重复判定）
            SetGlobalCurrentCatheterBreakStatues(true);
        }
    } __except (/*结构化异常保护，不拖垮采集线程*/) { /*...*/ }
}
```
**阈值默认值（ImageProcessingController.h L131-135，镜像已公开）**：
```cpp
float  m_threshold      = 0.3;    // 亮度/能量类阈值
double m_condition1     = 0.0019; // 比值类条件（公开推理：占比/斜率）
double m_condition2     = 90;     // 计数/角度类条件
bool   m_is_save_check_scan_image = false; // 默认不保存检查图（省 D2H）
```
> 这些数值已在头文件内联，本私有笔记可引用；对外仍按 §7 视为产品阈值黑盒。

## 4. 检测物理意义（公开推理，供学习实现）
导管折断的成像表现可归纳为“**整体结构的突然退化**”：
1. 图像整体能量骤降（光进不去/返回异常）→ `threshold=0.3` 类语义；
2. 导管壁亮环（W07 学的水平亮带）模式消失 → 结构一致性（`condition1` 比值）；
3. 连续/跨线异常范围超限 → `condition2` 计数类判定。
即：**先算帧级能量 + 结构统计，再组合条件**。

## 5. 开源学习实现（cpu_break_check，落点 OCTCudaProject）
```cpp
struct BreakResult { bool ok; double energy; double wall_frac; int bad_lines; };

BreakResult cpu_break_check(const std::vector<float>& mat, int H, int W,
                            double t_energy=0.3, double t_ratio=0.0019, int t_bad=90)
{
    // 1) 帧级能量：全局均值（公开近似），骤降则可能折断
    double sum=0; for (float v : mat) sum += v;
    double energy = sum / (H*W);
    // 2) 结构一致性：用“高亮行占比”近似导管壁模式（W07 的逐行投票复用）
    std::vector<int> row_peak(H, 0);
    for (int c = 0; c < W; ++c) {          // 每列找最亮行
        int br = 0; for (int r = 1; r < H; ++r) if (mat[r*W+c] > mat[br*W+c]) br = r;
        row_peak[br]++;
    }
    double wall_frac = *std::max_element(row_peak.begin(), row_peak.end()) / (double)W;
    int bad_lines = 0; for (int v : row_peak) if (v == 0) bad_lines++; // 无峰列数
    bool ok = (energy >= t_energy) && (wall_frac >= t_ratio * W) && (bad_lines < t_bad);
    return {ok, energy, wall_frac, bad_lines};
}
```
**训练你的“检测思维”**：产品三个条件由真实断裂样本标定（合规黑盒）；公开版让你练“把物理现象拆成可算特征 + 阈值组合”。

## 6. 自测
1. 正常帧（W07 合成环）→ ok=true，energy/wall_frac 稳定；
2. 制造“整帧变暗 ×0.1” → energy 骤降 → ok=false；
3. 制造“半幅线断信号”（把一半列清零）→ bad_lines 上升 → ok=false；
4. 观察：2 与 3 哪个条件先触发？→ 说明多条件各守一类异常（能量 vs 结构）。

## 7. 自测 Q&A
1. 为什么“只判一次”而不是持续告警？→ 折断是安全事件，持续刷屏会淹没正常日志；`GetGlobalCurrentCatheterBreakStatues()` 置位后 UI 只需一次提示与停止回拉。
2. is_device_to_host=false 时 out_CheckImage 传了干什么？→ 仅 device 侧分配，D2H 关闭省带宽；需要排查现场才置 m_is_save_check_scan_image=true（W06 学过的按需回拷）。
3. 检测与出图串行吗？→ 该分支在 DSC 前同步执行（L549 之后仍走 Transpose→DSC），GPU 前序 kernel 与检测在同一流，实时性可接受。
4. 为什么阈值放 h 头而不是写死在 cpp？→ 成员默认值可在构造后由 UI/测试改写，与 m_threshold 等同理，便于调参不重新编译。
5. condition1=0.0019 数量级意味着什么？→ 小于 1% 的比例量级，通常是“应满足的极小比值下限”，若低于它判异常——属于归一化比例特征。

## 8. DoD 打卡
- [ ] cpu_break_check 实现，三类合成帧测试全过
- [ ] 画一张“Scan 态三级门控”时序图，能对着讲给同事

## 明日预告
回拉 guiding 检测 `VGPU_guidingDetectOneFrame`（AFD 回拉判定“是否到达引导位”，L823-836）。
