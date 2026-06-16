# 一、CUDA 三类函数修饰符：**global** / **device** / **host**

## 1. 修饰符核心定义与执行位置

CUDA 通过限定符区分代码运行在 CPU（Host）还是 GPU（Device），三者作用域、调用方完全隔离。

### 1.1 `__global__` 全局核函数（Kernel）

1. **运行位置**：GPU 设备端
2. **调用位置**：只能在 Host（CPU）代码中调用
3. **调用语法**：`kernel<<<Grid维度, Block维度>>>(参数);`
4. 特性
   - 无返回值，只能用指针 / 显存数组输出结果；
   - 是 CPU 启动 GPU 并行计算的唯一入口；
   - 函数内部可调用 `__device__` 函数，**不能调用 \**host\** 函数**。

cpp

运行

```
// 核函数：GPU执行，CPU调用
__global__ void vecAdd(float* d_a, float* d_b, float* d_out)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    d_out[idx] = d_a[idx] + d_b[idx];
}
```

### 1.2 `__device__` 设备函数

1. **运行位置**：GPU 设备端
2. **调用位置**：只能被 `__global__` / 其他 `__device__` 函数调用
3. 特性
   - 支持返回值，普通函数写法；
   - 仅 GPU 内部可见，CPU 无法直接调用；
   - 多用于封装 GPU 内重复计算逻辑。

cp

运行

```
__device__ float square(float x)
{
    return x * x;
}
```

### 1.3 `__host__` 主机函数

1. **运行位置**：CPU 主机端
2. **调用位置**：仅 CPU 代码调用
3. 特性
   - 就是普通 C++ 函数，默认不加修饰符等价于`__host__`；
   - GPU 内无法调用。

cpp

运行

```
__host__ void printArr(float* h_data, int n)
{
    for(int i=0;i<n;i++) printf("%f ", h_data[i]);
}
```

### 1.4 混合修饰 `__host__ __device__`

函数同时编译两套版本：一份 CPU 执行、一份 GPU 执行；

CPU/GPU 都能调用，适合通用数学工具函数。

cpp

运行

```
__host__ __device__ float add(float a, float b)
{
    return a + b;
}
```

## 修饰符对照表

表格

|        限定符         | 运行硬件 |         允许谁调用          |  返回值  |
| :-------------------: | :------: | :-------------------------: | :------: |
|     `__global__`      |   GPU    |          CPU Host           |   void   |
|     `__device__`      |   GPU    | `__global__` / `__device__` | 任意类型 |
|      `__host__`       |   CPU    |          CPU Host           | 任意类型 |
| `__host__ __device__` | CPU+GPU  |        CPU、GPU 均可        | 任意类型 |

## 核心禁忌

1. CPU 不能直接调用 `__device__`；
2. GPU 核函数内不能调用 `__host__`；
3. `__global__` 必须 void，不能 return 数值。

------

# 二、一维 Grid / Block 线程基础逻辑

## 1. 三层线程层级（从大到小）

Grid（网格） → Block（线程块） → Thread（线程）

一维场景下只有 `.x` 维度，无 y/z。

### 关键内置变量（GPU 核函数内直接使用）

1. `blockIdx.x`：当前线程所在**块编号**（块索引）
2. `blockDim.x`：每个 Block 包含的**线程总数**（块大小）
3. `threadIdx.x`：当前线程在 Block 内部的**线程编号**

### 全局唯一线程 ID 公式（一维标准）

cpp

运行

```
int globalIdx = blockIdx.x * blockDim.x + threadIdx.x;
```

- 作用：把二维的 (块号，块内线程号) 映射成一维数组下标；
- 所有线程的 `globalIdx` 连续不重复，对应数组 0,1,2,3...

## 2. 启动核函数语法一维拆解

cpp

运行

```
kernel<<<gridSize, blockSize>>>(params);
```

- 第一个参数 `gridSize` = Grid 包含多少个 Block（块总数）
- 第二个参数 `blockSize` = 每个 Block 内多少个 Thread（单块线程数）

示例：

cpp

运行

```
// 启动 4个Block，每个Block 64个线程，总线程数 = 4 * 64 = 256
vecAdd<<<4, 64>>>(d_a, d_b, d_out);
```

此时：

- blockIdx.x 取值：0、1、2、3
- threadIdx.x 取值：0~63
- globalIdx 范围：0 ~ 255

## 3. 执行调度逻辑

1. CPU 调用`<<<>>>`，把 Grid 所有 Block 批量提交给 GPU；
2. GPU 硬件 SM 多处理器自动分配 Block 并行执行；
3. 每个 Block 内部的 32 个线程打包为一个 Warp 调度；
4. 所有线程同步执行同一段核函数代码（单指令多线程 SIMT）。

## 4. 边界判断（防止数组越界）

总数据量 N 不一定刚好整除 `gridSize * blockSize`，超出有效数据的线程要直接 return：

cpp

运行

```
__global__ void vecAdd(float* d_a, float* d_b, float* out, int N)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if(idx >= N) return; // 超出数组范围，直接退出
    out[idx] = d_a[idx] + d_b[idx];
}
```

## 5. 完整一维示例 Demo

cpp

运行

```
#include <iostream>
#include "cuda_runtime.h"
#include "device_launch_parameters.h"

// 设备函数：GPU内部调用
__device__ float square(float x)
{
    return x * x;
}

// 核函数 __global__，CPU调用，GPU执行
__global__ void calcSquare(float* in, float* out, int dataNum)
{
    // 一维全局线程ID
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= dataNum) return;

    float val = in[idx];
    out[idx] = square(val); // 调用__device__函数
}

// 主机函数，仅CPU运行
__host__ void checkResult(float* h_out, int n)
{
    for (int i = 0; i < n; i++)
        printf("%f ", h_out[i]);
}

int main()
{
    const int N = 256;
    size_t bytes = N * sizeof(float);

    // 主机内存
    float* h_in = new float[N];
    float* h_out = new float[N]{};
    for (int i = 0; i < N; i++) h_in[i] = (float)i;

    // 显存分配
    float *d_in, *d_out;
    cudaMalloc(&d_in, bytes);
    cudaMalloc(&d_out, bytes);

    // 上传数据
    cudaMemcpy(d_in, h_in, bytes, cudaMemcpyHostToDevice);

    // 一维启动配置：每块64线程，一共4块，总线程4*64=256
    dim3 blockSize(64);
    dim3 gridSize(4);
    calcSquare<<<gridSize, blockSize>>>(d_in, d_out, N);
    cudaDeviceSynchronize();

    // 取回结果
    cudaMemcpy(h_out, d_out, bytes, cudaMemcpyDeviceToHost);

    // CPU主机函数打印
    checkResult(h_out, 10);

    // 释放资源
    cudaFree(d_in);
    cudaFree(d_out);
    delete[] h_in;
    delete[] h_out;
    return 0;
}
```

## 总结

1. 修饰符区分 CPU/GPU 代码：`__global__`是 CPU 启动 GPU 并行的入口；`__device__`是 GPU 内部工具函数；`__host__`普通 CPU 函数。
2. 一维线程三层结构：Grid (多块)→Block (单块线程组)→Thread (单个线程)；
3. 全局下标公式 `blockIdx.x * blockDim.x + threadIdx.x` 是一维并行计算核心；
4. 启动参数 `<<<grid块数, 单块线程数>>>` 控制总并行线程数量。