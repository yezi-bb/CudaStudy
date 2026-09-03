# =====================================================================
# oct_cuda_pipeline — 学习用 OCT GPU 管线（与 AIOCT 物理隔离）
# 约定：目录 = 代码身份；显式源文件列表（不用 file(GLOB)）
#   include/oct   公共头（只被别的目标从这里 include）
#   src/host      .cpp 宿主逻辑（不允许 <<<>>>）
#   src/kernels   .cu  （Week02 Day03 起逐个加入 oct_core 源列表）
#   tests/        每个模块一个 test_<module>.cpp（CTest，0 依赖）
#   bench/        kernel 计时 / 显存快照（产出可贴笔记的一行）
#   docs/         决策记录
# =====================================================================
cmake_minimum_required(VERSION 3.18)

# 项目名用下划线：连字符会让 ${oct-cuda_pipline_BINARY_DIR} 被误解析成减法
project(oct_cuda_pipeline LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# GPU 算力：按本机显卡改；RTX 40 系（Ada）=89。不确定先注释掉让 nvcc 默认
set(CMAKE_CUDA_ARCHITECTURES 89)

find_package(CUDAToolkit REQUIRED)

# =====================================================================
# MSVC 源码编码：本工程源码为 UTF-8（含中文注释）。
#   不设 /utf-8 时 cl 按系统 GBK(936) 读文件，中文注释的某些字节
#   （双字节尾字节 == 0x5C）会被当成行连接符，把下一行整行"吞掉"，
#   表现为 C4819 警告 + 函数声明/变量声明报"未声明/意外的 size_t"等诡异语法错误。
# =====================================================================
if(MSVC)
    add_compile_options($<$<COMPILE_LANGUAGE:CXX>:/utf-8>)
    # 以后加入 .cu 时 nvcc 需把 /utf-8 透传给宿主编译器 cl（nvcc 本身不认该开关）
    add_compile_options($<$<COMPILE_LANGUAGE:CUDA>:-Xcompiler=/utf-8>)
endif()

# =====================================================================
# oct_core —— 模块实现静态库。
#   host 代码现在就在这；Week02D3 起把每个 kernel 的 .cu 追加到下面源列表，
#   后续 oct_demo / 各 test / bench 统一链它，避免到处重复列源文件。
# =====================================================================
add_library(oct_core STATIC
    src/host/context.cpp
    src/host/resample_window.cpp          # Week02 Day02：CPU golden（Resample+Window）
    # Week02 Day03+：src/kernels/resample_kernel.cu
    # Week03：       src/kernels/fft_log_kernel.cu   （同时 target_link CUDA::cufft）
    # Week04：       src/kernels/transpose_kernel.cu / dsc_kernel.cu
)

# include/oct 是公开接口；src/host 因 context.hpp include "cuda_utils.hpp" 也公开暴露
target_include_directories(oct_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src/host
)

# CUDA 运行时只链接这一处；下游目标通过链 oct_core 间接获得
target_link_libraries(oct_core PUBLIC CUDA::cudart)

# 跨 .cu 互相调用 __global__/__device__ 符号时需要；host-only 阶段开着无害
set_target_properties(oct_core PROPERTIES CUDA_SEPARABLE_COMPILATION ON)

# =====================================================================
# oct_demo —— 演示/入口程序（Week01 Day04 的显存快照 main）
# =====================================================================
add_executable(oct_demo
    src/host/main.cpp
)

target_include_directories(oct_demo PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/OCTImages   # 读取测试图的目录（后续可视化用）
)

target_link_libraries(oct_demo PRIVATE oct_core)

# =====================================================================
# 单元测试 —— CTest，0 依赖（assert/fprintf + 返回码）
#   命令行跑法：ctest --test-dir build -C Release --output-on-failure
#   新增测试：add_executable(oct_test_<模块> tests/test_<模块>.cpp)
#             add_test(NAME <模块> COMMAND oct_test_<模块>)
# =====================================================================
enable_testing()

add_executable(oct_test_resample
    tests/test_resample_window.cpp         # Week02 Day02 黄金版锁定测试
)

target_link_libraries(oct_test_resample PRIVATE oct_core)

add_test(NAME resample_window COMMAND oct_test_resample)

# =====================================================================
# 拷贝 cudart DLL 到每个 exe 目录（仅 Windows；必须放在 add_* 之后）
# =====================================================================
if(WIN32)
  file(GLOB CUDART_DLL "${CUDAToolkit_BIN_DIR}/cudart64_*.dll")
  if(CUDART_DLL)   # 防止 glob 没匹配到 dll 时命令变成空参报错
    foreach(tgt oct_demo oct_test_resample)
      add_custom_command(TARGET ${tgt} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
          ${CUDART_DLL} $<TARGET_FILE_DIR:${tgt}>
        COMMENT "Copying CUDA runtime DLL -> ${tgt}"
      )
    endforeach()
  endif()
endif()
