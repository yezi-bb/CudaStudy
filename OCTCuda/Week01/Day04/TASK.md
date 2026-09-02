# Week 01 / Day 04 — 任务说明

## 今日目标

创建与 AIOCT 隔离的 oct-cuda-pipeline 骨架，对齐模块映射表。

## 必读代码 / 文档

- 01_API接口全解.md §8 开源模块映射
- 00_全局规划.md §6 实现优先级

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `oct::Context ↔ Allocate/Free/Memory（映射）`

**功能与实现要点：**

CMake 启用 CUDA 语言；目录 kernels/ host/ tests/ bench/；
先实现 Context 空壳：init/shutdown/mem_info。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 在 AIOCT 外或 OCTCuda/playground/oct-cuda-pipeline 创建工程
- README 含合规声明 + 模块列表
- 空 main 编译通过

## 任务参考

- CMake CUDA 官方示例
- CUDA Compilation Guide

## 完成标准（DoD）

- [ ] 工程可配置可编译
- [ ] README 含合规段
- [ ] 模块名与 §8 对齐

## 明日预告

吃透 DOCMotionType 与 is_device_to_host；写 W01 REVIEW

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
