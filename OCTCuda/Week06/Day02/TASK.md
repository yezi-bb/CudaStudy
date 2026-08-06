# Week 06 / Day 02 — 任务说明

## 今日目标

精读全帧 FFT 生成与下载。

## 必读代码 / 文档

- VGPU_Handle_All_Preview_data
- VGPU_Get_All_FFT_data
- 宿主搜索调用

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Handle_All_Preview_data`
- `VGPU_Get_All_FFT_data`

**功能与实现要点：**

设备上批处理全卷；下载 U16 FFT 供分析/IPA。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 开源 batch_fft_volume
- KeepDevice 直至 Get

## 任务参考

- cuFFT 扩展到多帧

## 完成标准（DoD）

- [ ] 能口述链 B 中段

## 明日预告

Handle_All_FFT / Calibration_Image

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
