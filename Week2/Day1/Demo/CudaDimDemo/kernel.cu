
#include "cuda_runtime.h"
#include "device_launch_parameters.h"

#include <stdio.h>
#include <opencv2/opencv.hpp>
#include <opencv2/highgui/highgui.hpp>

__global__ void grayConvertKernel(unsigned char *image, int width, int height)
{
    // 计算索引
    int px = blockIdx.x * blockDim.x + threadIdx.x;
    int py = blockIdx.y * blockDim.y + threadIdx.y;
    if (px > width || py > height) return;
    image[px + py * width] = 255 - image[px + py * width];
}

int main(int argc, char **argv)
{
    // 读取图像
    cv::Mat image = cv::imread("./image_0.bmp");
    std::cout << "image size: " << image.rows << "x" << image.cols <<std::endl;

    cv::Mat ori_src;
    cv::cvtColor(image, ori_src, cv::COLOR_BGR2GRAY);
    cv::Mat src = ori_src.clone();
    // 创建device存储
    unsigned char *d_image;
    cudaMalloc(&d_image, src.rows * src.cols);
    cudaMemcpy(d_image, src.data, src.rows * src.cols, cudaMemcpyHostToDevice);
    // 创建kernel
    dim3 threadsPerBlock(32, 32);
    dim3 blocksPerGrid((src.cols + threadsPerBlock.x - 1) / threadsPerBlock.x, (src.rows + threadsPerBlock.y - 1) / threadsPerBlock.y);
    grayConvertKernel<<<blocksPerGrid, threadsPerBlock>>>(d_image, src.cols, src.rows);
    cudaDeviceSynchronize();

    // 获取结果
    cudaMemcpy(src.data, d_image, src.rows * src.cols, cudaMemcpyDeviceToHost);
    cv::imshow("result", src);
    cv::imwrite("result.bmp", src);
    cv::imshow("origin", ori_src);
    cv::waitKey(0);

    // 释放device存储
    cudaFree(d_image);

    //释放源图像
    ori_src.release();
    return 0;
}