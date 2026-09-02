# Week 11 / Day 03 — 任务说明

## 今日目标

CUDA 实现 μ kernel 骨架。

## 必读代码 / 文档

- BLOCK_DIM

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Calculate_Ipa_Result`

**功能与实现要点：**

shared memory 载入一条 depth；block 内归约/拟合；写 out_mu。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- ipa_mu.cu
- 与 CPU 对比

## 任务参考

- CUDA reduction

## 完成标准（DoD）

- [ ] 小卷 GPU≈CPU

## 明日预告

Mu → 圆图

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
