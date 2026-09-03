# 白板 01 — Tile Transpose（40 min）

## 题目（面试口吻）
> 「我们的 OCT 管线在 FFT/Log 之后要把 A-line 缓冲从 `[帧内线数 × 深度]` 翻成 `[深度 × 线数]` 再切顶，才能送 DSC。你写一版 CUDA transpose，先给我朴素版，再优化成 tile 版，并解释 bank conflict。行主序，float。」

- 输入 `in[M][N]`（M=每帧 A 线数，N=深采样数），行主序；
- 输出 `out[N][M]`；请口述你如何画这块内存（先画图再写码）。

## 参考答案

```cuda
#define TS 32

// 版本 1：朴素 —— 可讲对，但跨步读全局 = 慢
__global__ void transpose_naive(const float* __restrict__ in,
                                float* __restrict__ out,
                                int M, int N) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;   // in 行（M）
    int y = blockIdx.y * blockDim.y + threadIdx.y;   // in 列（N）
    if (x < M && y < N)
        out[y * M + x] = in[x * N + y];              // 读合并写不合并
}

// 版本 2：tile —— 读一块、写一块，读写都尽量合并
__global__ void transpose_tile(const float* __restrict__ in,
                               float* __restrict__ out,
                               int M, int N) {
    // +1 列 padding：让 32 列错开不同 bank，避免写回时冲突
    __shared__ float tile[TS][TS + 1];

    int x = blockIdx.x * TS + threadIdx.x;   // in 行
    int y = blockIdx.y * TS + threadIdx.y;   // in 列
    if (x < M && y < N)
        tile[threadIdx.y][threadIdx.x] = in[x * N + y];   // 行主序读：合并
    __syncthreads();                         // 块内必须同步：tile 全写完才可读

    int xi = blockIdx.y * TS + threadIdx.x;  // 目标行来自原列块
    int yi = blockIdx.x * TS + threadIdx.y;  // 目标列来自原行块
    if (xi < N && yi < M)
        out[xi * M + yi] = tile[threadIdx.x][threadIdx.y]; // 写也按连续 xi 合并
}
// 启动：<<<dim3(ceil(N/TS), ceil(M/TS)), dim3(TS, TS)>>>
//      注意 out 维度是 [N][M]，所以 x 网格数要按 N 算、y 网格数按 M 算。
```

## 易错点 / 检查单
- [ ] **块索引和输出维度的对应**：`out` 是 `[N][M]`，blockIdx.x 该跑 N 方向——最常见翻车点；
- [ ] 边界：`M,N` 不是 32 倍数时两处 `if` 都不可省（本例 497 / 线数都不是 32 倍数）；
- [ ] `__syncthreads()` 位置：读回前必须同步；shared 声明 `[TS][TS+1]` 说明为什么 padding；
- [ ] 口述替代方案：块内对角交换（把共享数组下标交换一次）也能去 bank 冲突。

## 口述词（出声练）
「朴素版每个 warp 读 32 个连续 float 是合并的，但写出去跨 M 的大步长，等于每 32 次才碰一次相邻地址；反过来也一样。tile 版把一个 32×32 子块搬进 shared，再以转置后的坐标读回并写出——此时全局读写各自连续，代价是 block 内一次同步。shared 行宽 33 而不是 32，让相邻行错开 bank；否则第 0 列 32 行全部落同一 bank，32 路冲突。」

## 落点
OCTCudaProject/OCTCudaCmake/src/kernels/transpose_tile.cu（含 host 启动 + 与 CPU 转置断言 diff=0）。
回链笔记：`Week04/Day02`（链 A Transpose+Cut 语义与尺寸）。
