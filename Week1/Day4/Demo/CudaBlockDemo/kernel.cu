#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include <iostream>

const int N = 1 << 10;

__global__ void AddKernel(float* d_a, float* d_b, float* d_c)
{
	int idx = blockIdx.x * blockDim.x + threadIdx.x;
	if (idx >= N) return;
	d_c[idx] = d_a[idx] + d_b[idx];
}


__host__ void Print(float* a, int n)
{
	for (int i = 0; i < n; i++)
	{
		if (i % 20 == 0 && i) std::cout << std::endl;
		std::cout << a[i] << " ";
	}
}

int main(int argc, char** argv)
{
	float* h_a = new float[N];
	for (int i = 0; i < N; i++)
	{
		h_a[i] = i;
	}
	float* h_b = new float[N];
	for (int i = 0; i < N; i++)
	{
		h_b[i] = i;
	}
	float* h_c = new float[N];

	// Allocate device memory
	float* d_a = nullptr;
	float* d_b = nullptr;
	float* d_c = nullptr;
	cudaMalloc(&d_a, N * sizeof(float));
	cudaMalloc(&d_b, N * sizeof(float));
	cudaMalloc(&d_c, N * sizeof(float));

	// Copy host memory to device
	cudaMemcpy(d_a, h_a, N * sizeof(float), cudaMemcpyHostToDevice);
	cudaMemcpy(d_b, h_b, N * sizeof(float), cudaMemcpyHostToDevice);
	cudaMemcpy(d_c, h_c, N * sizeof(float), cudaMemcpyHostToDevice);

	// Launch kernel
	int blockSize = 256;
	int gridSize = (N + blockSize - 1) / blockSize;
	AddKernel << <gridSize, 256 >> > (d_a, d_b, d_c);
	cudaDeviceSynchronize();
	// Copy device memory to host
	cudaMemcpy(h_c, d_c, N * sizeof(float), cudaMemcpyDeviceToHost);

	// show
    Print(h_c, N);

	cudaFree(d_a);
	cudaFree(d_b);
	cudaFree(d_c);

	delete[] h_a;
	delete[] h_b;
	delete[] h_c;
	return 0;
}
