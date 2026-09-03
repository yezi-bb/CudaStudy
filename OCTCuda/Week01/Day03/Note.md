# Week01 / Day03 — 学习记录（源码填充版）

> 用途：掌握 CUDA 健康监控与「DL 后重建显存」语义。真实行号已核对。

## 1. 今日目标（回顾）
掌握 4 个“健康/恢复”类 API：错误状态、显存查询、Reset（设备级）、Reallocate（管线级重建）。

## 2. 真实声明（VGPU_Process.cuh L211-222）

```cpp
bool VGPU_Reallocate_memory();                    // L212 深度学习算法调用完毕后，再次重新分配计算显存
bool VGPU_GetCudaErrorStatus();                   // L216 false=异常 true=正常
void VGPU_GetCurrentGPUMemory(double& total_memory, double& free_memory, double& used_memory); // L219
bool VGPU_ResetCudaMemory();                      // L222 计算过程出现 cuda 异常时，重置当前进程显存
```

## 3. 宿主真实用法（本机核对）

| 宿主位置 | 行为 |
| --- | --- |
| `MainWindowView.cpp` L1776-1780（`NewOCTRecordingPushButtonSlot` 扫描前自检） | `VGPU_Check_pullback_Data_memory()` + `VGPU_GetCudaErrorStatus()` 都通过才开始扫描；L1824-1826 任一失败写 EventLog「auto shut down」 |
| `MainWindowView.cpp` L2548-2550（从分析界面返回记录态前） | 再次 `VGPU_GetCudaErrorStatus()` 检查，正常才继续；L2662-2665 失败写日志并自动关机 |
| `IPAAlgorithmController.cpp` L534-540（`GPU_GetCurrentGPUMemory(bool bInit, const QString& pos)` 包装） | 调 `VGPU_GetCurrentGPUMemory(total, free, used)` 并 `RUNLOG` 输出「Init/Release + 使用/剩余 MB」，用于 IPA 前后打显存日志 |

注：`VGPU_ResetCudaMemory()` 与 `VGPU_Reallocate_memory()` 在当前宿主代码中**没有直接调用**（保留接口给 DL 联合流程 / 故障恢复），属“防御式导出”。分析侧显存占用来自独立深度学习进程/线程，返回前调用 `VGPU_GetCudaErrorStatus` 验证 GPU 仍健康。

## 4. 语义精讲（怎么实现 → 自己写）

| API | 内部推断实现 | 触发时机 |
| --- | --- | --- |
| `GetCudaErrorStatus` | `cudaGetLastError()` + 自维护错误标志位；false 时宿主报警/关停 | 任何可能撞错的前后 |
| `GetCurrentGPUMemory` | `cudaMemGetInfo(&free,&total)`；`used=total-free`（注意把 MB 换算在宿主或 DLL 内做） | IPA/DL 前后做快照对比 |
| `ResetCudaMemory` | `cudaDeviceReset()` → 进程内所有 context/显存清空 → **必须重新 Allocate**（进程内 plan 一并失效） | 已发生 cuda 异常，进程不想重启 |
| `Reallocate_memory` | 不重置设备，只按原形状参数 **重跑一次内部 Allocate**（cufft plan 重建、缓冲重分）；速度远低于 Reset | DL 借走/归还显存导致池被回收后恢复成像 |

## 5. 决策树（何时 Reset vs 仅 Reallocate）——答案

```
遇到 CUDA 异常(如 cudaErrorMemoryAllocation / driver error)
├─ 只是"我自己的池子被外部挤占/释放" 且 设备仍可用 → 仅 Reallocate（轻量）
├─ 出现 context/设备级错误(需 cudaDeviceReset 才能恢复) → Reset + 全量重新初始化
│     （宿主流程：Reset → 释放宿主侧状态 → 重新 CpuAndGpuMemoryAllocation）
└─ Reset 后仍失败 → 写 EventLog、提示用户重启软件/驱动
```

## 6. 动手任务
- [ ] 已画决策树（§5 参照）
- [ ] 开源草稿 `cuda_utils.hpp`（可桩实现，要求）：
  - `void check(cudaError_t)`（失败打点+可回抛）
  - `void vram_snapshot(const char* tag, bool to_mb=true)`
  - `struct ScopeGuard`/`reset_and_reinit()` 骨架，留 TODO

## 7. 自测 Q&A
1. 为什么 MainWindow 在“开始扫描前”和“返回记录态前”都查一次状态？→ 扫描/回拉前保证 GPU 健康避免启动即错；分析侧（IPA/DL）回来后再验证一次，防止分析过程破坏 context。
2. IPA 前后打显存日志的价值？→ 量化分析模块（IPA/DL）的显存峰值，验证“借显存后归还/重建”策略是否生效，也是面试可讲的“显存水位监控”实践。
3. Reset 与 Reallocate 的核心差异？→ Reset=设备级核爆（context/plan 全没，代价最大）；Reallocate=进程内按需重建计算缓冲（不重设设备）。
4. GetCurrentGPUMemory 的三值从哪来？→ `cudaMemGetInfo`（free/total），used=total-free（注意驱动/其他进程占用会让 used 偏大）。
5. 为什么接口返回 `bool`（状态类）而 Memory 返回 void + 引用输出？→ 状态类成功与否是主流程分支依据；Memory 是“快照数据”，总返回但数据有效性靠调用者判断。

## 8. 疑点 / 待办
- 实际 DL 联合流程里 Reallocate 的调用点（可能在独立 DL 工程，当前仓未含）→ 面试讲“对接约定”即可，不臆断内部。
- 确认宿主日志单位：`IPAAlgorithmController` RUNLOG 输出 “u/f M”，推断 DLL 或宿主已换算 MB。

## 9. DoD 打卡
- [ ] 能讲清 MainWindow 保护与 IPA 前后打显存日志的原因
- [ ] notes 中有决策树（§5）

## 明日预告
搭建开源仓 CMake 骨架。
