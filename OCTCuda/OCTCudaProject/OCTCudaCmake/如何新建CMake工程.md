# 如何新建 CMake 工程（OCTCudaCmake）

> 本文只讲 **你自己动手** 的步骤。不要让别人代建文件：按节创建目录、粘贴内容、再配置编译。  
> 对应任务：Week01 Day04 — 与 AIOCT 隔离的 `oct-cuda-pipeline` 骨架。  
> 工程根目录（本文件所在处）：

```text
E:\CUDA\Learning\CudaStudy\OCTCuda\OCTCudaProject\OCTCudaCmake
```

完成后应能：配置成功 → 编过一个空 `main` → 打印显存快照后退出。业务 kernel、真正 `cudaMalloc` 管线放到 Week02。

---

## 0. 和 VS「CUDA Runtime」工程的区别

| | 你已经做过的 `CudaRuntime1` | 今天要建的 CMake |
|--|---------------------------|------------------|
| 工程文件 | `.sln` + `.vcxproj` | 只有 `CMakeLists.txt` |
| 打开方式 | 双击 sln | VS / Cursor **打开文件夹** |
| CUDA | 勾选「生成自定义 → CUDA」 | `project(... LANGUAGES CXX CUDA)` |
| 换机器 | 容易路径写死 | `find_package(CUDAToolkit)` 跟 `CUDA_PATH` |

CMake 适合后面加 `tests/`、Nsight、独立 Git 仓。`CudaRuntime1` 可以留着练 VS；**正式骨架用本目录**。

---

## 1. 前置检查（先做，否则配置必失败）

在 **x64 Native Tools** 或普通 PowerShell 里执行：

```powershell
cmake --version
nvcc --version
echo $env:CUDA_PATH
```

需要同时满足：

1. **CMake ≥ 3.18**（没有则从 cmake.org 安装，勾选 Add to PATH）。  
2. **CUDA Toolkit** 已装，且 `nvcc` 能跑（你这边笔记里常见 **12.9**，以本机 `nvcc --version` 为准）。  
3. **Visual Studio 2022** 带「使用 C++ 的桌面开发」；CUDA 安装时勾过对应 VS 集成。  
4. 平台只用 **x64**（CUDA 不支持 Win32）。

Cursor / VS Code：安装扩展 **CMake Tools**（Microsoft）和 **C/C++**。

---

## 2. 手动建目录

在资源管理器中进入 `OCTCudaProject`，确认已有文件夹 `OCTCudaCmake`。在其下 **自己新建**（不要用 Git 子模块、不要拷 AIOCT）：

```text
OCTCudaCmake\
  CMakeLists.txt          ← 第 3 节粘贴
  README.md               ← 第 4 节粘贴
  include\
    oct\                  ← 空目录即可，头文件第 5 节再放
  src\
    host\
    kernels\              ← 本日保持空，Week02 再放 .cu
  tests\
  bench\
  docs\
```

PowerShell 也可（在 `OCTCudaCmake` 里执行）：

```powershell
mkdir include\oct, src\host, src\kernels, tests, bench, docs -Force
```

**不要**把 `Week01Day03\CudaRuntime1` 整个复制进来。后面只需按需复制 `cuda_utils.hpp`。

---

## 3. 手写 `CMakeLists.txt`

在 `OCTCudaCmake` 根目录新建文本文件，命名为 `CMakeLists.txt`（注意不是 `.txt.txt`），粘贴：

```cmake
cmake_minimum_required(VERSION 3.18)

project(oct_cuda_pipeline LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# 按本机显卡改；RTX 40 系常见 89。不确定可先注释掉，让 CMake/nvcc 默认
set(CMAKE_CUDA_ARCHITECTURES 89)

find_package(CUDAToolkit REQUIRED)

add_executable(oct_demo
    src/host/main.cpp
    src/host/context.cpp
)

target_include_directories(oct_demo PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src/host
)

target_link_libraries(oct_demo PRIVATE CUDA::cudart)

# 有 .cu 时再启用；本日没有 kernels 也可留着
set_target_properties(oct_demo PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
)
```

说明：

- `LANGUAGES CXX CUDA` 才会让以后的 `.cu` 走 nvcc。  
- `find_package(CUDAToolkit)` 依赖环境变量 `CUDA_PATH`。  
- Week03 做 FFT 时再加 `CUDA::cufft`。  
- `CMAKE_CUDA_ARCHITECTURES` 必须和显卡匹配，否则 kernel 能链上但跑不了（你 Week1 笔记里 4060 用过 `sm_89`）。

---

## 4. 手写 `README.md`（合规段，Day04 DoD）

根目录新建 `README.md`，可粘贴：

```markdown
# oct-cuda-pipeline

Independent reimplementation of a spectral-domain OCT GPU pipeline
(windowing, FFT/log, scan conversion, optional attenuation skeleton).
Not affiliated with any commercial IV-OCT product.

## Compliance

- No vendor DLLs, no reverse engineering, no patient or calibration dumps.
- Algorithms follow public literature and synthetic data only.
- Module names: oct::Context, ResampleWindow, FftLog, TransposeCrop,
  Dsc, EnhanceColor, PullbackBatch, Calib, Detect, StitchContCalib, Ipa.

## Layout

- include/oct — public headers
- src/host — C++ (no <<<>>>)
- src/kernels — CUDA .cu (from Week02)
- tests / bench / docs

## Build

cmake -S . -B build -A x64
cmake --build build --config Release
```

---

## 5. 手写三个源文件（空壳 Context）

本日只要能编过。把 Day03 的 `cuda_utils.hpp` **复制**到 `src/host/cuda_utils.hpp`（或 `include/oct/`），不要改公司代码。

### 5.1 `include/oct/shape.hpp`

```cpp
#pragma once

namespace oct {

struct Shape {
    int N  = 0;  // points_per_aline
    int Ls = 0;  // scan lines
    int Lp = 0;  // pullback lines
    int F  = 0;  // reserved pullback frames
    int H  = 0;  // circle height
    int W  = 0;  // circle width
};

}  // namespace oct
```

### 5.2 `include/oct/context.hpp`

```cpp
#pragma once

#include "oct/shape.hpp"
#include "cuda_utils.hpp"

namespace oct {

class Context {
public:
    bool init(const Shape& s);
    bool shutdown(bool free_calib = true);
    bool reinit();
    cuda_utils::VramSnapshot mem_info() const;
    bool ok() const;
    bool reset_device();
    const Shape& last_shape() const { return shape_; }
    bool allocated() const { return allocated_; }

private:
    Shape shape_{};
    bool allocated_ = false;
};

}  // namespace oct
```

若 `cuda_utils.hpp` 放在 `src/host/`，CMake 里已加 `src/host` 到 include；头文件写 `#include "cuda_utils.hpp"` 即可。若放到 `include/oct/`，改成 `#include "oct/cuda_utils.hpp"`。

### 5.3 `src/host/context.cpp`

空壳：只记 Shape，**先不要 cudaMalloc**。

```cpp
#include "oct/context.hpp"

namespace oct {

bool Context::init(const Shape& s)
{
    shape_ = s;
    allocated_ = true;
    return true;
}

bool Context::shutdown(bool /*free_calib*/)
{
    allocated_ = false;
    return true;
}

bool Context::reinit()
{
    if (!allocated_) return false;
    Shape s = shape_;
    shutdown(false);
    return init(s);
}

cuda_utils::VramSnapshot Context::mem_info() const
{
    return cuda_utils::vram_snapshot();
}

bool Context::ok() const
{
    return cuda_utils::check_cuda_ok();
}

bool Context::reset_device()
{
    allocated_ = false;
    return cuda_utils::reset_device();
}

}  // namespace oct
```

### 5.4 `src/host/main.cpp`

```cpp
#include "oct/context.hpp"
#include <cstdio>

int main()
{
    oct::Context ctx;
    oct::Shape s;
    s.N = 64;
    s.Ls = 8;
    s.Lp = 8;
    s.F = 2;
    s.H = 32;
    s.W = 32;

    if (!ctx.init(s)) {
        std::fprintf(stderr, "init failed\n");
        return 1;
    }

    auto v = ctx.mem_info();
    std::printf("VRAM total=%zu free=%zu used=%zu\n",
        v.total_bytes, v.free_bytes, v.used_bytes);

    ctx.shutdown();
    return ctx.ok() ? 0 : 1;
}
```

体积刻意取小，避免本日按 F=550 去占 GB 显存。

---

## 6. 配置与编译（三选一）

下面 **只做一种** 即可。生成目录一律用 `build/`，不要配到源码根上。

### 方式 A — Visual Studio 2022（推荐你现在的环境）

1. 打开 VS → **文件 → 打开 → 文件夹** → 选 `OCTCudaCmake`（选文件夹，不是 sln）。  
2. 若提示配置 CMake，选 **x64-Release** 或 **x64-Debug**。  
3. 菜单 **项目 → 配置 CMake** 成功后再 **生成 → 生成全部**。  
4. 启动项选 `oct_demo.exe`，F5 运行。  
5. VS 会在 `out/build/...` 或 `build/` 下生成工程，属正常。

若打开文件夹后没有 CMake 菜单：安装工作负载「C++ CMake 工具」。

### 方式 B — 命令行

在 `OCTCudaCmake` 目录：

```powershell
cmake -S . -B build -A x64
cmake --build build --config Release
.\build\Release\oct_demo.exe
```

第一次 `-S . -B build` 会跑编译器探测和 `find_package(CUDAToolkit)`。失败先看第 8 节。

Debug：

```powershell
cmake --build build --config Debug
.\build\Debug\oct_demo.exe
```

### 方式 C — Cursor / VS Code

1. 用 Cursor **打开文件夹** `OCTCudaCmake`。  
2. 命令面板：`CMake: Select a Kit` → 选 **Visual Studio 2022 Release - amd64**（不要 Ninja+MSVC 混到没 CUDA 的 kit）。  
3. `CMake: Configure` → `CMake: Build` → `CMake: Run Without Debugging`。  
4. 出现 kit 选不到 CUDA 时，在 `.vscode/settings.json`（你自己建）里可指定：

```json
{
  "cmake.configureArgs": ["-A", "x64"]
}
```

---

## 7. 验收（Day04 DoD）

- [ ] `cmake` 配置无错误，能看到 `Found CUDAToolkit`  
- [ ] 生成 `oct_demo`，运行打印一行 `VRAM total=...`  
- [ ] `README.md` 有 Compliance 和十一模块名  
- [ ] 目录里有 `include/oct`、`src/host`、`src/kernels`（可空）、`tests`、`bench`、`docs`  
- [ ] **没有**链接 `VGPU_Process.lib` / 公司 DLL

---

## 8. 常见失败

| 现象 | 处理 |
|------|------|
| `cmake 不是内部或外部命令` | 安装 CMake 并勾选 PATH，新开终端 |
| `No CUDA toolset found` / 找不到 nvcc | 重装 Toolkit，勾选当前 VS 版本；确认 `CUDA_PATH` |
| `CMAKE_CUDA_COMPILER not found` | 项目必须 `LANGUAGES CUDA`；用 VS amd64 kit，不要纯 MinGW |
| 配置成 Win32 | 必须 `-A x64` 或 kit 选 amd64 |
| `cuda_utils.hpp: No such file` | 确认已复制到 `src/host` 或 `include/oct`，且 `target_include_directories` 包含该路径 |
| 中文路径乱码 | 本工程路径目前是英文，保持即可 |
| 能编译、一跑 kernel 就 invalid device | `CMAKE_CUDA_ARCHITECTURES` 与 GPU 不符；空壳 main 若只调 `cudaMemGetInfo` 一般仍能跑 |
| VS 打开了 `.sln` 而不是文件夹 | CMake 工程不要用 CUDA Runtime 向导再建一个 sln 混在一起 |

---

## 9. 做完之后

- 把配置命令、本机 `nvcc --version`、显卡型号记进 `Week01/Day04/Note.md` 或本目录 `docs/`。  
- **不要**把 `build/`、`out/` 提交 Git（可自己加 `.gitignore`：`build/`、`out/`、`.vs/`）。  
- Day05：`DOCMotionType`、`is_device_to_host`、写 `Week01/REVIEW.md`。  
- Week02：在 `src/kernels/` 加第一个 `.cu`，并在 `CMakeLists.txt` 的 `add_executable` 里追加该文件。

---

## 10. 不要做的事

- 不要在本目录拷 `VGPU_Process.dll`、患者数据、标定表。  
- 不要把 `OCTCuda/vgpu/include/cuda/` 整树官方头再拷一份（用 Toolkit 的 include）。  
- 不要今天就实现 Resample/FFT/DSC。  
- 不要用「新建 CUDA Runtime 项目」代替 CMake（那是另一条线，已经有 `CudaRuntime1`）。
