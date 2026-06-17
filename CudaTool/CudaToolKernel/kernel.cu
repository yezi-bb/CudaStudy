#include "CudaTool.h"
// 全局设备核函数
__global__ void AddKernel(float* a, float* b, float* out, int size)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size)
        out[idx] = a[idx] + b[idx];
}

// CUDA侧封装调用接口
void LaunchAddKernelImpl(float* devA, float* devB, float* devOut, int size)
{
    dim3 blockSize(256);
    dim3 gridSize((size + blockSize.x - 1) / blockSize.x);
    // 紧贴无空格标准写法
    AddKernel << <gridSize, blockSize >> > (devA, devB, devOut, size);
}