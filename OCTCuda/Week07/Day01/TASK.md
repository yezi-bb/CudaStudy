# Week 07 / Day 01 — 任务说明

## 今日目标

精读校准枚举与 Catheter_AutoCalibration 主 API。

## 必读代码 / 文档

- GPUCalibrationType / GPULightSourceType
- VGPU_Catheter_AutoCalibration
- ImageProcessingController 校准分支

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Catheter_AutoCalibration`

**功能与实现要点：**

连接校准 vs 术中自动；光源类型；新旧导管；输出校准数据/影响 cut。
公开实现方向：方图径向寻峰估导管壁。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 参数释义表
- 画：校准如何改 Transpose start

## 任务参考

- 01 §3

## 完成标准（DoD）

- [ ] 释义表完成
- [ ] 与 cut 联动写清

## 明日预告

旧 AutoCalibration_* 与 *_cs

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
