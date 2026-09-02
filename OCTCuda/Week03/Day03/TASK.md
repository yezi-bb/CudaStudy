# Week 03 / Day 03 — 任务说明

## 今日目标

精读存储与取出 API：当前帧 FFT、U16↔F32、After_Log。

## 必读代码 / 文档

- Get_Current_Frame_FFT_data*
- Get_After_Log_Result
- U16fft↔F32fft 两个 Result API
- GpuHandlingDataThreadController 中相关调用

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Get_Current_Frame_FFT_data`
- `VGPU_Get_Current_Frame_FFT_After_Interpolation_data`
- `VGPU_Get_After_Log_Result`
- `VGPU_Get_U16fft_data_toF32fft_Result`
- `VGPU_Get_F32fft_data_toU16fft_Result`

**功能与实现要点：**

计算用 F32，存盘用 U16；拍照 D2H 当前帧。开源：量化 scale 写入元数据。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 实现 quantize_u16 / dequantize
- 笔记：宿主何时必须 D2H

## 任务参考

- 02 链 C

## 完成标准（DoD）

- [ ] 量化往返误差表
- [ ] 理解存盘路径

## 明日预告

旧数据兼容 API

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
