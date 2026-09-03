#ifndef OCT_RESAMPLE_WINDOW_HPP
#define OCT_RESAMPLE_WINDOW_HPP

#include <cstddef>
#include <cstdint>

namespace oct {

// 重采样模式：标定表给“输出样本在原始像素域的浮点位置”。
//   Identity —— 简化：f(k) = k（练习/自检用）
//   Table    —— f(k) = calib[l*N + k]（产品标定表语义，值来自宿主 SetCalibrationData）
enum class ResampleMode { Identity, Table };

// Hann 窗（长度 N），供外部需要窗数组的场合复用
void make_hann(float* w, std::size_t N);

// 一帧 Resample + Window（CPU 黄金版，Day03 kernel 的验收 oracle）
//   raw    [Ls*N]  U16 原始数据（行主序：同一 A-line 连续）
//   calib  [Ls*N]  float 标定表；mode==Identity 时可为 nullptr
//   out    [Ls*N]  float 输出
//   算法：out[l*N+k] = interp(raw 于 f(k) 处) * hann[k]，
//         插值用 lo=floor(f), hi=lo+1（端点回绕 mod N），t=f-lo 线性插值。
void resample_window_frame(const std::uint16_t* raw, const float* calib,
                           std::size_t Ls, std::size_t N,
                           ResampleMode mode, float* out);

}  // namespace oct

#endif  // OCT_RESAMPLE_WINDOW_HPP
