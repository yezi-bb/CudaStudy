# CUDA 内存管理三大核心 API + 三类拷贝方向完整详解

## 一、四大核心内存 API（cudaMalloc /cudaFree/cudaMemcpy + 补充主机分配 cudaMallocHost）

### 1. cudaMalloc —— 在 GPU 全局显存分配内存

#### 函数原型

cpp

运行

```
cudaError_t cudaMalloc(void** devPtr, size_t size);
```

#### 参数说明

- `devPtr`：输出参数，接收**显存地址指针**（GPU 端虚拟地址，CPU 不能直接解引用）；
- `size`：需要分配的字节大小。

#### 作用

在 Device 全局显存（Global Memory）开辟一块内存，仅 GPU 线程可直接读写；CPU 只能通过拷贝 API 间接交互。

#### 使用示例

cpp

运行

```
float* d_data = nullptr;
size_t byteSize = 1024 * sizeof(float);
// 分配显存
cudaMalloc(&d_data, byteSize);
```

#### 注意事项

1. 显存地址与 CPU 内存地址空间完全隔离，不能直接赋值、不能直接读写；
2. 分配失败返回非 0 错误码（显存不足、设备未初始化等）；
3. 分配后必须配对`cudaFree`释放，否则显存泄漏。

### 2. cudaFree —— 释放 GPU 显存

#### 函数原型

cpp

运行

```
cudaError_t cudaFree(void* devPtr);
```

#### 参数

`devPtr`：cudaMalloc 得到的显存指针。

#### 作用

回收 GPU 全局显存，释放显卡内存资源。

#### 坑点

1. 重复 free、free 空指针、free 主机内存指针都会报错；
2. 程序退出前不释放会造成显存泄漏，长期循环程序会显存占满崩溃。

#### 配套规范：分配 / 释放成对

cpp

运行

```
float* d_data;
cudaMalloc(&d_data, 1024);
// ...计算逻辑...
cudaFree(d_data);
d_data = nullptr;
```

### 3. cudaMemcpy —— CPU 与 GPU 之间数据拷贝核心函数

#### 函数原型

cpp

运行

```
cudaError_t cudaMemcpy(
    void* dst,        // 目标地址
    const void* src,  // 源地址
    size_t count,     // 拷贝字节数
    cudaMemcpyKind kind // 拷贝方向枚举（核心）
);
```

#### 核心参数 `cudaMemcpyKind` 决定三类拷贝，下文单独展开。

#### 特性

1. **同步阻塞 API**：CPU 调用后会等待拷贝完全完成才返回（默认同步行为）；
2. 地址校验严格：源、目标必须分别对应主机 / 显存，传错类型直接报错；
3. 支持批量连续内存拷贝，带宽远高于逐元素传输。

### 补充关键 API：cudaMallocHost（锁页主机内存，配套拷贝优化）

很多教材会把它归为内存管理四大 API，用于加速拷贝：

cpp

运行

```
cudaError_t cudaMallocHost(void** hostPtr, size_t size);
```

普通主机内存（malloc/new）是可分页内存，操作系统会交换到磁盘，拷贝速度慢；

`cudaMallocHost`分配**锁页内存（Pinned Memory）**，物理内存固定不换页，Host↔Device 拷贝带宽大幅提升。

释放配套：`cudaFreeHost(hostPtr)`。

------

## 二、cudaMemcpy 三种拷贝方向（cudaMemcpyKind 枚举区分）

### 枚举总览

cpp

运行

```
enum cudaMemcpyKind
{
    cudaMemcpyHostToDevice,  // 1.主机内存 → GPU显存
    cudaMemcpyDeviceToHost,  // 2.GPU显存 → 主机内存
    cudaMemcpyDeviceToDevice,// 3.GPU显存 → GPU显存
    cudaMemcpyHostToHost     // CPU内存互拷，极少使用
};
```

## 1. cudaMemcpyHostToDevice：主机 → 显存（计算前传输入数据）

### 使用场景

CPU 生成 / 读取原始数据，上传到 GPU 显存，供核函数并行计算。

### 完整流程示例

cpp

运行

```
// 1.CPU分配主机内存
size_t num = 1024;
size_t bytes = num * sizeof(float);
float* h_data = new float[num];
for(int i=0;i<num;i++) h_data[i] = i;

// 2.GPU分配显存
float* d_data = nullptr;
cudaMalloc(&d_data, bytes);

// 3.主机拷贝至显存
cudaMemcpy(d_data, h_data, bytes, cudaMemcpyHostToDevice);

// 4.启动核函数，GPU读取d_data并行计算
kernel<<<grid, block>>>(d_data);
```

### 传输特点

- 走 PCIe 总线传输，带宽几十 GB/s；
- 使用`cudaMallocHost`锁页内存可翻倍拷贝速度；
- 同步阻塞，拷贝完成后 CPU 才往下执行。

## 2. cudaMemcpyDeviceToHost：显存 → 主机（计算后取回结果）

### 使用场景

GPU 完成并行运算后，把计算结果传回 CPU，用于打印、存储、后续串行逻辑处理。

### 示例接续上面代码

cpp

运行

```
// 同步等待GPU核函数执行完毕
cudaDeviceSynchronize();

// 显存数据拷贝回CPU
cudaMemcpy(h_data, d_data, bytes, cudaMemcpyDeviceToHost);

// CPU读取结果打印
for(int i=0;i<10;i++){
    printf("%f ", h_data[i]);
}

// 释放资源
cudaFree(d_data);
delete[] h_data;
```

### 注意点

1. 必须确保核函数执行完成再拷贝，否则拷贝未计算完成的脏数据；
2. 拷贝大数组耗时高，优化思路：减少主机显存来回传输，尽量把计算放 GPU。

## 3. cudaMemcpyDeviceToDevice：显存 → 显存（GPU 内部数据迁移）

### 使用场景

完全不经过 CPU，两块显存地址之间直接拷贝数据：

- 显存内数据分片复制、矩阵分块缓存；
- 多卡场景单卡内数据迁移；
- 共享内存中转前显存数据预处理。

### 示例

cpp

运行

```
float *d_src, *d_dst;
size_t bytes = 1024 * sizeof(float);
cudaMalloc(&d_src, bytes);
cudaMalloc(&d_dst, bytes);

// 先上传数据到d_src
cudaMemcpy(d_src, h_data, bytes, cudaMemcpyHostToDevice);

// GPU内部显存互拷，不走CPU
cudaMemcpy(d_dst, d_src, bytes, cudaMemcpyDeviceToDevice);
```

### 核心优势

1. 仅在 GPU 片上总线传输，**带宽 TB/s 级别**，远快 PCIe；
2. 无 CPU 参与，不占用主机总线资源；

### 限制

仅支持**同一块 GPU**内的显存拷贝；多 GPU 之间拷贝不能用该枚举，需要专用多卡 API。

------

# 三、综合完整标准 Demo（融合三大 API + 两类核心拷贝）

cpp

运行

```
#include <iostream>
#include "cuda_runtime.h"
#include "device_launch_parameters.h"

__global__ void addKernel(float* d_in)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    d_in[idx] += 1.0f;
}

int main()
{
    const int N = 256;
    size_t byteSize = N * sizeof(float);

    // 1.主机内存分配
    float* h_data = new float[N]{};
    for (int i = 0; i < N; i++)
        h_data[i] = (float)i;

    // 2.显存分配 cudaMalloc
    float* d_data = nullptr;
    cudaMalloc(&d_data, byteSize);

    // 3.主机→显存拷贝 HostToDevice
    cudaMemcpy(d_data, h_data, byteSize, cudaMemcpyHostToDevice);

    // 启动GPU核函数计算
    addKernel<<<1, N>>>(d_data);
    cudaDeviceSynchronize();

    // 4.显存→主机拷贝 DeviceToHost
    cudaMemcpy(h_data, d_data, byteSize, cudaMemcpyDeviceToHost);

    // CPU输出结果
    std::cout << h_data[0] << " " << h_data[1] << std::endl;

    // 5.释放显存 cudaFree
    cudaFree(d_data);
    delete[] h_data;
    return 0;
}
```

# 四、核心总结

1. `cudaMalloc` 开辟 GPU 显存，`cudaFree` 释放显存，成对使用；
2. `cudaMemcpy` 依靠第四个参数区分传输方向，是 CPU/GPU 数据交互唯一通道；
3. 三类拷贝适用场景区分：
   - HostToDevice：计算前输入上传；
   - DeviceToHost：计算后结果下载；
   - DeviceToDevice：GPU 内部数据复制，速度最快，不占用 PCIe；
4. 主机普通内存与显存地址隔离，**绝对不能直接赋值、直接访问**，必须依靠拷贝 API 完成数据交互。