# Week 01 / Day 04 — 学习记录

> 任务：创建与 AIOCT **物理隔离**的 `oct-cuda-pipeline` 骨架，模块名对齐 `01_API接口全解.md` §8。  
> 必读：`00_全局规划.md` §6 实现优先级、§7 合规；`README.md` 建议目录。  
> 本日只要求：**CMake/VS 能编过空 main、README 有合规段、目录与 §8 模块名对上**。不写业务 kernel。

`README.md` 写「Day05 起创建仓库」，与本 TASK 冲突时 **以 Day04 TASK 为准**：今天搭骨架，明天吃 `DOCMotionType` / `is_device_to_host` 并写 REVIEW。

## 1. 核心结论

公司仓只能 **只读对照** API + 宿主调用。开源仓必须：

- 不链 `VGPU_Process.dll`、不拷业务 `.cu`（本来也没有）
- 不出现患者数据、标定真值、内部阈值表
- 用 **自己的模块名** 复现「等价功能」，合成数据验证

Day02 的 `PipelineContext`、Day03 的 `cuda_utils.hpp` 今天要变成仓里的 **`oct::Context` 空壳**：`init` / `shutdown` / `mem_info`。缓冲可以先不 `cudaMalloc`，但接口形状要定死，Week02 往里填。

现有练习工程：

```text
OCTCuda/OCTCudaProject/Week01Day03/CudaRuntime1/
  cuda_utils.hpp    ← Day03 桩，应对齐进 oct::Context
```

正式骨架建议另开目录（不要和 AIOCT / 本笔记树搅在一起），例如：

```text
CudaStudy/OCTCuda/OCTCudaProject/oct-cuda-pipeline/   # 或完全独立的 Git 仓
```

VS CUDA Runtime 模板能编过也算 DoD「可编译」；计划原文偏 CMake，长期跟 Week02+ 单测/Nsight 更省事。两种可以并存：VS 练手，CMake 当开源仓。

## 2. 为何必须隔离（合规，README 必写）

摘自 `00` §7，开源 README 用通用术语，**不要**把公司路径写进公开仓：

| 禁止 | 允许 |
|------|------|
| 反汇编 / 开源 `VGPU_Process.dll` | 按 API **语义** 自写 kernel |
| 医院数据、原始 pullback、内部阈值表 | 合成 chirp / 公开文献算法 |
| 公开 README 堆内部函数名（可不写） | `oct::Dsc`、spectral reconstruction、scan conversion |

口述：简历写「独立开源复现光谱域重建」，不写「调用了公司 VGPU_Process」。

## 3. 目录骨架（对齐 README + TASK）

```text
oct-cuda-pipeline/
  CMakeLists.txt              # enable_language(CUDA)；找 CUDAToolkit
  README.md                   # 合规段 + §8 模块列表
  include/oct/
    context.hpp               # oct::Context 空壳
    shape.hpp                 # N, Ls, Lp, F, H, W
  src/host/
    context.cpp               # init / shutdown / mem_info
    main.cpp                  # 空 main：init → mem_info → shutdown
  src/kernels/                # Week02 起放 .cu；本日可空
  tests/                      # Week02 CPU 黄金版单测
  bench/                      # Nsight / 计时
  docs/                       # 公开算法说明，不写公司路径
```

对应关系：

| 目录 | 职责 |
|------|------|
| `include/oct/` | 对外 API，MSVC 工程只需 include |
| `src/host/` | 无 `<<<>>>`，MSVC 可编 |
| `src/kernels/` | 仅 nvcc；`Launch*Impl` |
| `tests/` | 合成数据，对 CPU 黄金版比误差 |
| `bench/` | 作品集数字 |

## 4. §8 模块映射（DoD：名字必须一致）

开源模块名 **不要**改成 `VGPU_*`。后续每周往对应目录加文件。

| 开源模块 | 覆盖的 VGPU 语义 | 哪周填肉 |
|----------|------------------|----------|
| `oct::Context` | Allocate / Free / Realloc / Memory / Status | **W01 空壳**；malloc 可 W02 起 |
| `oct::ResampleWindow` | `Data_Resampling_*` | W02 |
| `oct::FftLog` | `Get_FFT_Power_*` / Log / U16↔F32 | W03 |
| `oct::TransposeCrop` | `Transpose*` | W04 |
| `oct::Dsc` | `DSC`（作品集核心） | W04 |
| `oct::EnhanceColor` | Enhancement / Gray2Color | W05 |
| `oct::PullbackBatch` | `Set_Original` / `Handle_All_*` | W06 |
| `oct::Calib` | `Catheter_AutoCalibration*` | W07 |
| `oct::Detect` | Contrast / Break / guiding | W08 |
| `oct::StitchContCalib` | Stitching / Continuous* | W09 |
| `oct::Ipa` | Calculate_Ipa / Mu_To_Image / UpdateValueIPA | W10–W12 |

`00` §6 优先级（开源仓填肉顺序，不是今天全做）：

- **P0：** Context 语义、窗、FFT/Log、Transpose、DSC、增强伪彩、Scan e2e、Pullback 骨架、IPA μ 骨架、UpdateIPA 理解、Streams  
- **P1：** Texture DSC、U16 压缩、连续校准简化、导管检测简化  
- **P2：** VTK/CUDA-GL、TensorRT、多 GPU  

本日只验收 **Context 空壳 + 目录上能看出上表其它模块的位置**（可用空 `hpp` 或 README 列表占位）。

## 5. `oct::Context` ↔ Allocate / Free / Memory

Day02 形状符号：`N, Ls, Lp, F, H, W`。空壳只保存 Shape、调 Day03 工具，**可以暂不 malloc**。

```text
oct::Context::init(Shape)          ↔ VGPU_Allocate_Parameter_Manager
oct::Context::shutdown(free_calib) ↔ VGPU_Free_Parament_Manager
oct::Context::reinit()             ↔ VGPU_Reallocate_memory   （内部 shutdown(false)+init(last)）
oct::Context::mem_info()           ↔ VGPU_GetCurrentGPUMemory （cuda_utils::vram_snapshot）
oct::Context::ok()                 ↔ VGPU_GetCudaErrorStatus  （cuda_utils::check_cuda_ok）
oct::Context::reset_device()       ↔ VGPU_ResetCudaMemory     （之后必须再 init）
```

接口草稿（本日实现可全是空操作 + 打日志）：

```cpp
namespace oct {

struct Shape {
    int N  = 0;   // points_per_aline
    int Ls = 0;   // scan_lines_number
    int Lp = 0;   // pullback_lines_number
    int F  = 0;   // pullback_total_fram_numer
    int H = 0, W = 0;  // 圆图
};

class Context {
public:
    bool init(const Shape& s);                 // 记住 s；日后 cudaMalloc
    bool shutdown(bool free_calib = true);     // 成对释放
    bool reinit();                             // 同尺寸重建；上下文须仍健康
    cuda_utils::VramSnapshot mem_info() const;
    bool ok() const;
    bool reset_device();                       // 慎用；之后 init
    const Shape& last_shape() const { return shape_; }
    bool allocated() const { return allocated_; }
private:
    Shape shape_{};
    bool allocated_ = false;
};

}  // namespace oct
```

`init` 失败 ⇒ `allocated_==false`，宿主不得进入 Resample/FFT（Day02 结论）。  
`reset_device` 后必须清 `allocated_`，旧指针当悬空。

把现有 `cuda_utils.hpp` 拷进 `include/oct/` 或 `src/host/`，`Context::mem_info/ok/reset_device` 直接转发，避免第三套封装。

## 6. CMake 要点（TASK 参考：官方 CUDA 示例）

```cmake
cmake_minimum_required(VERSION 3.18)
project(oct-cuda-pipeline LANGUAGES CXX CUDA)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CUDA_STANDARD 17)
find_package(CUDAToolkit REQUIRED)

add_executable(oct_demo
    src/host/main.cpp
    src/host/context.cpp)
target_include_directories(oct_demo PRIVATE include)
target_link_libraries(oct_demo PRIVATE CUDA::cudart)
# Week03 再链 CUDA::cufft
```

- `LANGUAGES CUDA` 后 `.cu` 走 nvcc；本日可以没有 `.cu`。  
- 算力日后与显卡对齐（本机练习仓曾用 `compute_89,sm_89`）。  
- 空 `main`：`Context c; c.init({2048,500,500,8,64,64}); auto v = c.mem_info(); c.shutdown();` 能跑通即 DoD。

VS 路线：沿用 `CudaRuntime1`，加 `context.hpp/.cpp`，链接只要 `cudart`（与 Day01：宿主不编业务 kernel 时仍可能链 cudart）。

## 7. README 合规段（可直接贴进开源仓）

```markdown
# oct-cuda-pipeline

Independent reimplementation of a spectral-domain OCT GPU pipeline
(windowing, FFT/log, scan conversion, optional attenuation-coefficient skeleton).
Not affiliated with any commercial IV-OCT product.

## Compliance
- No vendor DLLs, no reverse engineering, no patient or calibration dumps.
- Algorithms follow public literature + synthetic data only.
- Module names are oct::Context / ResampleWindow / FftLog / Dsc / ...
  (functional equivalents, not a copy of any closed API).

## Layout
include/oct  src/host  src/kernels  tests  bench  docs
```

公开 README 用英文模块名即可；公司路径只留在本 `OCTCuda/Week*` 笔记里。

## 8. 空 main 最小行为

```text
main
  → Context::init(小 Shape，避免本日就按 F=550 去估 GB)
  → mem_info() 打印 total/free/used
  → ok() 为 true 再 shutdown
  → return 0
```

本日 **不要** 为了「像产品」去 malloc 回拉 bulk。Context 先当状态机：`Idle → Allocated → Freed`。

## 9. 与前三天、明天的衔接

```text
Day01  DLL 边界、官方 cudart vs 业务库
Day02  Allocate 尺寸 → 假想缓冲；Context 语义
Day03  Status / Memory / Reset vs Reallocate；cuda_utils.hpp
Day04  独立仓骨架 + oct::Context 空壳     ← 本笔记
Day05  DOCMotionType、is_device_to_host、W01 REVIEW
Week02 第一颗业务代码：CPU Hann + CUDA 乘窗，放进 ResampleWindow
```

## 10. 口述 / DoD 自检

- [ ] 说得出：为何不能在 AIOCT 里直接加开源 kernel（合规 + nvcc 不进宿主）  
- [ ] 能背 §8 十一模块名，并指出 Context 覆盖 Allocate/Free/Memory/Status  
- [ ] README 有合规段；目录或列表能对上 §8  
- [ ] `init → mem_info → shutdown` 能编过（CMake 或现有 VS 工程）

动手落地时：新建 `oct-cuda-pipeline`，把 `CudaRuntime1/cuda_utils.hpp` 挪进去，不要在笔记目录里堆 `.cu`。
