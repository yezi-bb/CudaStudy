# Week 03 / Day 05 — 任务说明

## 今日目标

对照回拉单帧捷径 API；复盘 FFT 周。

## 必读代码 / 文档

- VGPU_Pullback_ProcessData_ToImage
- ImageProcessingController 回拉循环

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Pullback_ProcessData_ToImage`

**功能与实现要点：**

等价于多阶段融合入口；开源可先顺序调用已有 stage 模拟。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- Week03/REVIEW.md
- e2e: window→fft→log
- cudaEvent 计时

## 任务参考

- 01 §2

## 完成标准（DoD）

- [ ] REVIEW + 计时表
- [ ] 融合 API 语义清楚

## 明日预告

Week04 Transpose / DSC

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
