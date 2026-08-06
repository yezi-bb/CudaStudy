# Week 12 / Day 04 — 任务说明

## 今日目标

精读 IPA 前后显存监控及与成像缓冲共生问题。

## 必读代码 / 文档

- IPAAlgorithmController 显存日志
- VGPU_Reallocate_memory 场景
- MainWindow CUDA 保护

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_GetCurrentGPUMemory`
- `VGPU_Reallocate_memory`

**功能与实现要点：**

IPA 与实时成像争用 GPU；需监控与重建。开源：统一 Context 分配器。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 争用与缓解笔记
- allocator 草图

## 任务参考

- Week01 健康 API

## 完成标准（DoD）

- [ ] 面试可讲清争用故事

## 明日预告

写 15 分钟 IPA 口述稿；W12 REVIEW

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
