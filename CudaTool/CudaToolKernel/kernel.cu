#include "CudaTool.h"


#pragma region 加法函数
// 全局设备核函数
template<typename T>
__global__ void AddKernel(T* a, T* b, T* out, size_t elemCount)
{
	int idx = blockIdx.x * blockDim.x + threadIdx.x;
	if (idx < elemCount)
		out[idx] = a[idx] + b[idx];
}

template<typename T>
void LaunchAddKernelImp(T* devA, T* devB, T* devOut, size_t elemCount)
{
	dim3 blockSize(256);
	dim3 gridSize((elemCount + blockSize.x - 1) / blockSize.x);
	AddKernel << <gridSize, blockSize >> > (devA, devB, devOut, elemCount);
}
// 加法实例化
template CUDA_TOOL_API void LaunchAddKernelImp<unsigned char>(unsigned char*, unsigned char*, unsigned char*, size_t);
template CUDA_TOOL_API void LaunchAddKernelImp<float>(float*, float*, float*, size_t);
template CUDA_TOOL_API void LaunchAddKernelImp<uint16_t>(uint16_t*, uint16_t*, uint16_t*, size_t);
#pragma endregion


#pragma region OTSU大津算法 类间方差阈值
template<typename T>
void __global__ OtsuKernel(int* devHist, int width, int height, T* otusThreshold)
{
	// 单步骤处理即可
	if (threadIdx.x != 0)return;
	int totalpixels = width * height;
	float w0 = 0.0f;
	float mu0 = 0.0f;
	float w1 = 0.0f;
	float mu1 = 0.0f;
	unsigned long long sumAll = 0;
	T threshold = 0;
	float maxVar = 0.0f;
	for (int i = 0; i < 256; i++)
	{
		sumAll += (unsigned long long)devHist[i] * i;
	}
	// 平均灰度
	float mu = (float)sumAll / totalpixels;
	for (int k = 0; k < 256; k++)
	{
		int cnt = devHist[k];
		// 累计灰度计算
		w0 += (float)cnt / totalpixels;
		mu0 += (float)cnt * k / totalpixels;
		if (w0 > 1.0f) break;
		w1 = 1.0f - w0;
		mu1 = (mu - mu0) / w1;

		// 类间方差
		float var = w0 * w1 * (mu0 - mu1) * (mu0 - mu1);
		if (var > maxVar)
		{
			maxVar = var;
			threshold = k;
		}
	}
	*otusThreshold = threshold;
}

template<typename T>
void __global__ HistogramKernel(const T* devA, int width, int height, int* devHist)
{
	int px = blockIdx.x * blockDim.x + threadIdx.x;
	int py = blockIdx.y * blockDim.y + threadIdx.y;
	if (px < width && py < height)
	{
		int index = py * width + px;
		atomicAdd(&devHist[devA[index]], 1);
	}
}

// CUDA侧封装调用接口
template<typename T>
void  LaunchOtsuKernelImp(const T* devA, int width, int height, T* otusThreshold)
{
	dim3 block(32, 32);
	dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);

	// 获取直方图阈值计算
	int* devHist = nullptr;
	cudaMalloc(&devHist, 256 * sizeof(int));
	cudaMemset(devHist, 0, 256 * sizeof(int)); // 新增清零
	HistogramKernel << <grid, block >> > (devA, width, height, devHist);
	cudaDeviceSynchronize();

	// 执行完成了直方图计算 gpu函数直接运行就行
	OtsuKernel << <1, 64 >> > (devHist, width, height, otusThreshold);
	cudaDeviceSynchronize();

	cudaFree(devHist);
}

// 下面这几行是解决报错的核心，缺哪个加哪个
// ========== 关键：核函数 + 外层接口全部显式实例化 ==========
// 直方图核实例化
template __global__ void HistogramKernel<unsigned char>(const unsigned char*, int, int, int*);
// Otsu计算核实例化
template __global__ void OtsuKernel<unsigned char>(int*, int, int, unsigned char*);
// 对外封装接口实例化（你报错缺失的符号）
template CUDA_TOOL_API void LaunchOtsuKernelImp<unsigned char>(const unsigned char*, int, int, unsigned char*);

// 按需扩展其他类型 float / uint16_t
template __global__ void HistogramKernel<uint16_t>(const uint16_t*, int, int, int*);
template __global__ void OtsuKernel<uint16_t>(int*, int, int, uint16_t*);
template CUDA_TOOL_API void LaunchOtsuKernelImp<uint16_t>(const uint16_t*, int, int, uint16_t*);
#pragma endregion


#pragma region 二值化阈值分割
template<typename T>
void __global__ BinarySegmentationKernel(T* devA, int width, int height, T threshold)
{
	int x = blockIdx.x * blockDim.x + threadIdx.x;
	int y = blockIdx.y * blockDim.y + threadIdx.y;
	if (x < width && y < height)
	{
		int index = y * width + x;
		devA[index] = devA[index] > threshold ? 255 : 0;
	}
}

template<typename T>
void LaunchBinarySegmentationKernelImp(T* devA, int width, int height, T otusThreshold)
{
	dim3 block(32, 32);
	dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
	BinarySegmentationKernel << <grid, block >> > (devA, width, height, otusThreshold);
	cudaDeviceSynchronize();
}
// 二值分割实例化，防止后续调用报错
template __global__ void BinarySegmentationKernel<unsigned char>(unsigned char*, int, int, unsigned char);
template CUDA_TOOL_API void LaunchBinarySegmentationKernelImp<unsigned char>(unsigned char*, int, int, unsigned char);

template __global__ void BinarySegmentationKernel<uint16_t>(uint16_t*, int, int, uint16_t);
template CUDA_TOOL_API void LaunchBinarySegmentationKernelImp<uint16_t>(uint16_t*, int, int, uint16_t);

template __global__ void BinarySegmentationKernel<float>(float*, int, int, float);
template CUDA_TOOL_API void LaunchBinarySegmentationKernelImp<float>(float*, int, int, float);
#pragma endregion
