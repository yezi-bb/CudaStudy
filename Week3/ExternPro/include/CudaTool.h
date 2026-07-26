#pragma once

// DLL 导出宏：库工程定义 CUDA_EXTERN_DLL，调用方不定义 → dllimport
#ifdef CUDA_EXTERN_DLL
#define DLL_EXPORT __declspec(dllexport)
#else
#define DLL_EXPORT __declspec(dllimport)
#endif

#include "cuda_runtime.h"
#include <stdio.h>
#include <cstddef>
#include <stdexcept>

// 模板内核启动实现（定义在 kernel.cu，需显式实例化后才能跨 DLL 使用）
template <typename T>
DLL_EXPORT void LaunchBinaryKernelImpl(T* d_in, T* d_out, size_t width, size_t height, T threshold);

template <typename T>
DLL_EXPORT void LaunchHistsholdKernelImpl(T* d_in, T* threshold, size_t width, size_t height);

class DLL_EXPORT CudaTool
{
private:
	CudaTool() = default;
public:
	~CudaTool() = default;

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

#pragma region 求取阈值接口
	template<typename T>
	void LaunchHistsholdKernel(T* src, T* threshold, size_t width, size_t height);
#pragma endregion
};

// ===== 模板成员实现必须在头文件（调用方也会编译这些符号）=====
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

		CheckCudaStatus(cudaFree(d_in), "cudaFree d_in");
		d_in = nullptr;
		CheckCudaStatus(cudaFree(d_out), "cudaFree d_out");
		d_out = nullptr;
	}
	catch (...)
	{
		if (d_in)  cudaFree(d_in);
		if (d_out) cudaFree(d_out);
		throw;
	}
}

template<typename T>
inline void CudaTool::LaunchHistsholdKernel(T* src, T* threshold, size_t width, size_t height)
{
	T* d_in = nullptr;
	T* d_threshold = nullptr;
	size_t byteSize = width * height * sizeof(T);

	try
	{
		CheckCudaStatus(cudaMalloc(&d_in, byteSize), "cudaMalloc d_in");
		CheckCudaStatus(cudaMalloc(&d_threshold, sizeof(T)), "cudaMalloc threshold");
		copyHostToDevice(d_in, src, byteSize);
		LaunchHistsholdKernelImpl(d_in, d_threshold, width, height);
		CheckCudaStatus(cudaGetLastError(), "HistsholdKernel launch");
		CheckCudaStatus(cudaDeviceSynchronize(), "HistsholdKernel execute sync");
		copyDeviceToHost(threshold, d_threshold, sizeof(T));

		CheckCudaStatus(cudaFree(d_in), "cudaFree d_in");
		d_in = nullptr;
		CheckCudaStatus(cudaFree(d_threshold), "cudaFree threshold");
		d_threshold = nullptr;
	}
	catch (...)
	{
		if (d_in)  cudaFree(d_in);
		if (d_threshold) cudaFree(d_threshold);
		throw;
	}
}
