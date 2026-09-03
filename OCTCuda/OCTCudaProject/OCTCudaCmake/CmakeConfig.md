# CmakeConfig — OCTCudaCmake 结构说明

> 本文解释 `CMakeLists.txt` 为什么这样分块、每段做什么，以及以后加模块/测试怎么改。
> 与 `如何新建CMake工程.md` 互补：那篇讲"怎么建一个工程"，这篇讲"当前这个工程怎么组织的"。

## 0. 一句话总览

```
oct_core (STATIC 静态库)          ← 所有业务代码（host + 未来的 kernel）都进这里
   ├─ oct_demo          (演示入口，只留 main.cpp)
   └─ oct_test_resample (单元测试入口，只留断言)
```

核心思想：**代码进库，入口只留壳**。后续每加一个模块（FFT/DSC/…），只往 `oct_core` 源列表追加文件，demo 和所有测试自动获得新能力，不用每个 target 重复列源文件。

## 1. 文件头部与工程声明（L1–24）

```cmake
cmake_minimum_required(VERSION 3.18)
project(oct_cuda_pipeline LANGUAGES CXX CUDA)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CUDA_ARCHITECTURES 89)
find_package(CUDAToolkit REQUIRED)
```

| 行 | 作用 |
|---|---|
| L11 | 最低 CMake 版本 3.18 |
| L14 | `LANGUAGES CXX CUDA`：声明工程用两种编译器——MSVC 编 `.cpp`，**nvcc 编 `.cu`**。没有 `CUDA` 语言声明，以后的 kernel 文件不会被编译。项目名用下划线：连字符会让 `${oct-cuda..._BINARY_DIR}` 被误解析成减法 |
| L16–19 | C++ 与 CUDA 都锁 C++17 |
| L22 | GPU 算力锁 `sm_89`（RTX 40 系 / Ada）。与显卡不匹配会"编得过、跑不了"；不确定时可先注释掉让 nvcc 按本机默认 |
| L24 | 找 CUDA Toolkit（NVCC + cudart）。找不到会在这里直接报错，属于"配置期失败"，比编译期再炸好 |

## 2. `oct_core` 静态库（L26–49）——结构的核心

```cmake
add_library(oct_core STATIC
    src/host/context.cpp
    src/host/resample_window.cpp          # Week02 Day02：CPU golden（Resample+Window）
    # Week02 Day03+：src/kernels/resample_kernel.cu
)
target_include_directories(oct_core PUBLIC include/ src/host)
target_link_libraries(oct_core PUBLIC CUDA::cudart)
set_target_properties(oct_core PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
```

- **`STATIC`**：编成 `.lib` 而非 exe，本身不能独立跑，供其他 target 链接。
- **源文件显式列出，不用 `file(GLOB)`**：新增 `.cu` 必须手动在 `add_library` 加一行。GLOB 的坑是新增文件不会自动进配置，表现为"我加了文件但没编进去"。
- **`PUBLIC include/`**：接口**向外传递**——任何链了 `oct_core` 的目标自动获得 `include/` 和 `src/host/` 的搜索路径。`src/host` 之所以也公开，是因为 `context.hpp` 要 `#include "cuda_utils.hpp"`。各 exe 因此不用再自己配 include。
- **`PUBLIC CUDA::cudart`**：CUDA 运行时只在这一处链接，下游 exe 只需写 `target_link_libraries(x PRIVATE oct_core)`。
- **`CUDA_SEPARABLE_COMPILATION ON`**：为将来跨 `.cu` 互调 `__global__/__device__` 符号预留；当前 host-only 阶段无害，只是编译略慢。

> 以后加模块只改这一处：`# Week03：src/kernels/fft_log_kernel.cu`（同时给 oct_core 补 `target_link_libraries(... CUDA::cufft)`），`# Week04：src/kernels/transpose_kernel.cu / dsc_kernel.cu`。

## 3. `oct_demo` 演示入口（L51–62）

```cmake
add_executable(oct_demo src/host/main.cpp)
target_include_directories(oct_demo PRIVATE OCTImages)
target_link_libraries(oct_demo PRIVATE oct_core)
```

- `main.cpp` 里不再直接出现 `context.cpp` 的实现——都从 `oct_core` 来，demo 只剩入口逻辑。
- **`PRIVATE OCTImages`**：读测试图的目录只给 demo 自己用，不污染库的公共接口。**能 PRIVATE 就不 PUBLIC**，是防止头文件路径蔓延的关键纪律。

## 4. CTest 单元测试（L64–78）

```cmake
enable_testing()
add_executable(oct_test_resample tests/test_resample_window.cpp)
target_link_libraries(oct_test_resample PRIVATE oct_core)
add_test(NAME resample_window COMMAND oct_test_resample)
```

- 测试也链 `oct_core`，直接调 `oct::resample_window_frame`，测试源码只有断言逻辑——**测试只测行为，不含实现**。
- `enable_testing()` + `add_test()` 注册进 CTest，之后一条 `ctest` 命令可跑全部注册测试。
- 断言用 `assert`/`fprintf` + 返回码，0 依赖（不引 GoogleTest）；将来展示测试工程化时再换框架。
- **新增测试模板**（照抄即可）：

```cmake
add_executable(oct_test_<模块> tests/test_<模块>.cpp)
target_link_libraries(oct_test_<模块> PRIVATE oct_core)
add_test(NAME <模块> COMMAND oct_test_<模块>)
```

## 5. cudart DLL 拷贝（L80–94）

```cmake
if(WIN32)
  file(GLOB CUDART_DLL "${CUDAToolkit_BIN_DIR}/cudart64_*.dll")
  if(CUDART_DLL)
    foreach(tgt oct_demo oct_test_resample)
      add_custom_command(TARGET ${tgt} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CUDART_DLL} $<TARGET_FILE_DIR:${tgt}> ...)
    endforeach()
  endif()
endif()
```

- Windows 下 exe 运行时需要同目录的 `cudart64_*.dll`，每次构建后自动拷到各 exe 目录。
- `copy_if_different`：只拷贝有变化的文件，避免每次都触发重链接。
- `foreach` 遍历目标而不是复制粘贴两遍——**同一逻辑只写一次**，以后加 exe 只需在列表里补名字。
- `if(CUDART_DLL)` 空参保护：glob 没匹配到 dll 时 `copy` 参数为空会报错。
- 注意：这里的 `file(GLOB)` 只用于**定位系统里的 DLL**，不是收集工程源文件，与"源文件显式列出"的纪律不冲突。

## 6. 与原单 exe 版的差别

| | 单 exe 版（Week02 前） | 库 + 测试版（现在） |
|---|---|---|
| 加一个模块 | demo 的源列表越滚越长 | 只动 `oct_core` 一处 |
| 加测试 | 测试代码混进 main | 独立 `oct_test_*`，CTest 统一跑 |
| include/链接 | 每个 exe 自己配一遍 | 链 `oct_core` 自动继承 |
| 加 `.cu` | 要决定放哪个 exe | 直接追加进 `oct_core`，全目标生效 |

## 7. 常用命令速查（在工程根目录）

```powershell
# 配置（首次需 VS2022 + CUDA Toolkit；产物全部进 build/，源码目录保持干净）
cmake -S . -B build -A x64

# 编译
cmake --build build --config Release --target oct_demo oct_test_resample

# 跑全部注册测试
ctest --test-dir build -C Release --output-on-failure

# 直接跑测试 exe（看 PASS 与数值摘要行）
.\build\Release\oct_test_resample.exe
```

## 8. 目录与文件身份对照

| 目录 | 放什么 | 不得放 |
|---|---|---|
| `include/oct/` | 模块公共头（`resample_window.hpp`） | 实现 |
| `src/host/` | `.cpp` 宿主逻辑（CPU golden、Controller 模拟） | `<<<>>>` CUDA 语法 |
| `src/kernels/` | `.cu`（Day03 起逐个加入 `oct_core`） | host 逻辑 |
| `tests/` | 每模块一个 `test_<模块>.cpp` | 平台相关代码 |
| `bench/` | kernel 计时/显存快照 main，产出可贴笔记的一行 | 业务逻辑 |
| `docs/` | 决策记录（为什么 N=2048、Layout 约定） | 操作步骤 |

文件按类名 snake_case 命名（`ResampleWindow` → `resample_window.hpp/.cpp`），与 `01_API接口全解.md §8`、`README.md` 的模块表保持一致，找文件零成本。
