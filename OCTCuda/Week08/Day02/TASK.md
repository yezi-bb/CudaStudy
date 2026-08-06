# Week 08 / Day 02 — 任务说明

## 今日目标

精读 CheckCatheterBreakDetection。

## 必读代码 / 文档

- VGPU_CheckCatheterBreakDetection
- ImageProcessingController 调用与 out_CheckImage

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_CheckCatheterBreakDetection`

**功能与实现要点：**

异常模式识别并输出检查图。开源：简化能量/结构异常特征。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 假想特征列表
- 可选 CPU 原型

## 任务参考

- 01 §4

## 完成标准（DoD）

- [ ] 特征列表 + 链上插入点

## 明日预告

guidingDetectOneFrame

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
