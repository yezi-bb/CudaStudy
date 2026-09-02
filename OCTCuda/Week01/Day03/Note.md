# Week 01 / Day 03 — 学习记录

> 任务：CUDA 健康监控与「DL 后重建显存」。  
> 源：`VGPU_Process.cuh` 同 region 后四个接口；`01_API接口全解.md` §1；`02_数据流与调用链.md`「显存与错误旁路」。  
> `MainWindowView.cpp` / `IPAAlgorithmController.cpp` **不在本学习仓**，宿主行为按文档与头文件注释推断。

## 1. 核心结论

Day02 的 Allocate/Free 管的是「缓冲从哪来、何时还」。本日四个 API 管的是 **缓冲还健不健康、被别人占了怎么办**。

```text
横切旁路（02）：
  任意重计算前:  GetCurrentGPUMemory / Check_pullback_Data_memory
  计算中异常:    GetCudaErrorStatus → UI 可关机保护
  DL / 分析之后: Reallocate_memory          ← 上下文还活着，只重建成像缓冲
  严重故障:      ResetCudaMemory → 再 Allocate  ← 上下文已毁，指针全部作废
```

两件不同的事，不要混：

| | `Reallocate_memory` | `ResetCudaMemory` |
|--|---------------------|-------------------|
| 上下文 | 仍有效 | `cudaDeviceReset` 后整进程 CUDA 状态清空 |
| 旧 device 指针 | 自己 Free 再 malloc，形状不变 | **全部悬空**，禁止再 `cudaFree` 旧指针 |
| 典型原因 | DL/IPA 占显存、成像缓冲被挤掉 | sticky error、非法访存、launch 失败后上下文不可恢复 |
| 之后 | 可继续 Scan | **必须重新 Allocate**（Reset 不带尺寸参数） |

医疗 UI 上 Reset 是最后手段：同一进程里 OpenCV CUDA / TensorRT / 显示互操作也会一起死。

## 2. 四个 API

头文件注释：

```cpp
// 深度学习算法调用完毕后，再次重新分配计算显存
bool VGPU_Reallocate_memory();

// 获取cuda错误状态 返回false代表异常，返回true代表正常
bool VGPU_GetCudaErrorStatus();

void VGPU_GetCurrentGPUMemory(double& total_memory, double& free_memory, double& used_memory);

// 计算过程出现cuda异常时，重置当前进程显存
bool VGPU_ResetCudaMemory();
```

### 2.1 `VGPU_GetCudaErrorStatus`

| 项 | 内容 |
|----|------|
| **语义** | `true` = 正常，`false` = 异常（头文件约定，和 CUDA 的 `cudaSuccess==0` 方向相反） |
| **实现假设** | `cudaGetLastError()` 或 `cudaPeekAtLastError()`；kernel 异步，可能还要一次同步才能抓住运行期错误 |
| **宿主** | MainWindow 保护路径；计算中轮询 |

CUDA 错误分两类：

1. **启动错误**（立即出现）：grid/block 非法、空指针启动。`cudaGetLastError` 在 `<<<>>>` 后就能看到。  
2. **运行错误**（异步）：越界、`illegal memory access`。往往要 `cudaDeviceSynchronize` / stream sync 才上报。报过一次后变成 **sticky**：后续几乎所有 CUDA 调用都失败，直到 Reset。

因此「Status 为 false」不等于「这一帧图坏了」，更可能是 **整条 GPU 管线已死**。UI 应停采集、禁止继续调 `VGPU_*`，再决定要不要 Reset。

`cudaGetLastError` 会清错误位，`cudaPeekAtLastError` 只看不清。包装成 Status 时要约定：探测后是否清空。开源建议 Peek 给 UI，真正处理时再 Get。

### 2.2 `VGPU_GetCurrentGPUMemory`

| 项 | 内容 |
|----|------|
| **实现假设** | `cudaMemGetInfo(&free, &total)`；`used ≈ total - free` |
| **单位** | 头文件是 `double`，宿主日志常见 GB；开源自己定并写死（建议字节 + 日志再换算） |
| **局限** | 是整卡视角，含别的进程；不能当本进程精确账本 |

用途不是「算得准」，而是 **趋势**：IPA 前 / IPA 后 / DL 后 free 掉了多少；回拉前够不够装 bulk（Day02：F×L×N 是 GB 级）。

`used = total - free` 含驱动、显示、别的软件。本进程泄漏要用自己记的 `cudaMalloc` 账或 Nsight。

### 2.3 `VGPU_Reallocate_memory`

| 项 | 内容 |
|----|------|
| **注释原话** | 深度学习算法调用完毕后，再次重新分配计算显存 |
| **实现假设** | 记住上次 Allocate 的 Shape；等价 `Free(计算区) + Allocate(同样尺寸)`；可打 peak VRAM 日志 |
| **不需要** | 再传一遍 PIU/线数/N/H/W/F（那些应还在 DLL 的 Parameter Manager 里） |
| **不破坏** | CUDA context、标定若 `Free(false)` 可留下 |

场景：分析/DL（TensorRT 等）在同一 GPU、同一进程里 `cudaMalloc` 大块，成像 bulk 被 `cudaFree` 腾空或碎片化。DL 结束后成像指针失效或空间不够 → **只重建成像缓冲**，不要 Reset。

IPA 也会短暂抬高峰值（FFT 卷 + μ）。争用细节 Week12 Day04 再展开；本日记住：IPA/DL 与 Scan **共生同一块卡**，分析结束要恢复成像池。

### 2.4 `VGPU_ResetCudaMemory`

| 项 | 内容 |
|----|------|
| **注释原话** | 计算过程出现 cuda 异常时，重置当前进程显存 |
| **实现假设** | `cudaDeviceReset()`（慎用） |
| **之后** | 所有 device 指针、cuFFT plan、stream 作废；**必须** `VGPU_Allocate_Parameter_Manager(...)` 全参再走一遍 |
| **之前** | 停 GPU 线程（`GpuHandlingDataThreadController`），不要边 Scan 边 Reset |

Reset 之后旧指针不能 `cudaFree`。宿主应把「已 Allocate」标志清掉，当 Idle。

## 3. 决策树：何时 Reset vs 仅 Reallocate（DoD）

```text
                    需要动显存 / CUDA 状态？
                              │
              ┌───────────────┴───────────────┐
              │ 先 GetCudaErrorStatus         │
              │ 再 GetCurrentGPUMemory        │
              └───────────────┬───────────────┘
                              │
              Status == false（sticky / 非法访存 / 上下文坏）
                              │
                         是 ──► 停 GPU 线程
                              │  UI 关机保护 / 禁止继续 VGPU_*
                              │  VGPU_ResetCudaMemory
                              │  VGPU_Allocate_Parameter_Manager（全参）
                              │  再查 Status；仍失败 → 放弃 GPU
                              │
                         否 ──► 上下文还健康
                              │
                    只是 free 变少 / 成像缓冲被 DL、分析拆掉？
                              │
                         是 ──► VGPU_Reallocate_memory
                              │  （内部：同尺寸 Free+Allocate）
                              │  再打一次 Memory 日志，确认 free 回来
                              │
                         否 ──► 回拉前体积不够？
                              │
                         是 ──► Check_pullback_Data_memory 失败
                              │  → 不要开回拉，不要 Reset
                              │  → 减 F / 关其它 GPU 占用后再查 Memory
                              │
                         否 ──► 正常：继续 Scan / 分析
```

口诀：

- **缓冲没了、卡还活着 → Reallocate**  
- **卡（上下文）死了 → Reset，然后 Allocate**  
- **还没坏、只是空间不够 → 不要 Reset，先查 Memory / 减负载**

## 4. 为何 MainWindow 要保护、IPA 前后要打显存日志（DoD）

本仓无这两份 cpp。按 `01`「宿主：MainWindow、IPA、Background 线程日志」和 `02` 旁路推断如下；对照公司仓时搜 `VGPU_GetCuda` / `Memory` / `Reset`。

### 4.1 MainWindow 保护

实时链在独立 GPU 线程里跑。一旦 sticky error：

- 继续 `Resampling → FFT → DSC` 会连续失败或把进程打崩。  
- 医疗界面不能「图花了还继续采」。`GetCudaErrorStatus == false` 时主窗口应：**停采集、提示、禁止再点回拉/分析、可选走关机保护**。  
- Reset 必须由主窗口协调：先停线程，再 Reset，再 Allocate，最后才允许恢复。不能在成像 kernel 路径里随手 Reset。

保护的是 **进程和患者流程**，不是某一帧图。

### 4.2 IPA（及 DL）前后打 `GetCurrentGPUMemory`

IPA 输入是整卷 U16 FFT，体积 O(F×L×D)，和成像 bulk 抢同一张卡。日志作用：

1. **证明有没有泄漏**：IPA 前 free、IPA 后 free，应对回同一量级。只掉不回就是没 `cudaFree`。  
2. **决定要不要 Reallocate**：IPA/DL 若自己 malloc 大块或把成像池拆了，分析结束后成像指针可能空。日志里 used 仍高 → 调 `Reallocate_memory` 再进 Scan。  
3. **回拉/重计算前的门闩**：`02` 写「任意重计算前」打 Memory。free 不够就不要 `Set_Original_pullback_Data_To_GPU`，避免中途 OOM。

没有前后两条日志，Reallocate 会变成盲调：不知道是泄漏、碎片，还是 DL 还没释放。

## 5. 和 Day02 生命周期怎么接

```text
Idle
  → Allocate                         缓冲出生
  → [Scan 循环]                      只拷贝 + kernel
  → （可选）分析 / IPA / DL          显存峰值 ↑；前后打 Memory
  → Reallocate                       恢复成像池（上下文仍在）
  → 若 Status 失败                   Reset → Allocate（当第一次）
  → Free                             缓冲死亡
```

`GetCudaErrorStatus` / `GetCurrentGPUMemory` **不是生命周期节点**，是任何节点上都能做的探针。

## 6. 开源草稿 `cuda_utils.hpp`（桩，Day04 再进工程）

任务允许先桩。对应：`check(err)` / `vram_snapshot()` / `safe_reinit()`。

```cpp
#pragma once
#include <cuda_runtime.h>
#include <cstdio>
#include <cstdint>

namespace oct {

struct VramSnapshot {
    std::size_t total_bytes = 0;
    std::size_t free_bytes  = 0;
    std::size_t used_bytes  = 0;  // total - free，整卡近似
};

inline void check(cudaError_t err, const char* what)
{
    if (err != cudaSuccess) {
        std::fprintf(stderr, "[CUDA] %s: %s\n", what, cudaGetErrorString(err));
    }
}

inline bool cuda_ok()  // 对齐 GetCudaErrorStatus：true=正常
{
    return cudaPeekAtLastError() == cudaSuccess;
}

inline VramSnapshot vram_snapshot()
{
    VramSnapshot s;
    std::size_t free_b = 0, total_b = 0;
    check(cudaMemGetInfo(&free_b, &total_b), "cudaMemGetInfo");
    s.total_bytes = total_b;
    s.free_bytes  = free_b;
    s.used_bytes  = total_b - free_b;
    return s;
}

// Reset 后 Context 全空，调用方必须再 init(shape)
inline bool reset_device()
{
    check(cudaDeviceReset(), "cudaDeviceReset");
    return cuda_ok();
}

// 形状未变：Free 计算区 + 按上次 Shape Allocate（桩：只打日志）
inline bool safe_reinit(/* PipelineContext& ctx */)
{
    auto before = vram_snapshot();
    (void)before;
    // ctx.shutdown(/*free_calib=*/false);
    // ctx.init(ctx.last_shape());
    return cuda_ok();
}

}  // namespace oct
```

Day04 的 `oct::Context` 应暴露 `init` / `shutdown` / `mem_info`；本桩是它的底层。

## 7. 口述要点

- Status 的 true/false 和 `cudaSuccess==0` 相反；false 多半是 sticky，要停 UI。  
- Memory 是整卡近似，IPA 前后打点是为了泄漏和要不要 Reallocate。  
- Reallocate = 同尺寸重建缓冲；Reset = 毁掉上下文，必须全参 Allocate。  
- MainWindow 保护的是整条 GPU 路径，不是单帧。
