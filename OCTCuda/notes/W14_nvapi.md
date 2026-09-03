# W14 — NVAPI 温度/显示（私有学习笔记，约 10 行）

- 温度：GpuController::ReadGpuTemperature（NvAPI_Initialize→EnumPhysicalGPUs→GPU_GetThermalSettings）→ SystemDiagnosticsView 轮询，GPU>85℃ 弹“请关机冷却”（2307 信号），CPU/采集卡/光源另有阈值。
- 显示：GPUDisplayConfigController::SetDuplicatedMode/SetExtendedMode（ServiceView L210/L240）做复制/扩展屏工位。
- 边界：VGPU_*=CUDA 计算；NVAPI=驱动级硬件/显示控制；两者独立，别把“工位显示”当算法 GPU 任务。
