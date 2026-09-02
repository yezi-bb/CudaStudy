# Week 04 / Day 02 — 任务说明

## 今日目标

实现 shared-memory tile transpose（含 bank conflict padding）。

## 必读代码 / 文档

- BLOCK_DIM / WARPSIZE

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Transpose`

**功能与实现要点：**

tile 16x16 或 32x32；__shared__ tile[TILE][TILE+1]；与 CPU 比对。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- kernel + 测试
- bank conflict 笔记

## 任务参考

- CUDA Best Practices — shared memory

## 完成标准（DoD）

- [ ] GPU 与 CPU 一致
- [ ] 笔记含 padding 原因

## 明日预告

DSC API 精读

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
