# Week 01 / Day 02 — 学习记录

> 任务：精读显存生命周期 API，理解「先分配再算」。  
> 源：`vgpu/include/VGPU_Process.cuh` region「参数配置与显存分配」；`01_API接口全解.md` §1；`02_数据流与调用链.md`。  
> 宿主 `ImageProcessingController.cpp` **不在本学习仓**，尺寸名以 API 形参为准；对照公司仓时在该文件初始化路径搜索同名实参。

## 1. 核心结论：先分配再算

实时 Scan 每秒几十～上百帧。若每帧 `cudaMalloc` / `cudaFree`，开销和碎片都不可接受。

正确模型：

```text
Idle
  │  VGPU_Allocate_Parameter_Manager   ← 一次性 cudaMalloc + cufftPlanMany
  ▼
Allocated（Device 缓冲尺寸锁死）
  │  每帧只做 H2D / kernel /（可选）D2H，不再 malloc
  │  SetFunctionConfig / SetCalibrationData 只改 flag 或一张表
  ▼
Free  VGPU_Free_Parament_Manager       ← 成对 cudaFree + cufftDestroy
```

`DOC_SCAN` / `DOC_PULLBACK_*` 共用这一套已分配缓冲，用 **不同 device 指针或偏移** 切换，而不是换一套 malloc。链 A 写得很清楚：缓冲尺寸在 Allocate 时已定。

开源对应：`class PipelineContext { init(shape); shutdown(); }`（`01` §8 的 `oct::Context`）。

## 2. 四个 API

### 2.1 `VGPU_Allocate_Parameter_Manager`

```cpp
bool VGPU_Allocate_Parameter_Manager(
    int current_piu_speed,
    int noise_max_index, int noise_width,
    int original_data_buf_lines_number,
    int scan_lines_number, int pullback_lines_number,
    int points_per_aline,
    int image_height, int image_width,
    int pullback_total_fram_numer,
    float* calibration_data);
```

| 项 | 内容 |
|----|------|
| **功能** | 按几何与机型，**一次性**分配后续管线全部 Device 缓冲和 FFT plan |
| **输出** | `bool`；副作用是 DLL 内全局 Device 状态 |
| **实现假设** | `cudaMalloc` 多缓冲 + `cufftPlanMany(batch=线数)`；标定表 H2D；按最大回拉帧预留 bulk |

### 2.2 `VGPU_SetFunctionConfig`

`void VGPU_SetFunctionConfig(bool is_need_remove_dc);`

不是分配。全局 flag：FFT/Log 前是否去直流/底噪。实现上存在 Context 里，kernel 读这个开关。

### 2.3 `VGPU_SetCalibrationData`

`bool VGPU_SetCalibrationData(float* calibration_data, int points_per_aline);`

换导管/重标定时 **只更新** `d_calib[N]`（H2D），不必整管线 Free+Allocate。长度必须等于 Allocate 时的 `points_per_aline`。

### 2.4 `VGPU_Free_Parament_Manager`

`bool VGPU_Free_Parament_Manager(bool isfree_CalibrationConfig);`

| `isfree_CalibrationConfig` | 含义 |
|----------------------------|------|
| `true` | 连标定配置一起释放（关机、彻底拆管线） |
| `false` | 释放计算缓冲，保留标定，便于下次只 Allocate 计算区 |

必须与 Allocate **成对**。IPA/DL 若共用同一 GPU，释放顺序要小心（Day03 的 Reallocate / Reset）。

## 3. Allocate 形参 = 宿主必须传入的尺寸名

本仓没有 `ImageProcessingController.cpp`。宿主初始化时传入的就是下面这些形参；公司仓里常见是成员/全局与形参同名或加 `m_` 前缀。对照时按列搜索。

| API 形参（宿主实参名） | 物理含义 | 谁消费 | 典型量级（文档/头文件推断，非实测） |
|------------------------|----------|--------|--------------------------------------|
| `current_piu_speed` | PIU 转速 | 可能影响线速率/缓冲策略 | 机型配置 |
| `noise_max_index` | 底噪统计起点/峰位 | 去底噪 kernel | 与光谱维相关 |
| `noise_width` | 底噪窗宽 | 同上 | |
| `original_data_buf_lines_number` | DMA/原始缓冲线数 | Resampling 输入跨距 | ≥ `scan_lines_number` |
| `scan_lines_number` | 实时一帧 A-line 数 | `DOC_SCAN` 单帧缓冲 | `att_paras.number_theta` 举例 **500** |
| `pullback_lines_number` | 回拉一帧 A-line 数 | `DOC_PULLBACK_*` | 可与 scan 不同 |
| `points_per_aline` | 每线采样点数 **N** | 窗、标定、FFT 长度 | `windata.h` 窗长约 **2048** |
| `image_height` / `image_width` | 圆图高/宽 **H×W** | DSC / 增强 / 伪彩 | 与 `VALID_R=900` 同量级 |
| `pullback_total_fram_numer` | 预留回拉最大帧数 **F** | bulk 体积 | 链 B 举例避免 **550×** 小拷贝 |
| `calibration_data` | Host 侧 λ/k 标定表 | H2D → `d_calib` | 长度 = N |

分析侧别名（IPA `att_paras`，同一套几何）：

| `att_paras` 字段 | 对应 Allocate 几何 |
|------------------|-------------------|
| `number_theta` | ≈ `scan_lines_number` / `pullback_lines_number` |
| `number_depths` | FFT 后每线点数，举例 **1025**（N=2048 的 R2C：N/2+1） |
| `number_frames` | 实际回拉帧，≤ `pullback_total_fram_numer` |
| `number_alines` | `frames × theta` |

符号约定（下文公式）：

```text
N  = points_per_aline
Ls = scan_lines_number
Lp = pullback_lines_number
Lo = original_data_buf_lines_number
H,W = image_height, image_width
F  = pullback_total_fram_numer
D  = N/2 + 1          // R2C 后每线复数/功率点数
C  = 裁剪后深度点数    // Transpose 的 end-start，≤ D
```

## 4. 参数 → 假想 Device 缓冲（≥ 6 类，含估算公式）

Allocate 不是只分一块「显存」，而是按管线阶段预留一组指针。闭源内部布局未知，下面是 **合理复现假设**（`01` 的「如何实现」口径）。

```text
calibration_data[N], Hannwin[N]
        │ H2D（Allocate 或 SetCalibrationData）
        ▼
┌─────────────────────────────────────────────────────────────┐
│ d_calib[N]     d_window[N]     d_noise 相关标量/小缓冲       │
└─────────────────────────────────────────────────────────────┘
        │
        ▼  每帧 Raw（Scan 单帧 / Pullback 写入 bulk 偏移）
┌─────────────────────────────────────────────────────────────┐
│ d_raw_scan     : Ls × N × U16（或 Vivo U8）                 │
│ d_raw_bulk     : F  × Lp × N × U16   ← 回拉帧数在这里        │
└─────────────────────────────────────────────────────────────┘
        │ Resampling + 加窗
        ▼
┌─────────────────────────────────────────────────────────────┐
│ d_windowed     : L × N × float       （L = Ls 或 Lp）       │
└─────────────────────────────────────────────────────────────┘
        │ cuFFT R2C + log/功率
        ▼
┌─────────────────────────────────────────────────────────────┐
│ d_fft_cplx     : L × D × cufftComplex                       │
│ d_power / d_log: L × D × float                              │
│ d_fft_u16      : L × D × U16     （压缩谱，存盘/分析）       │
│ d_fft_vol      : F × Lp × D × U16  ← 回拉整卷 FFT           │
└─────────────────────────────────────────────────────────────┘
        │ Transpose 裁剪
        ▼
┌─────────────────────────────────────────────────────────────┐
│ d_rect         : L × C × float/U8   （方图）                 │
│ d_rect_vol     : F × Lp × C × U8                            │
└─────────────────────────────────────────────────────────────┘
        │ DSC 极坐标
        ▼
┌─────────────────────────────────────────────────────────────┐
│ d_circle       : H × W × float/U8                           │
│ d_circle_vol   : F × H × W × U8     ← 回拉预览圆图           │
└─────────────────────────────────────────────────────────────┘
        │ Enhancement + Gray2Color
        ▼
┌─────────────────────────────────────────────────────────────┐
│ d_enhance      : H × W × U8                                 │
│ d_color        : H × W × 3 × U8     （COLOR_CHANNEL=3）     │
└─────────────────────────────────────────────────────────────┘
另：cufftHandle plan（scan batch=Ls，pullback batch=Lp，可两套）
```

### 公式表（DoD：不少于 6 类）

字节数；`sizeof(U16)=2`，`sizeof(float)=4`，`cufftComplex=8`。

| # | 缓冲 | 估算公式 | 作用 |
|---|------|----------|------|
| 1 | **raw**（扫描单帧） | `Ls * N * 2`（U16）或 `Ls * N * 1`（Vivo U8） | 光谱输入 |
| 2 | **raw bulk**（回拉） | `F * Lp * N * 2` | 整卷一次上传，避免 F 次小拷贝 |
| 3 | **windowed** | `max(Ls,Lp) * N * 4` | 重采样 + Hann 后实数 |
| 4 | **fft** | `max(Ls,Lp) * D * 8`（复数）+ `max(Ls,Lp) * D * 4`（功率/Log） | cuFFT 与 log |
| 5 | **fft vol** | `F * Lp * D * 2`（U16 压缩谱） | 分析/IPA 输入卷 |
| 6 | **rect**（方图） | `max(Ls,Lp) * C * 4`；卷：`F * Lp * C * 1` | Transpose 后 |
| 7 | **circle**（圆图） | `H * W * 4`（DSC float）或 `H * W * 1`（灰度） | 极坐标 |
| 8 | **color** | `H * W * 3 * 1` | 伪彩上屏 |
| + | **calib / window** | 各 `N * 4` | 常量表，几乎不改 |
| + | **cuFFT workspace** | `cufftGetSize` 查询，与 N、batch 有关 | plan 工作区 |

**数量级心算**（代入文档举例 N=2048，D=1025，L=500，F=550，H=W=900）：

- 单帧 raw ≈ 500×2048×2 ≈ **2 MB**
- 回拉 raw bulk ≈ 550×500×2048×2 ≈ **1.05 GB**
- 回拉 FFT U16 卷 ≈ 550×500×1025×2 ≈ **0.54 GB**
- 单帧圆图 float ≈ 900×900×4 ≈ **3.1 MB**

回拉 bulk 是显存大头，所以 **F 必须在 Allocate 时进入**，不能等回拉结束再现分。

## 5. 回拉帧数为什么进入 Allocate（DoD）

1. **预留峰值体积**：`d_raw_bulk` / `d_fft_vol` / 预览方图圆图体数据都含因子 F。启动时就要知道「这台机器最多允许多少帧」，否则回拉中途 `cudaMalloc` 失败无法补救。
2. **避免 550 次小拷贝**：链 B 是 `VGPU_Set_Original_pullback_Data_To_GPU` **整卷一次 H2D**，写入已分配 bulk。Allocate 时 F 定了 stride：`frame_i` 的偏移 = `i * Lp * N`。
3. **与 `VGPU_Check_pullback_Data_memory` 对账**：回拉前检查「实际帧数 ≤ 预留 F、当前 free 显存够」。预留不够只能失败，不能在术中扩。
4. **`DOC_PULLBACK_BEFORE` 逐帧写入**：回拉进行中每来一帧写 bulk 的第 k 段，k 的上限就是 Allocate 的 F。
5. **后续分析复用同一块**：IPA 的 `number_frames` / `number_alines = frames×theta` 建立在这块体积上。

一句话：**F 是体积维度，不是运行时计数器。** 计数器是当前帧号；体积必须先锁死。

## 6. 与 cudaMalloc / Free / Memcpy 的对应

| CUDA Runtime | 落在哪个 VGPU API |
|--------------|-------------------|
| `cudaMalloc` 多缓冲 + `cufftPlanMany` | `Allocate` |
| `cudaMemcpy` H2D 标定表 | `Allocate` 末尾或 `SetCalibrationData` |
| 每帧 `cudaMemcpy` H2D raw | Resampling 等成像 API（Day 后续） |
| 中间阶段 **不做** D2H | `is_device_to_host=false`（Day05） |
| `cudaFree` + `cufftDestroy` | `Free` |

Allocate 失败应视为整条 GPU 管线不可用，宿主不应继续调 Resampling/FFT。

## 7. 开源草稿：`PipelineContext`

```text
oct::Context::init(Shape s):
    N, Ls, Lp, F, H, W ← s
    cudaMalloc raw_scan, raw_bulk, windowed, fft, power,
               fft_vol, rect, circle, color, calib, window
    cufftPlanMany(&plan, ..., batch=Ls)   // pullback 可另 plan
    if (calib_host) cudaMemcpy H2D calib

oct::Context::set_remove_dc(bool)
oct::Context::update_calib(float* host, int n)  // n 必须 == N
oct::Context::shutdown(bool free_calib)
```

Day04 会把该类接到独立仓骨架；本日只锁语义，不写工程。

## 8. 口述要点

- 为什么不能每帧 malloc：实时路径只允许拷贝和 kernel。
- 六类缓冲：raw / windowed / fft / rect / circle / color；回拉再加 bulk 与 vol。
- F 进 Allocate：bulk 体积 = O(F×L×N)，必须预留。
- `SetCalibrationData` 换表不换缓冲；`SetFunctionConfig` 只改 flag。
- `Free(true/false)` 决定标定是否留下。
