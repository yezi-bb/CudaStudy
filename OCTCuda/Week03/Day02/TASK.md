# Week 03 / Day 02 — 任务说明

## 今日目标

开源实现 FftLogStage：PlanMany + Exec + log_power kernel。

## 必读代码 / 文档

- ComplexData 结构体

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Get_FFT_Power_Result`

**功能与实现要点：**

cufftPlanMany(batch=n_alines)；log_power kernel；默认 KeepDevice。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 代码实现
- 与小 N CPU DFT/第三方 FFT 对照

## 任务参考

- cuFFT 文档

## 完成标准（DoD）

- [ ] batch FFT 跑通
- [ ] 小尺寸误差可接受

## 明日预告

U16 压缩与 Current_Frame 取出

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
