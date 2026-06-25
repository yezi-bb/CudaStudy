#include <iostream>
#include "CudaTool.h"
#include "opencv2/opencv.hpp"

void OtusToolDemo()
{
	unsigned char bestThreshold = 0;
	cv::Mat img = cv::imread("lenna.jpg");
	// 灰度转化
	cv::Mat grayImg;
	cv::cvtColor(img, grayImg, cv::COLOR_BGR2GRAY);

	// 创建设备数据
	unsigned char* deviceA;
	CudaTool::MallocDevice<unsigned char>(&deviceA, grayImg.cols * grayImg.rows);
	CudaTool::CopyHostToDevice<unsigned char>(deviceA, grayImg.data, grayImg.cols * grayImg.rows);

	unsigned char* deviceB = 0;
	CudaTool::MallocDevice<unsigned char>(&deviceB, 1);

	// 运行
	CudaTool::LaunchOtsuKernel<unsigned char>(deviceA, grayImg.cols, grayImg.rows, deviceB);
	cudaMemcpy(&bestThreshold, deviceB, 1, cudaMemcpyDeviceToHost);

	std::cout << "Otus threshold: " << bestThreshold << std::endl;

	// 显示分割结果
	cv::Mat binaryImg = grayImg.clone();
	// 运行
	CudaTool::LaunchBinarySegmentationKernel<unsigned char>(deviceA, grayImg.cols, grayImg.rows, bestThreshold);
	cudaMemcpy(binaryImg.data, deviceA, grayImg.cols * grayImg.rows * sizeof(unsigned char), cudaMemcpyDeviceToHost);

	cv::imshow("origin img", img);
	cv::imshow("Gray image", grayImg);
	cv::imshow("Binary segmentation", binaryImg);
	cv::waitKey(0);

	cudaFree(deviceA);
	cudaFree(deviceB);
}


void Add()
{
	// 1. 定义数据长度
	size_t dataSize = 1024;
	float* hostA = new float[dataSize];
	float* hostB = new float[dataSize];
	float* hostResult = new float[dataSize] {0.0f};

	// 2. CPU端填充测试数据
	for (int i = 0; i < dataSize; i++)
	{
		hostA[i] = static_cast<float>(i);
		hostB[i] = 1.0f;
	}

	// 3. 申请GPU显存
	float* devA = nullptr;
	float* devB = nullptr;
	float* devOut = nullptr;
	CudaTool::MallocDevice<float>(&devA, dataSize);
	CudaTool::MallocDevice<float>(&devB, dataSize);
	CudaTool::MallocDevice<float>(&devOut, dataSize);

	// 4. 调用CudaTool封装接口
	// CPU数据拷贝到GPU
	CudaTool::CopyHostToDevice<float>(devA, hostA, dataSize);
	CudaTool::CopyHostToDevice<float>(devB, hostB, dataSize);
	// 执行GPU加法核函数
	CudaTool::LaunchAddKernel<float>(devA, devB, devOut, dataSize);

	// 5. GPU结果拷贝回CPU
	CudaTool::CopyDeviceToHost<float>(hostResult, devOut, dataSize);

	// 6. 打印前5组结果验证
	std::cout << "GPU加法计算结果：" << std::endl;
	for (int i = 0; i < 5; i++)
	{
		std::cout << "idx " << i << " : " << hostResult[i] << std::endl;
	}

	// 7. 释放GPU显存
	CudaTool::SafeFreeDevice<float>(devA);
	CudaTool::SafeFreeDevice<float>(devB);
	CudaTool::SafeFreeDevice<float>(devOut);

	// 释放CPU内存
	delete[] hostA;
	delete[] hostB;
	delete[] hostResult;

	std::cout << "\n计算执行完成！" << std::endl;
}
int main()
{
	OtusToolDemo();
	return 0;
}