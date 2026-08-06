# Week 14 / Day 02 — 任务说明

## 今日目标

抽样 RecordingThumbnail 与导出中的 GPU 调用子集。

## 必读代码 / 文档

- RecordingThumbnailView.cpp 搜索 VGPU_
- ImportationExportationController.cpp 搜索 VGPU_

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `OneFrame / Handle 系列（实际出现的子集）`

**功能与实现要点：**

缩略图与导出复用同一 DLL 能力。整理调用子集列表。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 调用子集列表笔记

## 任务参考

- 见 `01_API接口全解.md` / `02_数据流与调用链.md`

## 完成标准（DoD）

- [ ] 列表完成

## 明日预告

NVAPI 温度与显示

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
