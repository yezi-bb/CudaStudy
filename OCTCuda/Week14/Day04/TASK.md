# Week 14 / Day 04 — 任务说明

## 今日目标

阅读 ThreeDimensionsImageController 中 VTK GPU 体绘制。

## 必读代码 / 文档

- ThreeDimensionsImageController 搜索 GPUVolume / vtk

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `vtkGPUVolumeRayCastMapper（VTK）`

**功能与实现要点：**

3D 走 VTK/OpenGL，与 VGPU 重建分离。加分：了解 CUDA–GL interop 概念。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- notes/W14_vtk.md

## 任务参考

- VTK GPU volume 概述

## 完成标准（DoD）

- [ ] 能说出与 VGPU 边界

## 明日预告

W14 REVIEW + P0 缺口列表

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
