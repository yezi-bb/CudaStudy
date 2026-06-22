#include <iostream>
#include "CudaTool.h"

int main()
{
    // 1. 定义数据长度
    const int dataSize = 1024;
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
    cudaMalloc(&devA, dataSize * sizeof(float));
    cudaMalloc(&devB, dataSize * sizeof(float));
    cudaMalloc(&devOut, dataSize * sizeof(float));

    // 4. 调用CudaTool封装接口
    // CPU数据拷贝到GPU
    CudaTool::CopyHostToDevice(hostA, devA, dataSize);
    CudaTool::CopyHostToDevice(hostB, devB, dataSize);
    // 执行GPU加法核函数
    CudaTool::LaunchAddKernel(devA, devB, devOut, dataSize);

    // 5. GPU结果拷贝回CPU
    cudaMemcpy(hostResult, devOut, dataSize * sizeof(float), cudaMemcpyDeviceToHost);

    // 6. 打印前5组结果验证
    std::cout << "GPU加法计算结果：" << std::endl;
    for (int i = 0; i < 5; i++)
    {
        std::cout << "idx " << i << " : " << hostResult[i] << std::endl;
    }

    // 7. 释放GPU显存
    CudaTool::SafeFreeDevice(devA);
    CudaTool::SafeFreeDevice(devB);
    CudaTool::SafeFreeDevice(devOut);

    // 释放CPU内存
    delete[] hostA;
    delete[] hostB;
    delete[] hostResult;

    std::cout << "\n计算执行完成！" << std::endl;
    return 0;
}