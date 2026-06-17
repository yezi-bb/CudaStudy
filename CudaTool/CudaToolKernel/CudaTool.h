#pragma once

// 导出宏：本库编译时定义 CUDA_TOOL_EXPORTS，标记为 dllexport；外部使用自动变成 dllimport
#ifdef CUDA_TOOL_EXPORTS
#define CUDA_TOOL_API __declspec(dllexport)
#else
#define CUDA_TOOL_API __declspec(dllimport)
#endif

// CUDA 基础头文件
#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include "stdlib.h"
#include "stdio.h"

class CUDA_TOOL_API CudaTool
{
public:
    // 简单GPU内存拷贝封装
    static void CopyHostToDevice(float* hostData, float* devData, size_t elemCount);
    // 简单核函数调用封装 Add算法
    static void LaunchAddKernel(float* devA, float* devB, float* devOut, int size);
    // 设备资源释放
    static void SafeFreeDevice(float* devPtr);
};

// 全局CUDA错误检查工具函数
CUDA_TOOL_API void CheckCudaStatus(cudaError_t status, const char* msg);