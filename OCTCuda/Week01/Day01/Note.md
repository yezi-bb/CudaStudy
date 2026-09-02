# Week 01 / Day 01 — 学习记录

> 对照练习库：`CudaStudy/CudaTool`（`CudaTool.h` / `.lib` / `.dll` + `CudaTool.props`）。  
> OCT 产品库：闭源 `VGPU_Process.dll` + 头文件 `vgpu/include/VGPU_Process.cuh`。

## 1. 核心结论

OCT 主程序**不编译业务 `.cu`**。算法在公司 CUDA 工程里用 nvcc 编成 `VGPU_Process.dll`；Qt/C++ 宿主只 `#include` 头文件、链接 `.lib`、运行时加载 `.dll`。`CudaTool` 是同一模式的缩小版。

h / lib / dll **分两层**：NVIDIA 官方 Runtime/cuFFT 是一层，OCT 业务库是另一层，不是「全是官方的」。

简历不能只写「调用过 `VGPU_Process`」：宿主调用的是 C API，kernel、显存生命周期、`is_device_to_host`、cuFFT plan 都在 DLL 内。能讲清边界与管线，才算理解 CUDA 部分。

## 2. 理论上 CUDA 在干什么

任何 CUDA 程序都是同一条主机–设备循环：

```text
CPU（Host）                          GPU（Device）
─────────────────────────────────────────────────────
1. cudaMalloc 分配显存
2. cudaMemcpy  H→D  上传输入  ──────►  原始光谱 / 图像
3. kernel<<<grid,block>>>()  ────────►  线程并行计算
4. （可选）下一阶段 kernel 接着用 Device 结果
5. cudaMemcpy  D→H  取回结果  ◄──────  FFT / 圆图 / IPA
6. cudaFree
```

对应 OCT 实时 Scan（`02_数据流与调用链.md` 链 A）：

```text
采集线程 DMA 缓冲 (U16/U8)
        │  Host 指针交给 DLL
        ▼
VGPU_Allocate_Parameter_Manager     ← 一次性 cudaMalloc + cuFFT plan
        │
        ▼  中间阶段 is_device_to_host = false（结果留在显存）
Resampling → FFT/Log → Transpose → DSC → Enhancement
        │
        ▼  最后 Gray2Color(..., true)
cv::Mat 上屏
```

`is_device_to_host=false`：**不要每一步都 D2H**，下一阶段 kernel 直接吃上一阶段 Device 缓冲。这是实时成像的关键。

## 3. 工程上为什么先编 DLL 再调用

`<<<>>>` 只能给 **nvcc** 编。Qt 主工程是 MSVC 编 `.cpp`，不能直接写 kernel。产品拆成两份工程：

| 工程 | 编译器 | 产物 | 职责 |
|------|--------|------|------|
| CUDA 库（`VGPU_Process` / 练习 `CudaTool`） | nvcc + MSVC | `.h` + `.lib` + `.dll` | kernel、显存、cuFFT |
| 业务宿主（`ImageProcessingController` 等） | 只 MSVC | `.exe` | 采集、线程、UI、调 `VGPU_*` |

宿主没有业务 `.cu`。头文件是契约，例如：

```cpp
extern "C" __declspec(dllexport) bool VGPU_Allocate_Parameter_Manager(...);
```

`extern "C"` 保证 C++ 不改名，MSVC 能按导入库链接。宿主只看到 `VGPU_DSC(...)` 这类 C 接口，看不到 `__global__`。

练习侧同一调用方式：`MainWindow.cpp` → `CudaTool::LaunchBinaryKernel(...)`。

| OCT 产品 | 练习库 |
|----------|--------|
| `VGPU_Process.cuh` | `CudaTool.h` |
| `VGPU_Process.lib` | `CudaTool.lib` |
| `VGPU_Process.dll` | `CudaTool.dll` |
| `ImageProcessingController.cpp` | `MainWindow.cpp` |

不是「外部随便生成一段代码」，而是用 CUDA 工程把 kernel 编成 DLL；`.cu` 永远在库工程里。

## 4. 这些 h / lib / dll 哪些是官方的

### A. NVIDIA 官方（CUDA Toolkit / 驱动）

| 文件 | 角色 | 典型位置 |
|------|------|----------|
| `cuda_runtime.h`、`vector_types.h`、`cufft.h` | 官方头 | `CUDA\v12.x\include\` |
| `cudart.lib`、`cufft.lib` | 链接导入库 | `CUDA\v12.x\lib\x64\` |
| `cudart64_12.dll`、`cufft64_*.dll` | 运行时 | Toolkit `bin` 或随驱动 |

本学习仓 `OCTCuda/vgpu/include/cuda/` 是 Toolkit 头文件拷贝/钉版本，版权仍是 NVIDIA，不是 OCT 算法。

### B. 公司 / 自己写的业务库（不是官方）

| 文件 | 谁写的 |
|------|--------|
| `VGPU_Process.cuh` / `.lib` / `.dll` | 公司 OCT GPU 算法 |
| `CudaTool.h` / `.lib` / `.dll` | 自己的练习库 |

运行一个 OCT exe，通常要同时有：

```text
IS05.exe
  ├─ VGPU_Process.dll      ← 公司算法（必须自己带）
  ├─ cudart64_12.dll       ← NVIDIA Runtime
  └─ cufft64_*.dll         ← NVIDIA cuFFT（FFT 阶段）
```

缺业务 DLL：找不到 `VGPU_*`。缺 `cudart`：业务 DLL 自己也加载失败。

## 5. 依赖怎么建（三件套）

Windows 静态导入动态库：

```text
编译期：  #include "Xxx.h"     → AdditionalIncludeDirectories
链接期：  链 Xxx.lib           → AdditionalLibraryDirectories + AdditionalDependencies
运行期：  exe 旁有 Xxx.dll     → 构建后 Copy
```

OCT 主工程（`IS05.vcxproj` 中搜 `cudart` / `cufft` / `VGPU_Process`）大致是：

- Include：`Algorithm/vgpu/include` + CUDA Toolkit include
- Link：`VGPU_Process.lib` + `cudart.lib` + `cufft.lib`
- 运行：拷贝 `VGPU_Process.dll`；`cudart`/`cufft` 靠 PATH 或一起拷

练习库 `CudaTool.props` 已把业务库这三步自动化（include / 链 `CudaTool.lib` / Copy dll）。`ExternPro.props` 额外加上官方 `$(CUDA_PATH)\include` 和 `cudart.lib`，因为头文件里直接调了 `cudaMalloc`。

建立顺序：

1. 先用 CUDA 工程编出业务库（Debug/Release、x64、`/MD` 与宿主一致）
2. 确认三件套：`include\*.h`、`lib\x64\{Debug,Release}\*.lib`、`dll\x64\{Debug,Release}\*.dll`
3. 宿主导入 `.props`（或手写等价 include/lib/copy）
4. 本机 Toolkit 版本匹配；运行机有驱动 + `cudart`/`cufft`

## 6. 分层总图

```text
                    NVIDIA 官方
            cuda_runtime.h  cudart.lib  cudart64.dll
            cufft.h         cufft.lib   cufft64.dll
                         ▲
                         │ 库工程内部 #include / 链接
              ┌──────────┴──────────┐
              │  业务 CUDA DLL      │  nvcc 编译 .cu
              │  VGPU_Process.dll   │  真正的 kernel / 显存 / FFT
              │  （或 CudaTool.dll） │
              └──────────▲──────────┘
                         │ 只暴露 C/C++ API
              ┌──────────┴──────────┐
              │  OCT Qt 宿主        │  纯 MSVC，无业务 .cu
              │  ImageProcessing…   │  #include VGPU_Process.cuh
              │  链 VGPU_Process.lib │  运行加载 .dll
              └─────────────────────┘
```

可以「外部生成 DLL，宿主直接调用」——这就是 OCT 的用法。  
不能理解成「不用 CUDA 环境、只丢一个 DLL」：业务 DLL 仍依赖官方 `cudart`/`cufft` 和驱动。

## 7. 公司仓 vs 开源复现仓（一页纸）

| | 公司仓（AIOCT / 本学习对照） | 未来开源仓 |
|--|------------------------------|------------|
| 内核 `.cu` | **无**（在闭源 `VGPU_Process.dll`） | **有**（自己实现等价 kernel） |
| API 头 | `VGPU_Process.cuh` 完整导出 | 对齐语义的自有接口，不抄闭源 DLL |
| 宿主 | Qt 编排：Scan / Pullback / IPA 调用链 | 最小 host：Alloc → 管线 → Free |
| 数据 | 真实采集 / 标定 / 患者数据 | 仅合成数据或公开文献算法 |
| 依赖 | `VGPU_Process` + `cudart` + `cufft` | 仅 NVIDIA Toolkit + 自研代码 |
| 学习方式 | 读 API + 读谁调用 + 推断 Device 生命周期 | CPU 黄金版 → naive CUDA → Nsight |

## 8. Region 函数名索引

源：`OCTCuda/vgpu/include/VGPU_Process.cuh`。本日只建目录，不深入单 API。

### 参数配置与显存分配 — 横切 / 生命周期

- `VGPU_Allocate_Parameter_Manager`
- `VGPU_SetFunctionConfig`
- `VGPU_SetCalibrationData`
- `VGPU_Free_Parament_Manager`
- `VGPU_Reallocate_memory`
- `VGPU_GetCudaErrorStatus`
- `VGPU_GetCurrentGPUMemory`
- `VGPU_ResetCudaMemory`

### 扫描回拉过程计算 — 成像主干

- `VGPU_Data_Resampling_For_Scan` / `_Vivo` / `_For_Pullback`
- `VGPU_Get_FFT_Power_Result` / `VGPU_Get_FFT_Power_Interpolation_Result`
- `VGPU_Pullback_ProcessData_ToImage`
- `VGPU_Get_After_Log_Result` / `old_data_toLog` / `cutfront25` / `Denoising_data_toLog`
- `VGPU_Get_U16fft_data_toF32fft_Result` / `VGPU_Get_F32fft_data_toU16fft_Result`
- `VGPU_Get_Current_Frame_FFT_data` / `_After_Interpolation_data`
- `VGPU_Transpose` / `VGPU_Transpose_CheckImage`
- `VGPU_DSC`
- `VGPU_Image_Enhancement`
- `VGPU_Gray2Color`

### 导管校准相关接口 — 校准检测

- `VGPU_AutoCalibration_new` / `_connect` / `_new_cs` / `_connect_cs`
- `VGPU_Catheter_AutoCalibration`
- `VGPU_CheckImageInfo`

### 自动回拉造影剂检测 — 校准检测

- `VGPU_Contrast_MediumCheck5` / `_Afd`
- `VGPU_CheckCatheterBreakDetection`
- `VGPU_guidingDetectOneFrame`

### 回拉后处理 / 分析预处理 — 批处理

- `VGPU_Check_pullback_Data_memory`
- `VGPU_Set_Original_pullback_Data_To_GPU`
- `VGPU_Handle_All_Preview_data` / `VGPU_Get_All_FFT_data`
- `VGPU_Handle_All_FFT_data` / `VGPU_Handle_All_Calibration_Image`
- `VGPU_OneFrameRawData_To_Image` / `VGPU_PullbackRawData_To_FFT_Data` / `_To_Image`
- `VGPU_C7C8_PullbackFFT_Data_To_Image` / `VGPU_PullbackDcm_Data_To_Image`
- `VGPU_Set_all_U16_FFT_data_to_Gpu` / `VGPU_Set_all_FFT_data_to_Gpu`
- `VGPU_CalculatedContrastRange` / `VGPU_Hnad_One_Frame_Data`
- `VGPU_Data_Power_aline` / `VGPU_Vivo_Data_Power_aline`
- `VGPU_Get_Lumen_Stitching_FFT_Image` / `_Denoising_Data`
- `VGPU_Continuous_Clibration_To_Circle_Image` / `Get_All_Continuous_*` / `Update_Frame_Continuous_*`
- `VGPU_C7C8_Get_All_Continuous_Calibration_Image`
- `VGPU_GetContinuousCalibration`

### IPA 计算 — IPA

- `VGPU_Calculate_Ipa_Result`
- `VGPU_All_Aline_Mu_Data_To_Image`
- `VGPU_UpdateValueIPA`
