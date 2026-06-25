#pragma once

// DLL导出宏
#ifdef CUDA_TOOL_EXPORTS
#define CUDA_TOOL_API __declspec(dllexport)
#else
#define CUDA_TOOL_API __declspec(dllimport)
#endif

// 头文件依赖
#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include <cstdio>
#include <string>

class CUDA_TOOL_API CudaTool
{
public:
#pragma region 基础内存工具
	template<typename T>
	/**
	 * @brief 主机内存拷贝至设备内存
	 * @param devData    目标设备指针
	 * @param hostData   源主机指针
	 * @param elemCount  元素个数
	 */
	static inline void CopyHostToDevice(T* devData, const T* hostData, size_t elemCount);

	template<typename T>
	/**
	 * @brief 设备内存拷贝至主机内存
	 * @param hostData   目标主机指针
	 * @param devData    源设备指针
	 * @param elemCount  元素个数
	 */
	static inline void CopyDeviceToHost(T* hostData, const T* devData, size_t elemCount);

	template<typename T>
	/**
	 * @brief 分配设备内存
	 * @param devPtr     设备指针二级输出
	 * @param elemCount  元素个数
	 */
	static inline void MallocDevice(T** devPtr, size_t elemCount);

	template<typename T>
	/**
	 * @brief 分配设备内存并填充固定值
	 * @param devPtr     设备指针二级输出
	 * @param elemCount  元素个数
	 * @param value      填充字节值（仅0/255有效，cudaMemset按字节赋值）
	 */
	static inline void DeviceMallocSet(T** devPtr, size_t elemCount, unsigned char value);

	/**
	 * @brief 安全释放设备内存，空指针不报错
	 * @param devPtr 待释放设备指针
	 */
	template<typename T>
	static inline void SafeFreeDevice(T* devPtr);

	/**
	 * @brief 获取当前cuda最后错误文本
	 */
	static void GetLastError(std::string& errorMsg);
#pragma endregion

#pragma region CUDA算法算子封装
	template<typename T>
	/**
	 * @brief 向量加法核启动封装
	 */
	static inline void LaunchAddKernel(T* devA, T* devB, T* devOut, size_t elemCount);

	template<typename T>
	/**
	 * @brief Otsu大津阈值计算
	 * @param devA          输入图像设备缓冲区
	 * @param width/height 图像尺寸
	 * @param outThreshold 输出单阈值
	 */
	static inline void LaunchOtsuKernel(const T* devA, int width, int height, T* outThreshold);

	template<typename T>
	/**
	 * @brief 阈值二值分割
	 * @param devA          输入输出图像（原地二值化）
	 * @param width/height  图像尺寸
	 * @param threshold     分割阈值
	 */
	static inline void LaunchBinarySegmentationKernel(T* devA, int width, int height, T threshold);
#pragma endregion
};

// 全局CUDA状态检查
CUDA_TOOL_API void CheckCudaStatus(cudaError_t status);
CUDA_TOOL_API void CheckCudaStatus(cudaError_t status, const char* msg);

#pragma region 模板函数实现（全部inline写头文件，解决DLL链接缺失符号）
template<typename T>
inline void CudaTool::CopyHostToDevice(T* devData, const T* hostData, size_t elemCount)
{
	size_t byteSize = elemCount * sizeof(T);
	CheckCudaStatus(cudaMemcpy(devData, hostData, byteSize, cudaMemcpyHostToDevice), "CopyHostToDevice");
}

template<typename T>
inline void CudaTool::CopyDeviceToHost(T* hostData, const T* devData, size_t elemCount)
{
	size_t byteSize = elemCount * sizeof(T);
	CheckCudaStatus(cudaMemcpy(hostData, devData, byteSize, cudaMemcpyDeviceToHost), "CopyDeviceToHost");
}

template<typename T>
inline void CudaTool::MallocDevice(T** devPtr, size_t elemCount)
{
	size_t byteSize = elemCount * sizeof(T);
	CheckCudaStatus(cudaMalloc(devPtr, byteSize), "MallocDevice cudaMalloc");
}

template<typename T>
inline void CudaTool::DeviceMallocSet(T** devPtr, size_t elemCount, unsigned char value)
{
	size_t byteSize = elemCount * sizeof(T);
	CheckCudaStatus(cudaMalloc(devPtr, byteSize), "DeviceMallocSet cudaMalloc");
	CheckCudaStatus(cudaMemset(*devPtr, value, byteSize), "DeviceMallocSet cudaMemset");
}

template<typename T>
inline void CudaTool::SafeFreeDevice(T* devPtr)
{
	if (devPtr != nullptr)
	{
		CheckCudaStatus(cudaFree(devPtr), "SafeFreeDevice cudaFree");
	}
}

inline void CudaTool::GetLastError(std::string& errorMsg)
{
	errorMsg = cudaGetErrorString(cudaGetLastError());
}
#pragma endregion

#pragma region 算法算子模板封装（调用.cu中实现的imp核入口）
// 向量加法imp声明（在.cu文件实现）
template<typename T>
extern void LaunchAddKernelImp(T* devA, T* devB, T* devOut, size_t elemCount);

template<typename T>
inline void CudaTool::LaunchAddKernel(T* devA, T* devB, T* devOut, size_t elemCount)
{
	LaunchAddKernelImp(devA, devB, devOut, elemCount);
	CheckCudaStatus(cudaGetLastError(), "LaunchAddKernel launch failed");
}

// Otsu大津阈值imp声明
template<typename T>
extern void LaunchOtsuKernelImp(const T* devA, int width, int height, T* outThreshold);

template<typename T>
inline void CudaTool::LaunchOtsuKernel(const T* devA, int width, int height, T* outThreshold)
{
	LaunchOtsuKernelImp(devA, width, height, outThreshold);
	CheckCudaStatus(cudaGetLastError(), "LaunchOtsuKernel launch failed");
}

// 二值分割imp声明
template<typename T>
extern void LaunchBinarySegmentationKernelImp(T* devA, int width, int height, T threshold);

template<typename T>
inline void CudaTool::LaunchBinarySegmentationKernel(T* devA, int width, int height, T threshold)
{
	LaunchBinarySegmentationKernelImp(devA, width, height, threshold);
	CheckCudaStatus(cudaGetLastError(), "LaunchBinarySegmentationKernel launch failed");
}
#pragma endregion

#pragma region 全局CUDA错误检查实现
inline void CheckCudaStatus(cudaError_t status)
{
	CheckCudaStatus(status, "CUDA Operation");
}

inline void CheckCudaStatus(cudaError_t status, const char* msg)
{
	if (status != cudaSuccess)
	{
		printf("[CUDA ERROR] %s : %s\n", msg, cudaGetErrorString(status));
	}
}
#pragma endregion