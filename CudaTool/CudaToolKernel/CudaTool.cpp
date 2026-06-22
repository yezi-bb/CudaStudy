#include "CudaTool.h"

void CudaTool::CopyHostToDevice(float* hostData, float* devData, size_t elemCount)
{
    CheckCudaStatus(
        cudaMemcpy(devData, hostData, elemCount * sizeof(float), cudaMemcpyHostToDevice),
        "Host -> Device memcpy failed"
    );
}

void CudaTool::SafeFreeDevice(float* devPtr)
{
    if (devPtr)
    {
        CheckCudaStatus(cudaFree(devPtr), "cudaFree failed");
    }
}

// 外部声明cu里实现的函数
extern void LaunchAddKernelImpl(float* devA, float* devB, float* devOut, int size);

void CudaTool::LaunchAddKernel(float* devA, float* devB, float* devOut, int size)
{
    LaunchAddKernelImpl(devA, devB, devOut, size);
    CheckCudaStatus(cudaGetLastError(), "Kernel launch error");
    CheckCudaStatus(cudaDeviceSynchronize(), "Device sync failed");
}

void CheckCudaStatus(cudaError_t status, const char* msg)
{
    if (status != cudaSuccess)
    {
        printf("CUDA Error: %s, %s\n", msg, cudaGetErrorString(status));
        abort();
    }
}