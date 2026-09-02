#pragma once

/**
 * @file cuda_utils.hpp
 * @brief Week01 Day03 开源桩：CUDA 健康监控与显存重建
 *
 * 对应 OCT 闭源接口（VGPU_Process.cuh），语义对齐、不复制 DLL：
 *   check_cuda_ok()     ? VGPU_GetCudaErrorStatus()     上下文是否还健康
 *   vram_snapshot()     ? VGPU_GetCurrentGPUMemory()    读整卡 total/free/used
 *   reset_device()      ? VGPU_ResetCudaMemory()        毁掉上下文（最后手段）
 *   safe_reinit()       ? VGPU_Reallocate_memory()      同尺寸重建缓冲（上下文仍活）
 *
 * 口诀：
 *   缓冲没了、卡还活着 → safe_reinit / Reallocate
 *   卡（上下文）死了   → reset_device，然后必须重新 Allocate
 *   还没坏、只是空间不够 → 不要 Reset，先看 vram_snapshot
 *
 * 本文件全部 inline，调用方可只 #include，暂不链进独立 .cu。
 * Day04 的 PipelineContext::init/shutdown/mem_info 应建在这些函数之上。
 */

#include <cuda_runtime.h>
#include <stdio.h>
#include <stdlib.h>
#include <cstdint>

namespace oct_cuda
{

	/**
	 * 整卡显存快照（Video RAM Snapshot）。
	 *
	 * 数据来自 cudaMemGetInfo，是「这块 GPU 上所有进程」的视角，
	 * 含驱动、桌面显示、其它软件，不能当本进程 cudaMalloc 的精确账本。
	 * 用途是看趋势：IPA/DL 前后 free 掉了多少、回拉前够不够装 bulk。
	 *
	 * used_bytes = total_bytes - free_bytes，单位一律为字节；
	 * 打日志时再自行换算 GB（/ 1024^3）。
	 */
	struct VramSnapshot
	{
		std::size_t total_bytes = 0;  ///< 设备总显存
		std::size_t free_bytes  = 0;  ///< 当前空闲显存
		std::size_t used_bytes  = 0;  ///< 近似已用 = total - free
	};

	/**
	 * 检查单次 CUDA API 返回值并打印，不抛异常、不 abort。
	 *
	 * @param err  cudaMalloc / cudaMemcpy / cudaMemGetInfo 等返回的 cudaError_t
	 * @param what 便于日志定位的操作名，例如 "cudaMemGetInfo"
	 *
	 * 注意：kernel 是异步的。<<<>>> 之后的启动错误要用 cudaGetLastError；
	 * 越界等运行错误往往要 cudaDeviceSynchronize 之后才会出现在 err 里。
	 * 本函数只看传入的 err，不会主动同步设备。
	 */
	inline void check_cuda_error(cudaError_t err, const char* what)
	{
		if (err != cudaSuccess)
		{
			fprintf(stderr, "[CUDA] %s: %s\n", what, cudaGetErrorString(err));
		}
	}

	/**
	 * 探测当前线程的「最后一次 CUDA 错误」是否为成功。
	 *
	 * 对齐 VGPU_GetCudaErrorStatus：返回 true = 正常，false = 异常
	 *（与 CUDA 原生 cudaSuccess==0 的「0 表示成功」方向相反，这里用 bool 更直观）。
	 *
	 * 实现用的是 cudaGetLastError()：读取后会清空错误位。
	 * 若只想给 UI 偷看、留给后续逻辑再处理，应改用 cudaPeekAtLastError()。
	 *
	 * sticky error：illegal memory access 等一旦发生，后续几乎所有 CUDA
	 * 调用都会失败，直到 reset_device()。此时 false 不等于「这一帧图坏了」，
	 * 而是整条 GPU 管线已死，宿主应停采集、禁止继续算，再决定要不要 Reset。
	 */
	inline bool check_cuda_ok()
	{
		return cudaGetLastError() == cudaSuccess;
	}

	/**
	 * 拍一张当前 GPU 的显存快照。
	 *
	 * 对齐 VGPU_GetCurrentGPUMemory(total, free, used)。
	 * 内部 cudaMemGetInfo(&free, &total)；失败时 check_cuda_error 打日志，
	 * 结构体可能仍为 0，调用方应再配 check_cuda_ok()。
	 *
	 * 建议打点位置（OCT 旁路）：
	 *   - 任意重计算 / 回拉前
	 *   - IPA 或深度学习前后（看有没有泄漏、要不要 safe_reinit）
	 */
	inline VramSnapshot vram_snapshot()
	{
		VramSnapshot snapshot;
		std::size_t free_bytes  = 0;
		std::size_t total_bytes = 0;
		check_cuda_error(cudaMemGetInfo(&free_bytes, &total_bytes), "cudaMemGetInfo");
		snapshot.total_bytes = total_bytes;
		snapshot.free_bytes  = free_bytes;
		snapshot.used_bytes  = total_bytes - free_bytes;
		return snapshot;
	}

	/**
	 * 重置当前进程的 CUDA 设备上下文。最后手段。
	 *
	 * 对齐 VGPU_ResetCudaMemory()。内部 cudaDeviceReset()：
	 *   - 本进程内所有 device 指针、cuFFT plan、stream 全部作废
	 *   - 禁止再 cudaFree 旧指针（会二次出错）
	 *   - 同一进程的 OpenCV CUDA / TensorRT / GL 互操作也会一起死
	 *
	 * Reset 之后必须按全参数重新 Allocate（本桩尚无 PipelineContext，
	 * 调用方自己 cudaSetDevice + 再 malloc）。不要在成像 kernel 路径里随手调用；
	 * 应先停 GPU 工作线程，再 Reset。
	 *
	 * @return Reset 后 check_cuda_ok()；true 只表示错误位清了，不表示缓冲已重建
	 */
	inline bool reset_device()
	{
		check_cuda_error(cudaDeviceReset(), "cudaDeviceReset");
		return check_cuda_ok();
	}

	/**
	 * 在「上下文仍健康、只是成像缓冲被挤掉」时，按上次 Shape 重建计算区。
	 *
	 * 对齐 VGPU_Reallocate_memory()：深度学习 / IPA 占用结束后，
	 * 等价于 Free(计算缓冲, 可保留标定) + Allocate(同样尺寸)。
	 * 不调用 cudaDeviceReset，旧上下文还活着。
	 *
	 * 当前为桩：只拍一张重建前的显存快照，真正的
	 *   ctx.shutdown(free_calib=false);
	 *   ctx.init(ctx.last_shape());
	 * 等 Day04 PipelineContext 落地后再接上。
	 *
	 * 与 reset_device 的分界：
	 *   check_cuda_ok()==false  → 先停线程，reset_device，再全参 Allocate
	 *   仅 free 变少 / 缓冲被 DL 拆掉 → 走本函数
	 */
	inline bool safe_reinit(/* PipelineContext& ctx */)
	{
		auto before = vram_snapshot();
		(void)before;  // 桩阶段：保留「重建前」快照，便于以后打对比日志
		// ctx.shutdown(/*free_calib=*/false);
		// ctx.init(ctx.last_shape());
		return check_cuda_ok();
	}

}  // namespace octy_cuda
