# Week 09 / Day 03 — 任务说明

## 今日目标

精读 Continuous 出图 / 单帧更新 / 竞品入口。

## 必读代码 / 文档

- VGPU_Continuous_Clibration_To_Circle_Image
- VGPU_Get_All_Continuous_Calibration_Image
- VGPU_Update_Frame_Continuous_Calibration_Image
- VGPU_C7C8_Get_All_Continuous_Calibration_Image

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Continuous_Clibration_To_Circle_Image`
- `VGPU_Get_All_Continuous_Calibration_Image`
- `VGPU_Update_Frame_Continuous_Calibration_Image`
- `VGPU_C7C8_Get_All_Continuous_Calibration_Image`

**功能与实现要点：**

icut_start 变为每帧数组；Update 只重算一帧；C7C8 为竞品数据入口。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 开源 cuts[] 驱动 render
- 竞品入口笔记

## 任务参考

- 02 数据流

## 完成标准（DoD）

- [ ] 能解释为何需要 Update 单帧

## 明日预告

开源多帧 cut + 拼接 demo

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
