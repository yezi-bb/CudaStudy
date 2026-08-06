# Week 03 / Day 01 — 任务说明

## 今日目标

精读 FFT 功率与插值两套 API，画出与 Resampling 的衔接。

## 必读代码 / 文档

- VGPU_Get_FFT_Power_Result / Interpolation_Result
- ImageProcessingController 中紧接 Resampling 的调用

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Get_FFT_Power_Result`
- `VGPU_Get_FFT_Power_Interpolation_Result`

**功能与实现要点：**

加窗实数 → R2C FFT → 功率 → log/缩放；Interpolation 输出 U16；ground_noise 去底。
plan 应在 Allocate 创建并复用。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 笔记：windowed → complex → logpower 缓冲图
- 记录 is_device_to_host 取值

## 任务参考

- 01 §2 FFT
- cuFFT R2C

## 完成标准（DoD）

- [ ] IO 图完成
- [ ] 能解释两 API 差异

## 明日预告

实现 cuFFT stage

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
