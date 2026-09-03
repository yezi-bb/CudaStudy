# Week11 / Day02 — 学习记录（源码填充版）

> 主题：CPU 整卷/小卷 μ + 简化掩膜（lumen/labels/media）接入。

## 1. 今日目标（回顾）
把单线拟合扩展为“一卷多帧多线”的 `cpu_volume_mu`；宿主掩膜（int per aline）简化为可直接造测试的版本。

## 2. 宿主掩膜用法（真实）
- 全卷路径 IPAProcessing L182-193：`reshaped_lumen[alines]`、`labels_data[alines]` 整卷 memcpy 自 `DicomModel.m_pre_ipa_analysed_result`（int 每 aline）；
- 单帧路径 ProcessingOneFrame L355-374：只拷 `frame_id*theta` 起的一段（每帧 theta 条）；
- media=100 常量实参（L242/393）——宿主不传数组只传标量（04 in_reshaped_media 形参为 int）；
- 语义（公开推理，含 cuh L426-429 注释）：lumen=每条 A-line 的管腔边界（拟合起点），media=管腔外(+100)终止，labels=健康/非健康参与位。

## 3. 简化掩膜约定（开源）
```cpp
// 每条 aline 两个标量，不建模真实轮廓（教学用）：
//   lumen_b[aline] ∈ [0, depth) ；media_end = min(lumen_b+MEDIA_OFFSET, depth)
//   label[aline]   ∈ {0,1}  0=跳过
constexpr int MEDIA_OFFSET = 100;            // 对应宿主 media=100
```

## 4. 实现 cpu_volume_mu（落点 OCTCudaProject/oct/Ipa）
```cpp
// 卷布局：volume[frame][theta][depth]（theta=每帧线数, depth=深度）
// 输出：mu_vol 同布局 float*；line_mu[frame*theta]
void cpu_volume_mu(const std::vector<float>& logI, int frames, int theta, int depth,
                   const std::vector<int>& lumen_b, const std::vector<int>& labels,
                   float* mu_vol, float* line_mu, float noise_level)
{
    for (int f = 0; f < frames; ++f)
        for (int a = 0; a < theta; ++a) {
            int idx = f*theta + a;
            const float* line = &logI[((size_t)f*theta + a) * depth];
            float* omu = &mu_vol[((size_t)f*theta + a) * depth];
            if (labels[idx] == 0) { line_mu[idx] = 0; continue; }
            int media_end = std::min(lumen_b[idx] + MEDIA_OFFSET, depth);
            ALineMu r = cpu_aline_mu(line, depth, lumen_b[idx], media_end, noise_level);
            line_mu[idx] = (float)r.mu;
            // μ(z) 体：把每窗估计铺到窗内（简版：全线均值近似铺开，供 W11D4 出图）
            for (int z = lumen_b[idx]; z < media_end; ++z) omu[z] = (float)r.mu;
        }
}
```

## 5. 掩膜单测
1. label=0 的线：mu 恒 0、line_mu=0（跳过生效）；
2. lumen_b=200：z<200 的 mu 为 0（仅在 lumen 外拟合生效）；
3. media 截断：lumen_b 靠近 depth 时窗口数变少、不出伪 μ；
4. 双带合成卷：深度 300-600 用 μ=0.9、600+ 用 μ=1.8 → line_mu 分段跟随（帧方向沿卷做 20 帧验证布局）。

## 6. 布局一致性自检（对应宿主）
- 掩膜/line 索引 = f*theta + a；宿主 L367-370 单帧段偏移 frame*theta → 与开源一致；
- μ 体帧外层；宿主 miu_gray_array 偏移 i*rows*cols（W10D3）→ 一致。

## 7. DoD 打卡
- [ ] cpu_volume_mu + 掩膜单测 4 项通过

## 明日预告
CUDA kernel（ipa_mu.cu）：一 A-line 一 block、shared 载入、块内滑动拟合，与 CPU 结果对比。
