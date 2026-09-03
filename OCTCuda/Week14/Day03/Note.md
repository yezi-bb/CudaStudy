# Week14 / Day03 — 学习记录（源码填充版）

> 主题：NVAPI 温度与显示控制（广度；非 VGPU compute 核心）。

## 1. 今日目标（回顾）
能区分：VGPU_*（CUDA 计算）vs NVAPI（NVIDIA 驱动级硬件/显示控制）；温度监控归“工位健康”。

## 2. 宿主真实结构
### GpuController（Controllers/SingleChipControllers，ReadGpuTemperature L45+）
```cpp
#include "nvapi.h"
NvAPI_Initialize();                                     // L51
NvAPI_EnumPhysicalGPUs(hPhysicalGpu, &count);           // L68
NvAPI_GPU_GetThermalSettings(h, NVAPI_THERMAL_TARGET_ALL, &TempSensor); // L76
return TempSensor.sensor[0].currentTemp;                // L79
```
### SystemDiagnosticsView.cpp（监控/告警，L107-207）
- L107：`m_gpu_temperature->ReadGpuTemperature()`（定时轮询）；
- L135-137：GPU/CPU/采集卡温度格式化（85/93/70 阈值）；
- L175-193：GPU>85℃ → `emit OvertemperatureMessageSignal(2307)`（Qt 队列信号，L55）→ 弹窗“请关机冷却”；CPU/采集卡同理（2308/2309）；光源 2310；
- L207：写事件日志。
> 采集卡温度读取仅特定机型支持（L115-133 按机型/采集卡分支：Vivo/DMA/Alazar）。

### GPUDisplayConfigController（ServiceView.cpp L210/L240）
`SetDuplicatedMode()` / `SetExtendedMode()`——NVAPI 把工位显示切成 复制屏/扩展屏（双 4K 工位），返回 NVAPI_OK 检查。

## 3. 分类（核心判断）
| 层 | 用谁 | 职责 | 边界 |
| --- | --- | --- | --- |
| 计算 | VGPU_*（CUDA 内核 DLL） | 成像/重建算法 | 别与“显示”混用 GPU |
| 健康 | NVAPI（GpuController/温度/日志） | 温度/负载巡检 | 只读传感器 + 告警 |
| 显示 | NVAPI/GPUDisplayConfigController | 复制/扩展/分辨率工位 | 决定像素到屏，不改算法数据 |
| 3D | VTK（W14D4） | 体绘制渲染 | OpenGL 与 CUDA 并行共卡 |

## 4. DoD 打卡
- [x] 能区分 compute vs display 控制（§3 表）
- [x] notes/W14_nvapi.md（简短）归档

## 明日预告
ThreeDimensionsImageController 的 VTK GPU 体绘制（3D 视图与 VGPU 的边界）。
