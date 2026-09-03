# Week14 / Day04 — 学习记录（源码填充版）

> 主题：ThreeDimensionsImageController 的 VTK GPU 体绘制（3D 组织视图）——与 VGPU 重建的边界。

## 1. 今日目标（回顾）
确认 3D 走 VTK/OpenGL（非 VGPU compute）；理解体绘制与 CUDA 计算如何在一张卡上共存；知道 CUDA–GL interop 概念即加分项。

## 2. 宿主真实结构（ThreeDimensionsImageController.cpp，行号已核对）
### 成员（L31-35，构造时建好）
```cpp
vtkSmartPointer<vtkGPUVolumeRayCastMapper> tissu_mapper_;   // GPU 体绘制映射器
vtkSmartPointer<vtkVolumeProperty>        volume_property_;
vtkSmartPointer<vtkVolume>                volume_;           // 渲染对象
vtkSmartPointer<vtkPiecewiseFunction>     opacity_transfer_function_; // 透明度
vtkSmartPointer<vtkColorTransferFunction> color_transfer_function_;   // 颜色
min_opacity_=GetGlobalDefaultBlackLevel(); max_opacity_=GetGlobalDefaultWhiteLevel(); // L37-38
```
### 色彩 LUT（L17-19）
`color_red_/green_/blue_[10]`：10 阶多项式系数，SetOpacityAndColorTransferFunction 内把灰度 x∈[0,1] 用 9 次多项式合成 RGB（L83-90），映射到 0-255 区间——即“窗宽/窗位 → 组织彩色 3D”的渲染 LUT（对比 W05 Gray2Color 的查表思路）。

## 3. 与 VGPU 的边界（回答“3D 用的什么 GPU”）
| | VGPU_*（CUDA） | vtkGPUVolumeRayCastMapper（OpenGL） |
| --- | --- | --- |
| 做什么 | FFT/Log/DSC/检测/IPA（算数据） | 把 3D 数据体渲染成图（画出来） |
| API | DLL + cudaMemcpy | VTK 管线，内部 GLSL/OpenGL |
| 数据交接 | 宿主把重建好的卷塞给 vtkImageData/纹理 | mapper 用 GPU 光栅化采样 |
| 并行 | compute stream | GL render（CUDA–GL interop 可共享显存缓冲免拷贝） |
产品中两者同卡并存：**CUDA 负责“体”，VTK 负责“看”**；共显存 → 呼应 W12 显存记账需把 GL 纹理也算进去（Context allocator 的预算扩展项）。

## 4. 加分笔记：CUDA–GL interop（一句话）
`cudaGraphicsGLRegisterBuffer → cudaGraphicsMapResources → cudaMemcpy/cudaWrite 设备纹理 → 让 OpenGL 直接采样同一显存`，省一次 D2H+H2D。产品 3D 常为“CUDA 预处理 + GL 直接读同一 buffer”。

## 5. DoD 打卡
- [x] 能说出与 VGPU 边界（§3）
- [x] notes/W14_vtk.md 归档

## 明日预告
W14 REVIEW + P0 缺口列表（00 §6 L115-119）→ Week15 消灭缺口。
