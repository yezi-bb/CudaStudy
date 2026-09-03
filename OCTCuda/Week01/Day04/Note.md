# Week01 / Day04 — 学习记录（源码填充版）

> 用途：创建与 AIOCT 隔离的开源 CMake 骨架，固化模块映射。本节为“怎么搭、长什么样”，编译动作需本机执行。

## 1. 今日目标（回顾）
在 AIOCT 之外建 `oct-cuda-pipeline` 骨架：CMake+CUDA 语言、目录结构、空 `main`、合规 README，模块名与 API 全解 §8 对齐。

## 2. 为什么“隔离”？
- 公司仓代码/注释/常量不能外泄 → 开源仓只放：公开算法原理、自写 kernel、由接口头总结出的“契约说明”。
- 边界：`E:\CUDA\source\Algorithm\vgpu\include\VGPU_Process.cuh` 只当“需求文档/验收 oracle”，不复刻其注释文本。

## 3. 目录骨架（推荐，与 §8 对齐）

```
oct-cuda-pipeline/
├─ CMakeLists.txt            # cmake_minimum_required 3.18; project(oct LANGUAGES CXX CUDA)
├─ README.md                 # 合规段 + 模块列表 + 构建说明
├─ include/oct/              # 公共头：types.h / context.h / pipeline.h / copy_policy.h
├─ kernels/                  # *.cu + *.cuh：resample / fft / transpose / dsc / ...
├─ host/                     # 宿主编排：context.cpp pipeline.cpp device_buffer.cpp
├─ tests/                    # 每 kernel 的正确性单测（golden 比对）
└─ bench/                    # 耗时基准（nsys/ncu 就绪）
```

## 4. 模块映射（对齐 API 全解 §8；先建列出的首批）

| oct 模块 | 对应 DLL API / 主题 | 说明 |
| --- | --- | --- |
| `Context` | Allocate / Free / Memory / Status / Reallocate / Reset | 今天先做**空壳**：`init(shape)/shutdown()/mem_info()` |
| `raw` / `Resample` | `VGPU_Data_Resampling_For_Scan[_Vivo]/For_Pullback` | Week02 |
| `fft` / `log` | `VGPU_Get_FFT_Power_Result`、`Get_After_Log_Result` | Week03 |
| `transpose` | `VGPU_Transpose(_CheckImage)` | Week04 |
| `dsc` | `VGPU_DSC`（scan/ALINE/圆形重建） | Week04 |
| `enhance`/`color` | `VGPU_Image_Enhancement` / `Gray2Color` | Week05 |
| `calibration` / `contrast` / `pullback` / `ipa` | 对应 region | 后置 |
| `CopyPolicy` | `is_device_to_host` 语义 | Day05 |

## 5. 首个 CMakeLists（要点版）

```cmake
cmake_minimum_required(VERSION 3.18)
project(oct_cuda_pipeline LANGUAGES CXX CUDA)
set(CMAKE_CUDA_ARCHITECTURES 86)          # 按本机 GPU 调整(如 75/89)
add_library(oct_core STATIC
    src/context.cpp
    kernels/hello_kernel.cu)
target_include_directories(oct_core PUBLIC include)
find_package(CUDAToolkit REQUIRED)
target_link_libraries(oct_core PUBLIC CUDA::cudart CUDA::cufft)
enable_testing()
add_subdirectory(tests)
```

编译自查：`cmake -S . -B build && cmake --build build`。

## 6. 合规 README 必备段（逐字参考）
```
## Compliance
- 本仓库为个人学习/面试作品，不含任何公司私有代码、数据或注释。
- 模块接口签名参考自公开 API 头文件的『函数名/参数个数/语义』，实现全部为独立编写。
- 输入数据仅使用公开 OCT 数据集或合成数据。
```

## 7. 自测 Q&A
1. CMake 里为什么要 `LANGUAGES CXX CUDA`？→ 让 CMake 启用 nvcc 编译 .cu 并支持 CUDA::cudart/cufft 目标。
2. Context 空壳接口要暴露哪三件事？→ 分配/释放/查显存（init/shutdown/mem_info），对应 Allocate/Free/Memory。
3. tests 目录为什么现在就要留？→ 每 kernel 完成即有 golden 比对，重写契约才有“验收 oracle”。
4. 与 §8 对不齐会怎样？→ 后面各周笔记按该映射引用，容易错位；Day05 写完 CopyPolicy 即闭环首批。

## 8. DoD 打卡
- [ ] 工程可配置可编译（本机执行 cmake+build）
- [ ] README 含合规段（§6）
- [ ] 模块名与 API 全解 §8 对齐（首次对齐后，后续各周以《Week 笔记》验收）

## 明日预告
吃透 DOCMotionType 与 is_device_to_host；写 Week01 REVIEW。
