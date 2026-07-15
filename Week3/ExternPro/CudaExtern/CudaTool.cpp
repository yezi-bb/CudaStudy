#include "CudaTool.h"
#include <stdexcept>

void CudaTool::CheckCudaStatus(cudaError_t status, const char* msg)
{
	if (status != cudaSuccess)
	{
		printf("[CUDA ERROR] %s : %s\n", msg, cudaGetErrorString(status));
		throw std::runtime_error(msg);
	}
}
