# Week 05 / Day 04 — 任务说明

## 今日目标

精读光灵敏度功率 API（测试用途）。

## 必读代码 / 文档

- VGPU_Data_Power_aline
- VGPU_Vivo_Data_Power_aline
- 宿主调用点

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Data_Power_aline`
- `VGPU_Vivo_Data_Power_aline`

**功能与实现要点：**

对 A-line 功率做统计；与主显示链独立。实现：reduction。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 简单 reduce 或 thrust::reduce
- 与 DSC 链关系笔记

## 任务参考

- warp reduce 教程

## 完成标准（DoD）

- [ ] 能说明为何独立于显示链

## 明日预告

W05 REVIEW + 简历一句草稿

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
