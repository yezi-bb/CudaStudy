# CUDA 本周全部基础知识点复盘 + 思维导图结构化整理

## 一、整体知识框架（思维导图总根）

```
CUDA基础开发
├─ 1. 编译与工程基础
├─ 2. 三类代码修饰符（__global__ / __device__ / __host__）
├─ 3. 线程层级：Grid / Block / Thread / SM / Warp
├─ 4. 核心内存API（增删改查）
├─ 5. 数据拷贝三大方向
├─ 6. 核函数调用语法与线程索引计算
├─ 7. 同步机制 cudaDeviceSynchronize
└─ 8. 核函数报错全套排查流程
```

# 二、分模块思维导图

## 模块 1：工程 & 编译基础

```
1. CUDA工程配置
├─ 文件后缀：.cu（nvcc编译） .cpp（MSVC编译）
├─ 执行配置语法 <<<>>>：MSVC标红波浪，仅nvcc识别
├─ 算力配置（RTX4060）
│  └─ 代码生成填写：compute_89,sm_89
├─ 历史算力坑：compute_52,sm_52 仅CUDA11支持，12.9直接报错
└─ 编译报错诱因
   ├─ MSVC14.44高版本与CUDA12.9不兼容
   └─ .cu文件项类型未设置为NVIDIA CUDA C/C++
```

## 模块 2：三大函数修饰符（Host/Device 代码分离）

plaintext

```
2. 函数限定符
├─ __global__ 核函数 Kernel
│  ├─ 运行位置：GPU
│  ├─ 调用位置：CPU主机
│  ├─ 返回值：必须void
│  ├─ 调用语法：func<<<grid,block>>(args)
│  └─ 内部可调用：__device__，不能调用__host__
├─ __device__ 设备函数
│  ├─ 运行：GPU
│  ├─ 调用方：__global__ / 其他__device__
│  └─ 支持return返回值，CPU无法直接调用
├─ __host__ 主机函数
│  ├─ 运行：CPU，普通C++函数默认自带
│  └─ GPU内不可调用
└─ __host__ __device__ 双端函数
   └─ 同时生成CPU/GPU两套代码，两端均可调用
```

## 模块 3：硬件层级：SM / Block / Warp / Thread（核心底层）

plaintext

```
3. GPU硬件调度层级（从大到小）
GPU芯片 → SM流多处理器 → Block线程块 → Warp调度组 → Thread线程
├─ SM（流多处理器，物理硬件）
│  ├─ 独立资源：寄存器、共享内存、运算单元、Warp调度器
│  ├─ 规则：一个Block只能完整放在单个SM，不可跨SM拆分
│  └─ 性能关键：Block越小，单SM可容纳并发Block越多，延迟隐藏越强
├─ Block（软件线程分组，程序员可控）
│  ├─ 硬件硬性限制：单Block最大1024线程
│  ├─ 推荐取值：128 / 256（32倍数，均衡性能）
│  ├─ 块内特性：可使用__shared__、__syncthreads()同步
│  └─ Block之间：无共享内存、无法互相同步、完全隔离
├─ Warp（硬件最小调度单元，固定32线程）
│  ├─ 硬件自动切分Block，程序员无法修改大小
│  ├─ SIMT机制：同一Warp32线程同时执行一条指令
│  ├─ Warp分化：if/else分支导致分批执行，性能暴跌
│  └─ 性能原理：多Warp切换，掩盖显存访问长延迟
└─ Thread 单线程
   └─ 最小执行单元，拥有私有寄存器
```

## 模块 4：内存核心 API（增删改查全套）

plaintext

```
4. CUDA内存管理API
├─ 显存分配【增】cudaMalloc
│  ├─ 原型：cudaError_t cudaMalloc(void** devPtr, size_t size)
│  ├─ 作用：GPU全局显存开辟空间
│  └─ 注意：GPU地址CPU不能直接解引用
├─ 显存释放【删】cudaFree
│  ├─ 参数：cudaMalloc得到的显存指针
│  └─ 规范：分配释放成对，防止显存泄漏
├─ 数据拷贝【改/查】cudaMemcpy
│  └─ 第四个参数区分三大拷贝方向（见模块5）
└─ 辅助锁页内存API（拓展）
   ├─ cudaMallocHost：主机锁页内存，提升拷贝带宽
   └─ cudaFreeHost：释放锁页内存
```

## 模块 5：cudaMemcpy 三大拷贝方向

plaintext

```
5. 三类内存传输方向 cudaMemcpyKind
├─ cudaMemcpyHostToDevice 主机→显存
│  └─ 场景：计算前上传输入数据
├─ cudaMemcpyDeviceToHost 显存→主机
│  └─ 场景：计算完成取回结果校验、打印
├─ cudaMemcpyDeviceToDevice 显存→显存
│  ├─ GPU内部传输，不经过PCIe，速度极快
│  └─ 限制：仅同一块GPU内显存互拷
└─ 特性：普通cudaMemcpy是同步阻塞API，无需额外同步
```

## 模块 6：核函数启动 + 线程索引计算（本周高频易错点）

plaintext

```
6. Kernel启动与一维线程索引
├─ 启动语法 func<<<gridSize, blockSize>>>(params)
│  ├─ gridSize：Grid内Block总数量
│  └─ blockSize：单个Block内线程数量，≤1024
├─ 两种启动方案
│  ├─ 方案1：单Block <<<1,N>>> 仅N≤1024可用
│  │  └─ 索引简化：idx = threadIdx.x；大数据需线程内for循环步进
│  └─ 方案2：多Block标准写法（工程通用）
│     ├─ int gridSize = (N + blockSize - 1) / blockSize; //向上取整
│     └─ 优势：并行度拉满，充分利用GPU算力
├─ 全局线程ID标准公式（多Block必用，不可简写）
│  └─ int idx = blockIdx.x * blockDim.x + threadIdx.x;
├─ 易错坑：只写 idx = blockIdx.x + threadIdx.x → 下标重复覆盖数据
└─ 边界保护判断（必加）
   └─ if(idx >= N) return; 防止数组越界报错
```

## 模块 7：同步函数 cudaDeviceSynchronize

plaintext

```
7. 同步API cudaDeviceSynchronize
├─ 作用1：CPU阻塞等待GPU所有任务全部完成
│  └─ 使用场景：Kernel跑完再拷贝数据回CPU，避免脏数据
├─ 作用2：捕获核函数运行时崩溃报错
│  └─ Kernel异步提交，越界/空指针错误仅同步时抛出
├─ 同类同步对比
│  ├─ cudaDeviceSynchronize：全局设备同步，开销大，调试常用
│  └─ cudaStreamSynchronize：单流同步，高性能程序推荐
└─ 注意：频繁全局同步会降低CPU/GPU并行重叠效率
```

## 模块 8：核函数报错完整排查流程

plaintext

```
8. Kernel报错排查流程
├─ 步骤1：全局错误检测宏全覆盖
│  ├─ cudaMalloc / cudaMemcpy 后校验
│  ├─ Kernel调用后：cudaGetLastError() 检测启动错误
│  └─ cudaDeviceSynchronize() 同步捕获运行崩溃
├─ 步骤2：区分两类报错
│  ├─ 启动错误：invalid configuration argument
│  │  └─ 诱因：blockSize>1024、算力不匹配、Grid超限
│  └─ 运行错误：illegal memory access 非法内存访问（最高频）
│     └─ 诱因：索引越界、CPU指针传入GPU、空指针、无边界判断
├─ 步骤3：线程索引校验
│  └─ 核对全局ID公式，确认存在if(idx>=N)判断
├─ 步骤4：工程配置排查
│  └─ .cu文件、算力配置、MSVC编译器版本兼容问题
└─ 步骤5：二分调试
   └─ 缩小数据量、注释核函数分段代码定位出错行
```

# 三、本周核心易错点汇总（复盘重点）

1. `idx = blockIdx.x + threadIdx.x` 错误，必须乘 blockDim.x；
2. blockSize >1024 硬件直接限制，无法启动核函数；
3. compute_52,sm_52 在 CUDA12.9 完全失效，4060 只能填 compute_89,sm_89；
4. Kernel 调用异步，不加 `cudaDeviceSynchronize` 直接拷贝会读取未计算数据；
5. 单 Block<<<1,64>>> 总线程太少，GPU 算力闲置，速度极慢；
6. Warp 分化：if/else 同一 Warp 分支不同，性能大幅下降；
7. 忘记判断 `if(idx >= N)` 造成显存越界崩溃。