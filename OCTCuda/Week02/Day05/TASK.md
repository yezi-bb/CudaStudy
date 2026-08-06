# Week 02 / Day 05 — 任务说明

## 今日目标

Profile 窗核；写 REVIEW；预习 cuFFT。

## 必读代码 / 文档

- vcxproj 中 cufft 链接
- 01 §2 FFT 预览

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `（预备）VGPU_Get_FFT_Power_Result`

**功能与实现要点：**

用 cudaEvent 或 nsys 测 window；记录粗性能。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- Week02/REVIEW.md
- 性能一行表
- 预习 cuFFT PlanMany

## 任务参考

- cuFFT 用户指南 — PlanMany

## 完成标准（DoD）

- [ ] REVIEW 完成
- [ ] 理解 batch=线数 的含义

## 明日预告

Week03 FFT / Log

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
