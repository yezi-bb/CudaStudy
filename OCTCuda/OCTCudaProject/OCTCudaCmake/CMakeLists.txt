# 最低 CMake 版本
cmake_minimum_required(VERSION 3.18)

# 项目名建议用下划线：连字符会让 ${oct-cuda_pipline_BINARY_DIR} 这类自动变量被误解析成减法
project(oct_cuda_pipeline LANGUAGES CXX CUDA)

# C++17（强制，不能降级）
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# GPU 算力：RTX 40 系（Ada）8.9 ✔
set(CMAKE_CUDA_ARCHITECTURES 89)

# 查找 CUDA 工具包
find_package(CUDAToolkit REQUIRED)

# ⭐ 先创建目标 —— 所有 target_* 命令都必须排在它后面
add_executable(oct_demo
    src/host/main.cpp
    src/host/context.cpp
    # src/cuda/kernels.cu   ← 有 .cu 文件就加进来（见文末提醒）
)

# 头文件搜索路径
target_include_directories(oct_demo PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src/host
)

# 链接 CUDA 运行时（只保留这一处）
target_link_libraries(oct_demo PRIVATE CUDA::cudart)

# 可分离编译：多个 .cu 跨文件调用 __global__ 核函数时需要
set_target_properties(oct_demo PROPERTIES CUDA_SEPARABLE_COMPILATION ON)

# 拷贝 cudart dll —— 必须在 add_executable 之后
if(WIN32)
  file(GLOB CUDART_DLL "${CUDAToolkit_BIN_DIR}/cudart64_*.dll")
  if(CUDART_DLL)   # 防止 glob 没匹配到 dll 时命令变成空参报错
    add_custom_command(TARGET oct_demo POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${CUDART_DLL} $<TARGET_FILE_DIR:oct_demo>
      COMMENT "Copying CUDA runtime DLL"
    )
  endif()
endif()
