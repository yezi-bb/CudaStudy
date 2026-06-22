# 一、dim3 二维 Grid / Block 基础定义

## 1. dim3 类型说明

`dim3` 是 CUDA 内置结构体，专门描述三维尺寸（x/y/z），默认 z=1；

二维场景只用到 `.x`、`.y`，z 自动为 1，不影响计算。

结构体原型简化：

cpp

运行

```
struct dim3
{
    unsigned int x, y, z;
    dim3(unsigned int x_ = 1, unsigned int y_ = 1, unsigned int z_ = 1)
        : x(x_), y(y_), z(z_) {}
};
```

## 2. 二维 Block、Grid 标准定义（图像场景）

假设图像尺寸：宽 `width`（横向 X）、高 `height`（纵向 Y）

### 步骤 1：定义单块二维线程尺寸（推荐 32×32，完美对齐 Warp）

cpp

运行

```
// 每个Block：横向32线程，纵向32线程，单块总线程 32*32=1024（硬件上限）
dim3 blockSize(32, 32);
```

### 步骤 2：计算 Grid 二维块数量（向上取整，覆盖整张图所有像素）

cpp

运行

```
// 横向需要多少块 = 图像宽度 / 单块宽度
unsigned int gridX = (width + blockSize.x - 1) / blockSize.x;
// 纵向需要多少块 = 图像高度 / 单块高度
unsigned int gridY = (height + blockSize.y - 1) / blockSize.y;
dim3 gridSize(gridX, gridY);
```

### 步骤 3：二维核函数启动语法

cpp

运行

```
ImageKernel<<<gridSize, blockSize>>>(d_img, width, height);
```

### 内置二维线程变量（核函数内直接使用）

表格

|     变量      |               含义                |
| :-----------: | :-------------------------------: |
| `threadIdx.x` | 线程在当前 Block 内的横向局部坐标 |
| `threadIdx.y` | 线程在当前 Block 内的纵向局部坐标 |
| `blockIdx.x`  | 当前 Block 在 Grid 里的横向块编号 |
| `blockIdx.y`  | 当前 Block 在 Grid 里的纵向块编号 |
| `blockDim.x`  |      每个 Block 横向总线程数      |
| `blockDim.y`  |      每个 Block 纵向总线程数      |

------

# 二、二维线程 → 图像像素坐标映射公式（核心）

## 1. 像素二维坐标 (px, py)

cpp

运行

```
// 当前线程对应的像素 X（横向列）
unsigned int px = blockIdx.x * blockDim.x + threadIdx.x;
// 当前线程对应的像素 Y（纵向行）
unsigned int py = blockIdx.y * blockDim.y + threadIdx.y;
```

- `px`：图像列号，范围 `0 ~ width-1`
- `py`：图像行号，范围 `0 ~ height-1`

## 2. 一维展平下标（图像数组存储通用，显存是一维连续数组）

图像存储规则：**行优先**，一行像素连续存放，下一行接在后面

cpp

运行

```
// 一维全局数组索引，用来读写 d_img[ idx ]
unsigned int pixelIdx = py * width + px;
```

## 3. 边界判断（必加，防止越界）

Grid 总线程会大于等于像素总数，边缘多余线程直接退出：

cpp

运行

```
if (px >= width || py >= height)
    return;
```

------

# 三、完整二维图像核函数 Demo

cpp

运行

```
#include "cuda_runtime.h"
#include "device_launch_parameters.h"

// 图像灰度处理核函数：每个线程处理1个像素
__global__ void GrayKernel(unsigned char* d_img, int width, int height)
{
    // 1. 计算当前线程对应的像素二维坐标
    unsigned int px = blockIdx.x * blockDim.x + threadIdx.x;
    unsigned int py = blockIdx.y * blockDim.y + threadIdx.y;

    // 2. 边界保护，超出图像范围直接返回
    if (px >= width || py >= height)
        return;

    // 3. 转为一维数组下标
    unsigned int idx = py * width + px;

    // 示例逻辑：像素值取反
    d_img[idx] = 255 - d_img[idx];
}

int main()
{
    const int width  = 640;
    const int height = 480;
    size_t imgBytes = width * height * sizeof(unsigned char);

    // 1. 定义二维 Block、Grid
    dim3 block(32, 32);
    dim3 grid(
        (width  + block.x - 1) / block.x,
        (height + block.y - 1) / block.y
    );

    // 显存分配、数据上传省略...

    // 启动二维网格核函数
    GrayKernel<<<grid, block>>>(d_img, width, height);
    cudaDeviceSynchronize();

    // 结果拷贝回CPU省略...
    return 0;
}
```

------

# 四、关键细节补充

## 1. 为什么推荐 block (32,32)

单个 Block 总线程 = 32×32 = 1024，刚好硬件单 Block 线程上限；

每行 32 个线程完美对齐 Warp（Warp 固定 32 线程），无硬件资源浪费。

## 2. 易错点区分

1. 不要搞反宽高：`blockIdx.x` 对应图像宽度（横向），`blockIdx.y` 对应高度（纵向）；
2. 一维展平公式 `py * width + px`，**乘 width 不是 height**；
3. 二维 Grid 不存在下标重复问题，公式 `blockIdx * blockDim + threadIdx` 对 x、y 维度独立生效。

## 3. 简化场景：单 Block 二维（仅小图 ≤32×32）

启动 `<<<dim3(1,1), dim3(width,height)>>>`

此时 `blockIdx.x=0, blockIdx.y=0`，坐标可简写：

cpp

运行

```
unsigned int px = threadIdx.x;
unsigned int py = threadIdx.y;
```

## 4. 性能优势

二维线程天然贴合图像二维数据结构，不需要一维线程手动分行循环，逻辑直观；SM 调度二维 Block 时缓存局部相邻像素，访存局部性更好。