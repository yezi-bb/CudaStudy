# Week 01 / Day 03 — 任务说明

## 今日目标

掌握 CUDA 健康监控与「DL 后重建显存」语义。

## 必读代码 / 文档

- VGPU_GetCudaErrorStatus / GetCurrentGPUMemory / ResetCudaMemory / Reallocate_memory 声明
- MainWindowView.cpp 搜索 VGPU_GetCuda / Memory / Reset
- IPAAlgorithmController.cpp 中显存日志包装调用

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_GetCudaErrorStatus`
- `VGPU_GetCurrentGPUMemory`
- `VGPU_ResetCudaMemory`
- `VGPU_Reallocate_memory`

**功能与实现要点：**

GetCudaErrorStatus ← 错误探测；GetCurrentGPUMemory ← cudaMemGetInfo；
Reset ← 设备复位后必须重新 Allocate；Reallocate ← 分析/DL 占用后恢复成像缓冲。
开源：check(err)、vram_snapshot()、safe_reinit()。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 写决策树：何时 Reset vs 仅 Reallocate
- 在开源草稿实现 cuda_utils.hpp（可先桩实现）

## 任务参考

- CUDA Error Handling 文档/最佳实践

## 完成标准（DoD）

- [ ] 能讲清 MainWindow 保护与 IPA 前后打显存日志的原因
- [ ] notes 中有决策树

## 明日预告

搭建开源仓 CMake 骨架

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
