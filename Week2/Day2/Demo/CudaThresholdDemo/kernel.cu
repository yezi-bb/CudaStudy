#include "cuda_runtime.h"
#include "device_launch_parameters.h"
#include <opencv2/opencv.hpp>
#include <iostream>

__global__ void OctThresholdKernel(unsigned char* input, unsigned char* output,
    int width, int height, unsigned char threshold)
{
    int px = blockIdx.x * blockDim.x + threadIdx.x;
    int py = blockIdx.y * blockDim.y + threadIdx.y;

    if (px < width && py < height) {
        int idx = py * width + px;
        output[idx] = input[idx] > threshold ? 255 : 0;
    }
}

__global__ void OctGetThresholdHistKernel(unsigned char* input, int width, int height, unsigned int* out)
{
    int px = blockIdx.x * blockDim.x + threadIdx.x;
    int py = blockIdx.y * blockDim.y + threadIdx.y;

    if (px < width && py < height) {
        int idx = py * width + px;
        unsigned char grayVal = input[idx];
        atomicAdd(&out[grayVal], 1);
    }
}

__global__ void OctGetThresholdKernel(unsigned int* hist_value, int width, int height, unsigned char* d_outThresh)
{
    if (threadIdx.x != 0 || blockIdx.x != 0) return;

    int total_pixels = width * height;

    unsigned long long sumAll = 0;
    for (int i = 0; i < 256; i++) {
        sumAll += (unsigned long long)i * hist_value[i];
    }

    float mu = (float)sumAll / total_pixels;

    float w0 = 0.0f;
    float mu0 = 0.0f;
    float maxVariance = -1.0f;
    unsigned char bestT = 0;

    for (int T = 0; T < 256; T++) {
        unsigned int cnt = hist_value[T];
        w0 += (float)cnt / total_pixels;
        mu0 += (float)(T * cnt) / total_pixels;

        if (w0 <= 0.0f || w0 >= 1.0f) continue;

        float w1 = 1.0f - w0;
        float mu1 = (mu - mu0) / w1;

        float variance = w0 * w1 * (mu0 / w0 - mu1) * (mu0 / w0 - mu1);

        if (variance > maxVariance) {
            maxVariance = variance;
            bestT = (unsigned char)T;
        }
    }

    *d_outThresh = bestT;
}

int main(int argc, char** argv)
{
    cv::Mat src = cv::imread("lenna.jpg");
    if (src.empty()) {
        std::cout << "image_0.bmp not found" << std::endl;
        return -1;
    }

    cv::Mat src_orig = src.clone();
    cv::Mat gray;
    cv::cvtColor(src, gray, cv::COLOR_BGR2GRAY);

    unsigned char* d_input = nullptr;
    unsigned char* d_output = nullptr;

    cudaMalloc(&d_input, gray.cols * gray.rows * sizeof(unsigned char));
    cudaMemcpy(d_input, gray.data, gray.cols * gray.rows * sizeof(unsigned char), cudaMemcpyHostToDevice);

    cudaMalloc(&d_output, gray.cols * gray.rows * sizeof(unsigned char));

    dim3 block(32, 32);
    dim3 grid((gray.cols + block.x - 1) / block.x, (gray.rows + block.y - 1) / block.y);

    // 1. 统计直方图
    unsigned int* hist_value = new unsigned int[256];
    unsigned int* hist_out = nullptr;
    cudaMalloc(&hist_out, 256 * sizeof(unsigned int));
    cudaMemset(hist_out, 0, 256 * sizeof(unsigned int));

    OctGetThresholdHistKernel << <grid, block >> > (d_input, gray.cols, gray.rows, hist_out);
    cudaDeviceSynchronize();

    cudaMemcpy(hist_value, hist_out, 256 * sizeof(unsigned int), cudaMemcpyDeviceToHost);

    for (int i = 0; i < 256; i++) {
        printf("hist %d: %u\n", i, hist_value[i]);
    }

    // 2. 计算 Otsu 阈值
    unsigned char thresh[1] = { 0 };
    unsigned char* d_thresh = nullptr;
    cudaMalloc(&d_thresh, sizeof(unsigned char));

    OctGetThresholdKernel << <1, 64 >> > (hist_out, gray.cols, gray.rows, d_thresh);
    cudaDeviceSynchronize();

    cudaMemcpy(thresh, d_thresh, sizeof(unsigned char), cudaMemcpyDeviceToHost);

    std::cout << "thresh: " << (int)thresh[0] << std::endl;

    // 3. 阈值分割
    OctThresholdKernel << <grid, block >> > (d_input, d_output, gray.cols, gray.rows, thresh[0]);
    cudaDeviceSynchronize();

    cudaMemcpy(gray.data, d_output, gray.cols * gray.rows * sizeof(unsigned char), cudaMemcpyDeviceToHost);

    cv::imshow("src_orig", src_orig);
    cv::imshow("gray", gray);
    cv::waitKey(0);

    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(hist_out);
    cudaFree(d_thresh);
    delete[] hist_value;

    return 0;
}