# Week 04 / Day 01 — 任务说明

## 今日目标

精读 Transpose 与深度裁剪；联系导管校准 cut。

## 必读代码 / 文档

- VGPU_Transpose / Transpose_CheckImage
- ImageProcessingController 中 start/end 来源

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Transpose`
- `VGPU_Transpose_CheckImage`

**功能与实现要点：**

转置为显示方图布局并裁掉导管内无效深度。[start,end) 常由校准给出。
实现：shared-memory tile transpose + 行范围裁剪。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- CPU transpose+crop
- CheckImage 用途笔记

## 任务参考

- CUDA tile transpose 经典文章

## 完成标准（DoD）

- [ ] CPU 版正确
- [ ] cut 与校准关系写明

## 明日预告

CUDA tile transpose

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
