# 一、核函数调用语法 `kernel<<<grid, block>>>(args)` 完整讲解

## 1. 整体结构拆分

plaintext

```
函数名 <<< 网格尺寸, 块尺寸 >>> (普通参数列表)
squareKernel <<< gridSize, blockSize >>> (d_in, d_out, N);
```

`<<<>>>` 叫**执行配置符（Execution Configuration）**，是 nvcc 专属 C++ 扩展语法，标准 C++ 无此语法。

### 两段参数含义

1. ```
   <<<A , B>>>
   ```

   ：并行调度参数，控制创建多少线程、如何分组

   - A (gridSize)：Grid 包含多少个线程块 Block
   - B (blockSize)：每个 Block 内部有多少个线程 Thread

2. `(xxx)`：普通函数参数，传给 GPU 核函数做计算

## 2. 数值限制（硬件硬性规则）

- 单个 Block 最大线程数：**1024**
- blockSize 建议取 32 倍数（32/64/128/256，对齐 Warp 调度，性能最优）

### 示例 1：单块写法（仅适合数据量≤1024，新手 Demo）

cpp

运行

```
// 1个块，块内256个线程
squareKernel<<<1, 256>>>(d_in, d_out, N);
```

内部索引简化：`idx = threadIdx.x`

### 示例 2：多块通用写法（工程标准，支持海量数据）

cpp

运行

```
int blockSize = 256;
// 向上取整计算需要多少块，保证覆盖全部N个数据
int gridSize = (N + blockSize - 1) / blockSize;
squareKernel<<<gridSize, blockSize>>>(d_in, d_out, N);
```

## 3. 关键特性

1. 核函数调用是**异步**：CPU 提交线程任务后立刻往下执行，不等 GPU 计算；
2. 需要 `cudaDeviceSynchronize()` 等待 GPU 全部线程跑完，再拷贝数据回 CPU；
3. `__global__` 函数只能在 CPU 调用，GPU 内部无法互相调用核函数。

## 总结

1. 多 Block 场景索引必须：`blockIdx.x * blockDim.x + threadIdx.x`，只相加会下标重复出错；仅单 Block 可简写 `threadIdx.x`；
2. `<<<grid, block>>>` 是 CUDA 专属并行配置语法，分离「线程调度参数」和「计算业务参数」，分两层括号传参。