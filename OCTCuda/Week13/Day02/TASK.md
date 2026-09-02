# Week 13 / Day 02 — 任务说明

## 今日目标

划分线程调度 vs 算法调用边界。

## 必读代码 / 文档

- ImageProcessingController 对外方法
- GPU 线程调用哪些方法

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `链 A 主干 API（复习）`

**功能与实现要点：**

线程类不写算法细节；Controller 封装 VGPU_*。开源同样分层。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 重构：PipelineEngine + GpuWorker

## 任务参考

- 00 实现层目标

## 完成标准（DoD）

- [ ] 分层清晰可指给面试官

## 明日预告

CUDA Streams 双缓冲

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
