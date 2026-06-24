/*****************************************************************//**
 * @file   kernel.cu
 * @brief
OCT 标准降噪预处理流程

原始 OCT 灰度图
→ GPU 3×3 中值滤波（消除散斑极值噪点）
→ GPU 高斯平滑（均衡灰度、保留边缘）
→ Otsu 自适应阈值分割 → 病灶二值掩码
 * @author Administrator
 * @date   June 2026
 *********************************************************************/

#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include <stdio.h>
#include <stdlib.h>
#include <algorithm>
#include <opencv2/opencv.hpp>
 /**
  * Description:
	*  * @brief   3×3 中值滤波   中位数字
  * @param   input: 输入图像
  * @param   output: 输出图像
  * @param   width: 图像宽度
  * @param   height: 图像高度
  */
void __global__ kernelMedianFilter(unsigned char* input, unsigned char* output, int width, int height)
{
	int x = blockIdx.x * blockDim.x + threadIdx.x;
	int y = blockIdx.y * blockDim.y + threadIdx.y;
	int index = y * width + x;
	if (x > 0 && y > 0 && x < width - 1 && y < height - 1)
	{
		unsigned char temp[9];
		int temp_ptr = 0;
		for (int dy = -1; dy <= 1; dy++)
		{
			for (int dx = -1; dx <= 1; dx++)
			{
				temp[temp_ptr++] = input[(y + dy) * width + x + dx];
			}
		}
		// 中值滤波
		for (int i = 0; i < 9; i++)
		{
			for (int j = i + 1; j < 9; j++)
			{
				if (temp[i] > temp[j])
				{
					int temp_ = temp[i];
					temp[i] = temp[j];
					temp[j] = temp_;
				}
			}
		}
		output[index] = temp[4];
	}
	else
	{
		output[index] = input[index];		// 复制边缘值
	}
}

/**
 * Description:
 *		gaussianBlur 平滑
 * @param input
 * @param output
 * @param width
 * @param height
 * @return
 */
void __global__ kernelGaussianBlur(unsigned char* input, unsigned char* output, int width, int height)
{
	int x = blockIdx.x * blockDim.x + threadIdx.x;
	int y = blockIdx.y * blockDim.y + threadIdx.y;
	int index = y * width + x;
	// 边缘处理核函数 核函数可以修改
	unsigned char gaussian_kernel[3][3] = {
	{0,-1,0},
	{-1,4,-1},
	{0,-1,0}
	};
	if (x > 0 && y > 0 && x < width - 1 && y < height - 1)
	{
		unsigned char temp[9];
		int temp_ptr = 0;
		for (int dy = -1; dy <= 1; dy++)
		{
			for (int dx = -1; dx <= 1; dx++)
			{
				temp[temp_ptr++] = input[(y + dy) * width + x + dx];
			}
		}
		output[index] = (temp[0] * gaussian_kernel[0][0] + temp[1] * gaussian_kernel[0][1] + temp[2] * gaussian_kernel[0][2] +
			temp[3] * gaussian_kernel[1][0] + temp[4] * gaussian_kernel[1][1] + temp[5] * gaussian_kernel[1][2] +
			temp[6] * gaussian_kernel[2][0] + temp[7] * gaussian_kernel[2][1] + temp[8] * gaussian_kernel[2][2]);
	}
	else
	{
		output[index] = input[index];		// 复制边缘值
	}
}

int main(int argc, char** argv)
{
	cv::Mat src = cv::imread("image_0.bmp");
	// 转化为灰度
	cv::Mat gray;
	cv::cvtColor(src, gray, cv::COLOR_BGR2GRAY);

	// devcice memory
	unsigned char* input, * output;
	cudaMalloc(&input, gray.rows * gray.cols * sizeof(unsigned char));
	cudaMalloc(&output, gray.rows * gray.cols * sizeof(unsigned char));

	// 图像数据拷贝
	cudaMemcpy(input, gray.data, gray.rows * gray.cols * sizeof(unsigned char), cudaMemcpyHostToDevice);

	dim3 block(16, 16);
	dim3 grid(gray.cols / block.x + 1, gray.rows / block.y + 1);
	kernelMedianFilter << <grid, block >> > (input, output, src.cols, src.rows);
	cudaDeviceSynchronize();
	// 中值滤波
	cv::Mat median_filter = gray.clone();
	cudaMemcpy(median_filter.data, output, median_filter.rows * median_filter.cols * sizeof(unsigned char), cudaMemcpyDeviceToHost);
	cv::imshow("median_filter", median_filter);

	// 高斯滤波
	cv::Mat gaussian_filter = median_filter.clone();
	cudaMemcpy(input, gaussian_filter.data, gaussian_filter.rows * gaussian_filter.cols * sizeof(unsigned char), cudaMemcpyHostToDevice);
	kernelGaussianBlur << <grid, block >> > (input, output, src.cols, src.rows);
	cudaDeviceSynchronize();
	cudaMemcpy(gaussian_filter.data, output, gaussian_filter.rows * gaussian_filter.cols * sizeof(unsigned char), cudaMemcpyDeviceToHost);

	cv::imshow("gaussian_filter", gaussian_filter);
	cv::imshow("gray", gray);
	cv::waitKey(0);

	// delate
	cudaFree(input);
	cudaFree(output);
	return 0;
}
