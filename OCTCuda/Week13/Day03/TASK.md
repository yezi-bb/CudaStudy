# Week 13 / Day 03 — 任务说明

## 今日目标

开源实现双缓冲 + cudaMemcpyAsync + stream 上计算。

## 必读代码 / 文档

- CUDA Streams 文档

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `（对应）少拷贝管线 + 并行拷贝计算`

**功能与实现要点：**

H2D async → kernels → 可选 D2H；双缓冲。用 Nsight Systems 看重叠。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- bench 对比默认流
- 文档化结果

## 任务参考

- Nsight Systems

## 完成标准（DoD）

- [ ] 有重叠证据或写清未重叠原因

## 明日预告

实现开源状态机

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
