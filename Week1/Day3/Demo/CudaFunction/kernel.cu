/*****************************************************************//**
 * @file   kernel.cu
 * @brief  练习相关的CUDA函数功能和逻辑
 *
 * @author Administrator
 * @date   June 2026
 *********************************************************************/
#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include <iostream>

const int N = 256 - 2;
/**
 * Description:
 *		内部函数 只允许在device内调用
 *
 * @param x
 * @return
 */
__device__ float Square(float x)
{
	return x * x;
}

/**
 * Description:
 *		device kernel function，允许Host调用
 *
 * @return
 */
__global__ void SquareKernel(float* d_in)
{
	int i = blockIdx.x * blockDim.x + threadIdx.x;
	if (i > N) return;
	d_in[i] = Square(d_in[i]);
}

__host__ void	PrintValues(float* h_in, int n)
{
	for (int i = 0; i < n; i++)
	{
		if (i % 16 == 0 && i) std::cout << std::endl;
		std::cout << h_in[i] << " ";
	}
}

int main(int argc, char** argv)
{
	// 主机内存申请 计算资源
	float* h_in = (float*)malloc(sizeof(float) * N);
	for (int i = 0; i < N; i++)
	{
		h_in[i] = i;
	}
	// 设备内存申请
	float* d_in = NULL;
	cudaMalloc(&d_in, sizeof(float) * N);
	// 设备内存初始化
	cudaMemcpy(d_in, h_in, sizeof(float) * N, cudaMemcpyHostToDevice);

	// 运行kernel
	//SquareKernel<< <1, 256> >>(d_in);
	SquareKernel<<<1, N>>>(d_in);
	cudaDeviceSynchronize();

	// 设备内存拷贝
    cudaMemcpy(h_in, d_in, sizeof(float) * N, cudaMemcpyDeviceToHost);
    PrintValues(h_in, N);

	//释放设备内存
	cudaFree(d_in);
	// 主机内存释放
	free(h_in);


	return 0;
}
