#include "oct/resample_window.hpp"

#include <cmath>
#include <vector>

namespace oct {

namespace {

constexpr double kPi = 3.14159265358979323846;

inline float lerp(float a, float b, float t) { return a + (b - a) * t; }

}  // namespace

void make_hann(float* w, std::size_t N) {
    // 长度 N=1 时公式退化；防御一把
    if (N <= 1) {
        if (N == 1) w[0] = 1.0f;
        return;
    }
    const double denom = static_cast<double>(N - 1);
    for (std::size_t k = 0; k < N; ++k) {
        w[k] = static_cast<float>(0.5 * (1.0 - std::cos(2.0 * kPi * static_cast<double>(k) / denom)));
    }
}

void resample_window_frame(const std::uint16_t* raw, const float* calib,
                           std::size_t Ls, std::size_t N,
                           ResampleMode mode, float* out) {
    if (raw == nullptr || out == nullptr || Ls == 0 || N == 0) return;

    // 窗系数只算一次（整帧共享）
    std::vector<float> w(N);
    make_hann(w.data(), N);

    for (std::size_t l = 0; l < Ls; ++l) {
        const std::uint16_t* line = raw + l * N;
        float* o = out + l * N;
        for (std::size_t k = 0; k < N; ++k) {
            // 1) 目标位置 f（输出样本 k 在原始像素域的浮点坐标）
            float f = (mode == ResampleMode::Table) ? calib[l * N + k]
                                                    : static_cast<float>(k);

            // 越界兜底：f<0 夹到 0；f>=N 属真实标定越界（异常），夹到 N-1。
            // 注意 f∈[N-1, N)（如端点 k=N-1 处 calib=N-0.5）不夹 → 走 hi 回绕。
            if (f < 0.0f) f = 0.0f;
            if (f >= static_cast<float>(N)) f = static_cast<float>(N - 1);

            // 2) 端点回绕线性插值：hi = (lo+1) mod N（Note §3 约定）
            const std::size_t lo = static_cast<std::size_t>(f);
            const std::size_t hi = (lo + 1 < N) ? lo + 1 : 0;
            const float t = f - static_cast<float>(lo);
            const float x = lerp(static_cast<float>(line[lo]),
                                 static_cast<float>(line[hi]), t);

            // 3) 乘 Hann 窗
            o[k] = x * w[k];
        }
    }
}

}  // namespace oct
