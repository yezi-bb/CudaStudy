# Week09 / Day01 — 学习记录（源码填充版）

> 主题：远/近端长段拼接（Lumen Stitching）——两段 FFT 卷按帧范围 + 旋转角合成“超长回拉”。

## 1. 今日目标（回顾）
搞清宿主为什么要把两段 FFT 数据拼成一个长卷、旋转角参数如何参与（A-line 圆周移位）、两段各自取什么 cut；写 CPU 版“旋转 + 拼接”并自测。

## 2. API 声明与注释（真实，VGPU_Process.cuh L384-388 附近）
```cpp
// FFT 域拼接：远/近端数据按各自帧范围裁剪，近端做 A-line 旋转对齐后拼为长卷
extern "C" __declspec(dllexport) bool VGPU_Get_Lumen_Stitching_FFT_Image(
    float* far_data, int far_start_frame, int far_end_frame, int far_cut_start,
    float* near_data, int near_start_frame, int near_end_frame, int near_cut_start,
    int near_rotation_angle, float* out_stitching_data);
// Denoising(U16) 域同名拼接
extern "C" __declspec(dllexport) bool VGPU_Get_Lumen_Stitching_Denoising_Data(/*同上，U16*/);
```
物理背景（公开推理）：当需要比单次回拉更长的成像范围时，宿主采集**两段**（一段为参考/远端 FFT，一段为 PCI/近端补充），把二者沿帧维拼接成连续长卷后再统一进成像链出图。

## 3. 宿主真实调用（IntegrationChannel.cpp L5477-5478，实参逐项）
```cpp
// L5477-5478
VGPU_Get_Lumen_Stitching_Denoising_Data(
    GetGlobalFFTData(),                  // 现有远端 FFT 数据
    far_start_postion, far_end_postion,  // 远端帧范围
    GetGlobalCutHeightStart()[0],        // 远端段用自身 cut[0]
    GetGlobalFFTDataForPCI(),            // PCI 近端数据
    near_start_postion, near_end_postion,// 近端帧范围
    GetGlobalCutHeightStartForPci()[0],  // 近端段用自身 cut[0]
    360 - rotate_angle,                  // 近端旋转角（宿主换算成 0-360 补角）
    stitching_data);                     // 输出拼接体
```
设计要点：
1. **每段用自己的 `cut[0]`**：两段成像时机/导管位置不同，导管裁剪起点各自独立（W07 学的 cut 逐场景差异化在此复用为数组每段取头）。
2. **旋转角只在近端做**：远端为参考系（不转），近端对齐时对 A-line 序做**圆周移位** `rotate_angle` 根线 → 圆图角向对齐。
3. **输出长卷后再走既有链**（后续 HandleAllFFTData/成像），**下游无感**——拼接被封装成“把两个数据源变成一个数据源”。

## 4. 开源学习实现（cpu_rolling_stitch，落点 OCTCudaProject）
```cpp
// 对每帧：按旋转角对“线维度”做圆周移位（滚动 rotate_angle 根线）
void roll_lines_inplace(std::vector<float>& frame, int lines, int depth, int angle) {
    // frame 布局：frame[line*depth + dep]；只滚动 line 轴
    std::vector<float> buf(frame.size());
    int roll = ((angle % lines) + lines) % lines;
    for (int l = 0; l < lines; ++l)
        std::copy_n(frame.data() + l * depth, depth,
                    buf.data() + ((l + roll) % lines) * depth);
    frame.swap(buf);
}

// 拼接：far 帧段 + (旋转后) near 帧段 → 长卷
std::vector<float> cpu_rolling_stitch(const std::vector<float>& far, int far_s, int far_e,
                                      const std::vector<float>& near_, int near_s, int near_e,
                                      int lines, int depth, int near_angle)
{
    auto grab = [&](const std::vector<float>& v, int s, int e) {
        size_t step = (size_t)lines * depth;
        return std::vector<float>(v.begin() + (size_t)s * step, v.begin() + (size_t)(e + 1) * step);
    };
    auto near_seg = grab(near_, near_s, near_e);
    for (size_t f = 0; f < near_seg.size() / (lines * depth); ++f) {
        std::vector<float> fr(near_seg.begin() + f * lines * depth,
                              near_seg.begin() + (f + 1) * lines * depth);
        roll_lines_inplace(fr, lines, depth, near_angle);   // 旋转对齐
        std::copy(fr.begin(), fr.end(), near_seg.begin() + f * lines * depth);
    }
    auto far_seg = grab(far, far_s, far_e);
    far_seg.insert(far_seg.end(), near_seg.begin(), near_seg.end()); // 帧维拼接
    return far_seg;
}
```
> 真实 GPU 端不用整帧搬移：旋转角是编译期/参数，索引重映射即可（每目标线索引=源线索引+angle 模 lines），此处为教学可读版。

## 5. 自测
1. 合成两段各 100 帧（帧内放“标记行”：第 n 帧在 (n mod depth) 处放亮点）；
2. 对 near 段整体旋转 27°（27 根线）后拼接；
3. 验证：拼接卷帧数=帧范围之和、near 段每帧亮点列平移 27 线、帧序连续无跳号；
4. 校验两段帧序号无重叠（far_e < near_s）时的边界：拼接后长度 = (far_e-far_s+1+near_e-near_s+1)×lines×depth。

## 6. 自测 Q&A
1. 为什么旋转只在 near 做？→ 需要把 near 的角向参照系转回与 far 一致；若都转则要先约定共同参照（宿主以 far 为基准）。
2. cut 为什么取 [0] 而不是 per-frame 连续校准值？→ 拼接语义是“两段各按起始帧 cut”快速装配，连续逐帧 cut 是另一条 API 的职责（W09D2/D3）。
3. “下游无感”的价值？→ 拼好的长卷可复用全部既有单卷管线（FFT→Log→Transpose→DSC→增强），只新增一个数据源适配点。
4. CPU 版为何旋转要 O(frame×lines×depth) 拷贝？→ 教学直接搬；GPU 可用 gather 索引重映射省显存带宽，理解“等价变换”即可。
5. 若 far_e+1 != near_s 会怎样？→ 宿主按需求拼接，两段可能是分离采集（如先近端后远端），帧号不一定连续——所以“帧范围”是显式参数而非推断。

## 7. DoD 打卡
- [ ] cpu_rolling_stitch 实现，旋转/帧序/长度三类断言通过
- [ ] 能对着 L5477-5478 逐参解释 8 个实参

## 明日预告
连续校准：`VGPU_GetContinuousCalibration`（机型 + 新导管 → 每帧 `catheterCutStartHeight` 数组）。
