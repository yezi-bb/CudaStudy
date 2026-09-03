// Week02 Day02 黄金版锁定测试（0 依赖：assert 风格 + 返回码，供 CTest）
// 数据全部在内部用固定种子生成，不依赖文件 IO，保证可复现。
//   Identity 模式：out == raw * hann（强断言）
//   Table 模式：calib = k + 0.5 → out ≈ ((raw[k]+raw[k+1])/2) * hann（回绕）
#include "oct/resample_window.hpp"

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <ctime>
#include <string>
#include <vector>

namespace {

int g_failures = 0;

void check(bool ok, const char* what) {
    if (!ok) {
        std::printf("FAIL: %s\n", what);
        ++g_failures;
    }
}

void check_close(float got, float want, float tol, const char* what) {
    if (!(std::fabs(got - want) <= tol)) {
        std::printf("FAIL: %s  got=%f want=%f (tol=%f)\n", what, got, want, tol);
        ++g_failures;
    }
}

// 固定种子合成 chirp（线性调频，频率随 k 从 f0 扫到 f1）：
//   重采样/插值质量对高频振荡敏感，chirp 比单频 sin 更能暴露插值误差。
//   phase(k) = 2*pi*(f0*k + (f1-f0)*k^2/(2*(N-1)))
//   raw(l,k) = 30000 + 1500*sin(phase) + noise(±100, 固定种子)
std::vector<std::uint16_t> make_synth(std::size_t Ls, std::size_t N) {
    constexpr double kPi2 = 6.28318530717958647692;
    constexpr double f0 = 0.05;    // 起始归一化频率 (cycles/sample)
    constexpr double f1 = 0.40;    // 终止频率
    const double denom = static_cast<double>(N - 1);
    std::vector<std::uint16_t> raw(Ls * N);
    unsigned s = 0x5EEDu;
    auto rnd = [&s]() {
        s = s * 1664525u + 1013904223u;
        return (s >> 8) & 0xFFu;
    };
    for (std::size_t l = 0; l < Ls; ++l) {
        for (std::size_t k = 0; k < N; ++k) {
            const double kk = static_cast<double>(k);
            const double phase = kPi2 * (f0 * kk + (f1 - f0) * kk * kk / (2.0 * denom));
            double v = 30000.0 + 1500.0 * std::sin(phase);
            v += static_cast<double>(rnd() % 201) - 100.0;  // ±100 噪声
            if (v < 0.0) v = 0.0;
            if (v > 65535.0) v = 65535.0;
            raw[l * N + k] = static_cast<std::uint16_t>(v + 0.5);
        }
    }
    return raw;
}

// 打印一帧数值摘要：min/max/mean（Day03 kernel diff 对照用）
void print_summary(const std::vector<float>& out, const char* tag) {
    float mn = out[0], mx = out[0];
    double sum = 0.0;
    for (float v : out) {
        if (v < mn) mn = v;
        if (v > mx) mx = v;
        sum += v;
    }
    std::printf("%s summary: out[%zu] min=%.4f max=%.4f mean=%.4f\n",
                tag, out.size(), mn, mx, static_cast<float>(sum / out.size()));
}

}  // namespace

int main(int argc, char** argv) {
    // 默认小尺寸快检；传 "big" 跑冠脉真实尺寸 Ls=1000,N=2048 并计时（验收 Note §5）
    std::size_t Ls = 8;
    std::size_t N  = 64;
    bool big = (argc > 1 && std::string(argv[1]) == "big");
    if (big) { Ls = 1000; N = 2048; }

    const auto raw = make_synth(Ls, N);

    std::vector<float> w(N);
    oct::make_hann(w.data(), N);

    std::vector<float> out(Ls * N);

    const auto t0 = std::clock();

    // ---- 1) Identity：out == raw*w ----
    oct::resample_window_frame(raw.data(), nullptr, Ls, N,
                               oct::ResampleMode::Identity, out.data());
    for (std::size_t l = 0; l < Ls; ++l)
        for (std::size_t k = 0; k < N; ++k)
            check_close(out[l * N + k],
                        static_cast<float>(raw[l * N + k]) * w[k],
                        1e-3f, "identity out==raw*w");

    // ---- 2) Table：calib = k + 0.5 → 半像素位移插值 ----
    std::vector<float> calib(Ls * N);
    for (auto& c : calib) c = 0.0f;
    for (std::size_t l = 0; l < Ls; ++l)
        for (std::size_t k = 0; k < N; ++k)
            calib[l * N + k] = static_cast<float>(k) + 0.5f;

    oct::resample_window_frame(raw.data(), calib.data(), Ls, N,
                               oct::ResampleMode::Table, out.data());
    for (std::size_t l = 0; l < Ls; ++l) {
        for (std::size_t k = 0; k < N; ++k) {
            std::size_t k1 = (k + 1 < N) ? k + 1 : 0;   // 端点回绕
            float want = (static_cast<float>(raw[l * N + k]) +
                          static_cast<float>(raw[l * N + k1])) * 0.5f * w[k];
            check_close(out[l * N + k], want, 1e-3f, "table half-pixel interp");
        }
    }

    const double dt_ms = (static_cast<double>(std::clock() - t0) / CLOCKS_PER_SEC) * 1e3;

    // ---- 3) 数值摘要（记进 Note，供 Day03 kernel diff 对照）----
    print_summary(out, big ? "table big" : "table");   // 最后跑的是 table 模式
    if (big)
        std::printf("timing: Ls=%zu N=%zu total(identity+table)=%.2f ms\n",
                    Ls, N, dt_ms);

    if (g_failures == 0) {
        std::printf("PASS resample_window (identity + table)\n");
        return 0;
    }
    std::printf("%d check(s) FAILED\n", g_failures);
    return 1;
}
