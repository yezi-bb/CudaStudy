#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include <iostream>

__global__ void addKernel(float* d_in)
{
	int idx = blockIdx.x * blockDim.x + threadIdx.x;
	d_in[idx] += 1.0f;
}
int main()
{
	const int N = 256;
	size_t size = N * sizeof(float);
	// 主机内存分配
    float* h_in = (float*)malloc(size);
	if (h_in == nullptr)
    {
        std::cout << "malloc failed" << std::endl;
        return -1;
    }
	for (int i = 0; i < N; i++)
	{
		h_in[i] = i;
	}
	// 设备内存分配
	float *d_in = nullptr;
	cudaMalloc(&d_in, size);

	// 数据拷贝  主机内存 ->设备显存
	cudaMemcpy(d_in, h_in, size, cudaMemcpyHostToDevice);

	// 核函数调用
	addKernel<<<1, N>>>(d_in);
	cudaDeviceSynchronize();

	// 数据拷贝  设备显存 -> 主机内存
	cudaMemcpy(h_in, d_in, size, cudaMemcpyDeviceToHost);

	// 输出结果
	for (int i = 0; i < N; i++)
	{
		if (i % 20 == 0 && i) std::cout << std::endl;
		std::cout << h_in[i] << " ";
	}
	// 设备内存释放
	cudaFree(d_in);
	// 主机内存释放
    free(h_in);

	return 0;
}
