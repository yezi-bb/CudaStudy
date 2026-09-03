# Week11 / Day01 — 学习记录（源码填充版）

> 主题：CPU 单 A-line μ 拟合 + 合成指数衰减验证（W10D4 SPEC 落地第一步）。

## 1. 今日目标（回顾）
写 `cpu_aline_mu_test`：合成 I(z)=A·exp(−μz)+noise，用对数最小二乘估计 μ，检查与真值误差。

## 2. 与宿主对照（真实，IPAAlgorithmController.cpp L344-456 = ProcessingOneFrame）
单帧路径（lumen/ICA 轮廓变化触发）正是“一帧的 A-line × 拟合”：
- L348-351：number_frames=1，theta=RawToFFTDataRows()，alines=theta；
- L393：`VGPU_Calculate_Ipa_Result(..., original_fft_image_buffer + frame_id*rows*cols, reshaped_lumen, 100, labels_data, single_frame_miu_gray_array, line_ipa_miu, threshold, 0, isVivoData)`——**指针按帧偏移**，同一内核单帧/全卷共用。
先做 CPU 单线等价，验证拟合正确性后再上 CUDA。

## 3. 实现（落点 OCTCudaProject/oct/Ipa）
```cpp
// 对 log 强度做滑窗最小二乘斜率估计（教学版，对照 W10 SPEC）
constexpr int kMinWin = 41;
constexpr float kEps = 1e-6f;

// 返回: 每条“有效深度”估计 μ 后，线的稳健代表
struct ALineMu { double mu; int valid_win; };

ALineMu cpu_aline_mu(const float* logI, int depth, int lumen_b, int media_end, float noise_level)
{
    int z  = std::min(lumen_b + 1, depth - kMinWin);
    int zE = std::min(media_end, depth);
    std::vector<double> mu_acc; mu_acc.reserve(32);
    // 滑窗推进：成功大步(S=ceil0.5*41=21)，失败小步(F=ceil0.2*41=9)
    const int kS = (int)ceil(0.5 * kMinWin), kF = (int)ceil(0.2 * kMinWin);
    while (z + kMinWin <= zE) {
        double sx=0, sy=0, sxx=0, sxy=0; int n = kMinWin;
        for (int i = 0; i < kMinWin; ++i) {   // x=深度, y=logI
            double x = i, y = logI[z + i];
            sx += x; sy += y; sxx += x*x; sxy += x*y;
        }
        double range = max/min of y…; if (range < noise_level) { z += kF; continue; } // 噪声带
        double denom = n*sxx - sx*sx;
        double slope = fabs(denom) < 1e-9 ? 0.0 : (n*sxy - sx*sy)/denom; // 拟合斜率
        if (slope < 0) {                      // 衰减期望负斜率 → μ=-slope
            mu_acc.push_back(-slope);
            z += kS;
        } else z += kF;                       // 失败小步
    }
    if (mu_acc.empty()) return {0.0, 0};
    double med = /*中位数*/; return {med, (int)mu_acc.size()};
}
```
> 真实 GPU 端一次处理全卷且内部细节不同——本实现只做“方法等价”教学验证（合规，00 §7）。

## 4. 合成测试
```cpp
// I(z) = A·exp(−2·μ·z/points?)  归一：每深度步 δ=0.02mm
for (int z = 0; z < 1025; ++z) I[z] = 200.f * expf(-mu_true * 0.02f * z) + noise(0, 1);
// → 转 log(eps+I) 后送 cpu_aline_mu(lumen_b=50, media_end=600)
```
| μ_true | μ_est（理想） | rel.err |
| --- | --- | --- |
| 0.3 | ≈0.3 | <15% |
| 0.9 | ≈0.9 | <15% |
| 1.8 | ≈1.8 | <15% |
自检点：slope 取负、窗覆盖 >10 个、噪声带跳过。

## 5. DoD 打卡
- [ ] cpu_aline_mu + 合成测试，三档 μ rel.err<15%

## 明日预告
整帧/小卷 μ（cpu_volume_mu）并接入简化 lumen/labels/media 掩膜。
