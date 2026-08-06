# Week 01 / Day 02 — 任务说明

## 今日目标

精读显存生命周期 API，理解管线「先分配再算」模型。

## 必读代码 / 文档

- VGPU_Process.cuh → #pragma region 参数配置与显存分配
- ImageProcessingController.cpp 中 Allocate / Free / SetFunctionConfig / SetCalibrationData 调用处

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Allocate_Parameter_Manager`
- `VGPU_Free_Parament_Manager`
- `VGPU_SetFunctionConfig`
- `VGPU_SetCalibrationData`

**功能与实现要点：**

Allocate：按 PIU 转速、scan/pullback 线数、每线点数、圆图尺寸、回拉帧数、标定表，预分配 device 缓冲与 FFT plan（推断）。
SetFunctionConfig：去 DC/底噪开关。
SetCalibrationData：标定表 H2D。
Free：成对释放；注意 isfree_CalibrationConfig。
开源实现：class PipelineContext { init(shape); shutdown(); }。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 笔记画出 Allocate 参数 → 假想缓冲列表（raw/windowed/fft/rect/circle/color）
- 记录宿主实际传入的尺寸相关全局变量名

## 任务参考

- 01_API接口全解.md §1
- cudaMalloc / cudaFree / cudaMemcpy

## 完成标准（DoD）

- [ ] 写出不少于 6 类 device buffer 的估算公式
- [ ] 能解释回拉帧数为何进入 Allocate

## 明日预告

错误状态、显存查询、Reallocate / Reset

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
