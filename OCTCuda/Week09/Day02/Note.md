# Week09 / Day02 — 学习记录（源码填充版）

> 主题：连续校准 `VGPU_GetContinuousCalibration`——从“整卷一个 cut”进化到“每帧一个 cut”。

## 1. 今日目标（回顾）
搞清单帧校准（W07）与连续校准的差异；`machine_model`/`is_new_catheter` 分别校正什么；输出数组 `catheterCutStartHeight[]` 如何驱动后续每条出图 API。

## 2. API 原型（真实，VGPU_Process.cuh L418）
```cpp
extern "C" __declspec(dllexport) bool VGPU_GetContinuousCalibration(
    int machine_model,        // 0=冠脉 / 1=颈动脉 / 2=颅内
    bool is_new_catheter,     // 当前是否“新导管”类型
    int iheight, int iwidth,  // 单帧高（线数）、宽（深度点数）
    int ipullback_frames,     // 回拉总帧数
    float polarPixelSpacing,  // 极坐标像素间距(mm)
    int* catheterCutStartHeight); // 输出：每帧一个导管裁剪起点（长度为 ipullback_frames）
```

## 3. 宿主真实调用（行号已核对）
| 行 | 调用段要点 |
| --- | --- |
| L6066/L6070（源 A） | 从远端 FFT（或 PCI 近端数据）执行连续校准：`machine_model = EIntracranialOCTDataTyp ? 2 : 0`；`is_new_catheter = GetGlobalCurrentRecordCatheterType()`；尺寸 = 对应 RawToFFT 数据 rows/cols；`ipullback_frames = GetGlobalTotalFrameNumber()`；`polarPixelSpacing`；输出 `GetGlobalCutHeightStart()`（**int 数组，每帧一位**） |
| L6094/L6098（源 B） | 同型调用作用于另一路数据，结果仍写 `GetGlobalCutHeightStart()` |

**关键观察**：
- 宿主把 W07 的“整卷一个 cut”升级成**长度为帧数的数组**（`GetGlobalCutHeightStart()`），此后 DSC/连续校准出图均按帧取 `cut_start[k]`。
- `is_new_catheter` 影响光学常数（新导管曲率/外径不同 → 先验不同）；`machine_model` 影响导管规格与算法能力分支。

## 4. 为什么需要“每帧一个 cut”（物理）
回拉时导管（含光学探头）相对血管壁存在**轴向位移与抖动**，导管壁深度（W07 学的 R_wall）随帧缓慢漂移。整卷统一 cut 会：
- 近端导管较居中、远端漂移后错位 → 圆图“导管区切进管腔/管腔被切掉”。
连续校准给每帧独立起点 → 圆图稳定、后续 IPA（W10-12 需要准确 lumen 边界）受益。

## 5. 开源学习实现（cpu_continuous_calib，落点 OCTCudaProject）
```cpp
// 逐帧做 Day03 的 cpu_catheter_peak，再对“cut 时间序列”做一维平滑（抑制抖动）
std::vector<int> cpu_continuous_calib(const std::vector<float>& volume,
                                      int lines, int depth, int frames,
                                      int search_w /*=120*/)
{
    std::vector<int> cuts(frames);
    std::vector<double> raw(frames);
    for (int k = 0; k < frames; ++k) {
        // 取第 k 帧 → cpu_catheter_peak（W07D3）→ 导管壁行（此处先验项 search 窗口固定）
        CutResult r = cpu_catheter_peak(
            std::vector<float>(volume.begin() + (size_t)k * lines * depth,
                               volume.begin() + (size_t)(k + 1) * lines * depth),
            lines, depth, /*catheter_cut_h_px=*/depth/2, search_w);
        raw[k] = r.ok ? r.r_wall : depth / 2;   // 失败帧用默认先验兜底
    }
    // 时间维中值平滑窗(5)：截断单帧跳变，保留慢漂移
    for (int k = 2; k < frames - 2; ++k) {
        std::array<double,5> w = {raw[k-2], raw[k-1], raw[k], raw[k+1], raw[k+2]};
        std::nth_element(w.begin(), w.begin()+2, w.end());
        cuts[k] = (int)w[2];
    }
    cuts[0] = (int)raw[0]; cuts[1] = (int)raw[1];
    if (frames > 2) cuts[frames-1] = (int)raw[frames-1], cuts[frames-2] = (int)raw[frames-2];
    return cuts;
}
```
**方法论**：连续估计 = “逐帧独立估计 + 时序先验约束（平滑/相邻一致性）”，这是所有 per-frame 参数求解的通用套路。

## 6. 自测
1. 合成 volume：每帧真实 cut 为 `120 + 20*sin(2πk/200)`（慢漂移）+ 帧内高斯噪声；
2. cpu_continuous_calib 输出的 cuts[k] 应跟随正弦趋势；
3. 故意让第 50 帧过暗（cpu_catheter_peak ok=false）→ 该帧被兜底，但平滑后 cuts[50] 接近邻帧（验证鲁棒性）；
4. 用 cuts[] 去驱动渲染（W09D3）看逐帧 cut 稳定圆图。

## 7. 自测 Q&A
1. machine_model 传 0/1/2 是给算法什么信息？→ 各机型导管光学参数与裁剪先验不同（颅内=2 时宿主注释“算法内暂不支持运算”，仍传 2 以便未来版本）。
2. is_new_catheter 从哪来？→ `GetGlobalCurrentRecordCatheterType()`，记录当前导管是否新拆封——影响光学常数与校准先验。
3. 为什么输出是 int* 数组而非单值？→ 每帧独立 cut，长度=回拉帧数；后续 Get_All_Continuous_Calibration_Image / DSC 按帧索引取。
4. 失败帧兜底为什么用 depth/2？→ 中位先验，保证平滑窗有合理输入；产品内部是阈值真值（黑盒，00 §7）。
5. 与 W07 的 catheterCutHeight 关系？→ catheterCutHeight 是先验直径换算（粗），连续校准输出是精修逐帧序列（细），后者可偏离先验但通常在其搜索带内。

## 8. DoD 打卡
- [ ] cpu_continuous_calib 实现，正弦漂移/坏帧两类自测通过
- [ ] 能解释 machine_model、is_new_catheter、输出数组三者的用途

## 明日预告
连续校准出图三兄弟：`Continuous_Clibration_To_Circle_Image`（预处理）、`Get_All_Continuous_Calibration_Image`（全卷）、`Update_Frame_Continuous_Calibration_Image`（单帧更新）与竞品 `C7C8` 入口。
