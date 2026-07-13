#pragma once

// DLL导出宏放在最顶部
#ifdef CUDA_EXTERN_DLL
#define DLL_EXPORT __declspec(dllexport)
#else
#define DLL_EXPORT __declspec(dllimport)
#endif

#include "cuda_runtime.h"
#include <stdio.h>
#include <cstddef>

// 前向声明extern模板实现（定义在.cu）
template <typename T>
DLL_EXPORT void LaunchBinaryKernelImpl(T* d_in, T* d_out, size_t width, size_t height, T threshold);

class DLL_EXPORT CudaTool
{
private:
	// 私有构造
	CudaTool() = default;
public:
	~CudaTool() = default;

	// 局部静态单例（推荐，修复静态实例未定义问题）
	static CudaTool& getInstance()
	{
		static CudaTool inst;
		return inst;
	}

#pragma region 内存拷贝
	template<typename T>
	void copyHostToDevice(T* dst, T* src, size_t size);

	template<typename T>
	void copyDeviceToHost(T* dst, T* src, size_t size);
#pragma endregion

	void CheckCudaStatus(cudaError_t status, const char* msg);

#pragma region 二值化接口
	template<typename T>
	void LaunchBinaryKernel(T* src, T* dst, size_t width, size_t height, T threshold);
#pragma endregion
};

// ===== 模板成员实现必须放在.h =====
template<typename T>
void CudaTool::copyHostToDevice(T* dst, T* src, size_t size)
{
	auto ret = cudaMemcpy(dst, src, size, cudaMemcpyHostToDevice);
	CheckCudaStatus(ret, "cudaMemcpyHostToDevice");
}

template<typename T>
void CudaTool::copyDeviceToHost(T* dst, T* src, size_t size)
{
	auto ret = cudaMemcpy(dst, src, size, cudaMemcpyDeviceToHost);
	CheckCudaStatus(ret, "cudaMemcpyDeviceToHost");
}

template<typename T>
inline void CudaTool::LaunchBinaryKernel(T* src, T* dst, size_t width, size_t height, T threshold)
{
	T* d_in = nullptr;
	T* d_out = nullptr;
	size_t byteSize = width * height * sizeof(T);

	try
	{
		CheckCudaStatus(cudaMalloc(&d_in, byteSize), "cudaMalloc d_in");
		CheckCudaStatus(cudaMalloc(&d_out, byteSize), "cudaMalloc d_out");

		copyHostToDevice(d_in, src, byteSize);

		LaunchBinaryKernelImpl(d_in, d_out, width, height, threshold);
		CheckCudaStatus(cudaGetLastError(), "BinaryKernel launch");
		CheckCudaStatus(cudaDeviceSynchronize(), "BinaryKernel execute sync");

		copyDeviceToHost(dst, d_out, byteSize);
	}
	catch (...)
	{
		// 无论哪里抛出异常，都确保释放已分配显存
		if (d_in)  cudaFree(d_in);
		if (d_out) cudaFree(d_out);
	}

	// 正常流程释放
	CheckCudaStatus(cudaFree(d_in), "cudaFree d_in");
	CheckCudaStatus(cudaFree(d_out), "cudaFree d_out");
}