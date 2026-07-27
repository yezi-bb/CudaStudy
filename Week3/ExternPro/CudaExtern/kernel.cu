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
	BinaryKernel << <grid, block >> > (d_in, d_out, width, height, threshold);
}

// 显式实例化：DLL 目前仅导出 unsigned char 特化
template DLL_EXPORT void LaunchBinaryKernelImpl<unsigned char>(
	unsigned char* d_in, unsigned char* d_out, size_t width, size_t height, unsigned char threshold);
#pragma endregion

#pragma region BiModalValley 双峰谷底阈值
// 直方图统计核：hist 使用 int 计数，必须原子加法
template <typename T>
__global__ void GetHistArray(T* d_in, int* d_hist, size_t width, size_t height)
{
	size_t x = blockIdx.x * blockDim.x + threadIdx.x;
	size_t y = blockIdx.y * blockDim.y + threadIdx.y;
	if (x < width && y < height)
	{
		size_t id = y * width + x;
		T grayVal = d_in[id];
		atomicAdd(&d_hist[grayVal], 1);
	}
}

template<typename T>
__global__ void BiModalValleyKernel(int* d_hist, T* outThreshold)
{
	if (threadIdx.x != 0)
		return;

	float smooth[256];
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
	T valleyThresh = T(127);
	if (peakCnt >= 2)
	{
		int p1 = peaks[0];
		int p2 = peaks[peakCnt - 1];
		if (p1 > p2)
		{
			int temp = p1;
			p1 = p2;
			p2 = temp;
		}
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
		valleyThresh = static_cast<T>(valleyPos);
	}
	*outThreshold = valleyThresh;
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
	GetHistArray << <grid, block >> > (reinterpret_cast<unsigned char*>(d_in), d_hist, width, height);

	BiModalValleyKernel << <1, 1 >> > (d_hist, reinterpret_cast<unsigned char*>(d_outThresh));

	cudaFree(d_hist);
}

template DLL_EXPORT void LaunchHistsholdKernelImpl<unsigned char>(
	unsigned char* d_in, unsigned char* d_outThresh, size_t width, size_t height);
#pragma endregion


#pragma region 大津算法 otsu

// 主机端封装：\(\sigma^2(T)=w_0 w_1 (u_0-u_1)^2\)

template <typename T>
__global__ void OTSUKernel(int* dist, T* threshold, size_t width, size_t height)
{
	// 避免除法
	if (threadIdx.x != 0)return;

	// totalPix：图像总像素数量 N
	const double totalPix = (double)width * height;
	// U_total = ∑(i=0→255) i·n_i  未归一化的加权和
	double U_total = .0;
	for (int i = 0; i < 256; i++)
	{
		U_total += dist[i] * i;
	}
	// w0 = W₀(T) = ∑(i=0→T) n_i
   // 阈值T以下灰度的像素总数量
	double w0 = 0.0;
	// u0 = U₀(T) = ∑(i=0→T) i·n_i
	// 阈值T以下灰度「灰度 × 像素个数」累加和
	double u0 = 0.0;

	// 记录最大类间方差
	double maxSigma = 0.0;
	// 最优分割阈值，初始兜底127
	unsigned char bestT = 127;

	// 遍历全部候选阈值 T ∈ [0, 254]
	for (int T = 0; T <= 254; T++)
	{
		// 前缀增量累加：不断扩充 <= T 的灰度集合
		w0 += dist[T];
		u0 += (double)T * dist[T];

		// w1 = N - W₀(T)，阈值T以上灰度的像素总数量
		double w1 = totalPix - w0;

		// 边界判断：全部像素划分至同一类，无分割意义，跳过
		if (w0 <= 0 || w1 <= 0)
			continue;

		// μ₀ = U₀ / W₀  类别C0(灰度≤T)平均灰度
		double mu0 = u0 / w0;
		// μ₁ = (U_total - U₀) / W₁ 类别C1(灰度>T)平均灰度
		double mu1 = (U_total - u0) / w1;

		// ω₀ = W₀ / N 类别C0像素出现概率
		double omega0 = w0 / totalPix;
		// ω₁ = W₁ / N 类别C1像素出现概率
		double omega1 = w1 / totalPix;

		// Otsu标准类间方差 σ_B² = ω₀ ω₁ (μ₀−μ₁)²
		double sigma = omega0 * omega1 * (mu0 - mu1) * (mu0 - mu1);

		// 更新最大值与最优阈值
		if (sigma > maxSigma)
		{
			maxSigma = sigma;
			bestT = (unsigned char)T;
		}

	}
	// 将最优阈值写入设备显存
	*threshold = bestT;
}


template <typename T>
void LaunchOTSUImpl(T* d_in, T* d_outThresh, size_t width, size_t height)
{
	static_assert(sizeof(T) == 1, "LaunchOTSUImpl currently supports 8-bit pixel only");

	int* d_hist = nullptr;
	cudaMalloc(&d_hist, sizeof(int) * 256);
	cudaMemset(d_hist, 0, sizeof(int) * 256);

	dim3 block(16, 16);
	dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
	GetHistArray << <grid, block >> > (d_in, d_hist, width, height);

	// 大津算法求取阈值
	OTSUKernel << <1, 1 >> > (d_hist, d_outThresh, width, height);

	cudaFree(d_hist);
}

template DLL_EXPORT void LaunchOTSUImpl<unsigned char>(
	unsigned char* d_in, unsigned char* d_outThresh, size_t width, size_t height);
#pragma endregion