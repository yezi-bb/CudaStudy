# W14 — VTK GPU Volume（私有学习笔记，约 10 行）

- ThreeDimensionsImageController.cpp：vtkGPUVolumeRayCastMapper + vtkVolumeProperty + PiecewiseFunction(透明度) + ColorTransferFunction；L17-19 三组 10 阶多项式系数做“灰→RGB”组织色；min/max_opacity=全局黑白电平（L37-38）。
- 3D 走 VTK/OpenGL，VGPU 走 CUDA：CUDA 生产体数据，VTK 负责渲染；同卡共享显存（W12 记账含 GL）。
- 加分：CUDA–GL interop（cudaGraphicsGLRegisterBuffer + map）让 GL 直接采样 CUDA 缓冲免拷贝。
