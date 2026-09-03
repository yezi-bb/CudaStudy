# Week05 / Day03 — 学习记录（源码填充版）

> 主题：开源仓串联链 A：Resample→FFT→Transpose→DSC→Enhance→Color。

## 1. 今日目标（回顾）
在 open 工程实现 `run_scan_frame`，中间全程 KeepDevice、末尾 ToHost，输出合成数据生成的 PNG 与各阶段耗时。

## 2. 宿主单帧顺序参考（ImageProcessingController.cpp L505-660 已核对）
```
L511  Resample_For_Scan(doc, raw, win, false)
L521  FFT_Power_Interpolation_Result(doc, 0, power, interp, false)
L534  Transpose(doc, cut_start, cut_end, transpose_mat, false)
L625  DSC(doc, cut_end-cut_start, 1000, dsc_data, 704,704, 0,0, INTER_BILINEAR, false)
L636  Enhancement(704,704, 0, enhance, low,up, gamma, LinearEnhanceType, false)
L651  Gray2Color(mat, 704,704, true)   ← 唯一 ToHost
```

## 3. 开源 host 编排（run_scan_frame 骨架）
```cpp
bool Pipeline::run_scan_frame(const uint16_t* raw_frame, cv::Mat& out_bgr, Timing* t) {
  // 1) H2D raw_frame（若 DMA 已在 device 则跳过）
  // 2) device 内串：
  auto s0 = record();   resampleWindow(dev_in, calib, win, dev_win);      // KeepDevice
  auto s1 = record();   fftLogStage(dev_win, dev_interp);                 // KeepDevice
  auto s2 = record();   transposeCrop(dev_interp, cut_start, cut_end, dev_rect);
  auto s3 = record();   dscBilinear(dev_rect, dev_dsc);                   // 704² float
  auto s4 = record();   enhanceGray(dev_dsc, low, up, gamma, dev_gray);   // uchar
  auto s5 = record();   gray2Color(dev_gray, out_bgr, /*ToHost*/true);
  return true;
}
```
每个 stage 一个 `cudaEvent` 对（同一 stream），产出毫秒表；正确性用“每阶段 CPU golden 抽查”兜底。

## 4. e2e demo 与产物（DoD）
- 输入：合成 raw（正弦/斑块/暗带模拟），**不是公司数据**；
- 输出：`scan_frame.png`（伪彩圆图）+ `stages.csv`（stage 耗时）；
- 结果自查：圆图能看到对应角度/深度的模拟结构；多帧间稳定。

## 5. Stage 耗时表（自填）

| stage | ms/帧 | 备注 |
| --- | --- | --- |
| resample+window | __ | Week02 |
| fft+log(interp) | __ | Week03 |
| transpose+crop | __ | Week04 |
| DSC(bilinear) | __ | Week04 |
| enhance | __ | Week05 |
| gray2color + D2H | __ | 含拷贝 |
| 合计 | __ | 目标实时 <16.7ms@60fps |

## 6. 自测 Q&A
1. 为什么“中间 KeepDevice、末尾 ToHost”是性能原则？→ 每次 D2H 过 PCIe；中间结果只在 device 消费，拷贝是纯浪费。
2. 为什么 raw 可能已经 device 内？→ 采集 DMA/驱动可直写 GPU（映射内存），宿主缓冲只是兜底接口。
3. 时间表放 CSV 的意义？→ 可回归比较每次优化，简历用“X ms→Y ms（-Z%）”是量化证据。
4. 合成数据模拟注意什么？→ 频域必须能量集中在可用深度带（cut 内），否则 DSC 后结构位置看不出对错。
5. 验收“结果图”看什么？→ 结构方位/深度与输入一致、无镜像/旋转、灰度窗合理、无明显伪影。

## 7. DoD 打卡
- [ ] `run_scan_frame` 可跑通并输出 PNG（§4）
- [ ] stage 耗时表已填（§5）

## 明日预告
Power_aline 旁路统计 API。
