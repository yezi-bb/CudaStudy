#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include "CudaTool.h"

#pragma region BinaryKernel
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
	BinaryKernel<<<grid, block>>>(d_in, d_out, width, height, threshold);
}

// 显式实例化：DLL 目前仅导出 unsigned char 特化
template DLL_EXPORT void LaunchBinaryKernelImpl<unsigned char>(
	unsigned char* d_in, unsigned char* d_out, size_t width, size_t height, unsigned char threshold);
#pragma endregion

#pragma region BiModalValley 双峰谷底阈值
// 直方图统计核：hist 使用 int 计数，必须原子加法
__global__ void GetHistArray(unsigned char* d_in, int* d_hist, size_t width, size_t height)
{
	size_t x = blockIdx.x * blockDim.x + threadIdx.x;
	size_t y = blockIdx.y * blockDim.y + threadIdx.y;
	if (x < width && y < height)
	{
		size_t id = y * width + x;
		unsigned char grayVal = d_in[id];
		atomicAdd(&d_hist[grayVal], 1);
	}
}

__global__ void BiModalValleyKernel(int* d_hist, unsigned char* outThreshold)
{
	if (threadIdx.x != 0)
		return;

	float smooth[256];
	// 1. 三点平滑直方图
	for (int i = 0; i < 256; i++)
	{
		if (i == 0)
			smooth[i] = (d_hist[i] + d_hist[i + 1]) / 2.0f;
		else if (i == 255)
			smooth[i] = (d_hist[i - 1] + d_hist[i]) / 2.0f;
		else
			smooth[i] = (d_hist[i - 1] + d_hist[i] + d_hist[i + 1]) / 3.0f;
	}

	int peaks[256];
	int peakCnt = 0;
	for (int i = 1; i <= 254; i++)
	{
		if (smooth[i] > smooth[i - 1] && smooth[i] > smooth[i + 1])
		{
			peaks[peakCnt++] = i;
		}
	}

	// 峰值不足两组，兜底阈值 127
	if (peakCnt < 2)
	{
		*outThreshold = 127;
		return;
	}

	int p1 = peaks[0];
	int p2 = peaks[peakCnt - 1];
	if (p1 > p2)
	{
		int temp = p1;
		p1 = p2;
		p2 = temp;
	}

	// 两峰之间寻找谷底
	int valleyPos = p1 + 1;
	float minVal = smooth[valleyPos];
	for (int t = p1 + 1; t < p2; t++)
	{
		if (smooth[t] < minVal)
		{
			minVal = smooth[t];
			valleyPos = t;
		}
	}
	*outThreshold = static_cast<unsigned char>(valleyPos);
}

// 主机端封装：当前直方图算法仅支持 8bit 灰度
template <typename T>
void LaunchHistsholdKernelImpl(T* d_in, T* d_outThresh, size_t width, size_t height)
{
	static_assert(sizeof(T) == 1, "LaunchHistsholdKernelImpl currently supports 8-bit pixel only");

	int* d_hist = nullptr;
	cudaMalloc(&d_hist, sizeof(int) * 256);
	cudaMemset(d_hist, 0, sizeof(int) * 256);

	dim3 block(16, 16);
	dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
	GetHistArray<<<grid, block>>>(reinterpret_cast<unsigned char*>(d_in), d_hist, width, height);

	BiModalValleyKernel<<<1, 1>>>(d_hist, reinterpret_cast<unsigned char*>(d_outThresh));

	cudaFree(d_hist);
}

template DLL_EXPORT void LaunchHistsholdKernelImpl<unsigned char>(
	unsigned char* d_in, unsigned char* d_outThresh, size_t width, size_t height);
#pragma endregion