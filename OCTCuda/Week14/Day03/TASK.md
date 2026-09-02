# Week 14 / Day 03 — 任务说明

## 今日目标

阅读 NVAPI 温度与多屏配置（广度，非 compute 核心）。

## 必读代码 / 文档

- GpuController.cpp/.h
- GPUDisplayConfigController.cpp/.h（摘要）

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `（NVAPI，非 VGPU）`

**功能与实现要点：**

工位显示与温度监控；与成像 compute 分离。开源不必复现。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- notes/W14_nvapi.md（约 10–20 行说明即可）

## 任务参考

- NVAPI 文档目录

## 完成标准（DoD）

- [ ] 能区分 compute vs display 控制

## 明日预告

VTK GPU Volume

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
