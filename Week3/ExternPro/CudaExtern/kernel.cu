#include "CudaTool.h"
#include "device_launch_parameters.h"

template <typename T>
__global__ void BinaryKernel(T* d_in, T* d_out, size_t width, size_t height, T threshold)
{
    size_t x = blockIdx.x * blockDim.x + threadIdx.x;
    size_t y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x < width && y < height)
    {
        size_t idx = y * width + x;
        d_out[idx] = d_in[idx] > threshold ? T(255) : T(0);
    }
}

template <typename T>
void LaunchBinaryKernelImpl(T* d_in, T* d_out, size_t width, size_t height, T threshold)
{
    dim3 block(16, 16);
    dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
    BinaryKernel << <grid, block >> > (d_in, d_out, width, height, threshold);
}

// ==========显式模板实例化==========
template DLL_EXPORT void LaunchBinaryKernelImpl<unsigned char>(
    unsigned char* d_in, unsigned char* d_out, size_t width, size_t height, unsigned char threshold);