# Week04 / Day02 — 学习记录（源码填充版）

> 主题：shared-memory tile transpose（含 bank conflict padding）。

## 1. 今日目标（回顾）
实现经典 tile transpose kernel，与 CPU 逐点一致；能解释为什么 `TILE+1` padding。

## 2. 前置事实
- 输入在全局内存：`src[lines][depth]` 行主序 float（lines=1000，depth=1025 after FFT 或裁剪前的全深度）。
- 输出：`dst[depth][lines]`（裁剪在 host 侧 `start/end` 控制拷贝范围，或 kernel 内偏移）。
- `BLOCK_DIM=256`（DLL include 常量）；转置 tile 常用 `16×16`/`32×32`。

## 3. Kernel（参考）

```cpp
#define TILE 16                       // 或 32
__global__ void transposeTileKernel(const float* __restrict__ src,
                                    float* __restrict__ dst,
                                    int rows /*lines*/, int cols /*depth*/) {
  __shared__ float tile[TILE][TILE + 1];          // padding 防 bank conflict
  int x = blockIdx.x*TILE + threadIdx.x;          // col
  int y = blockIdx.y*TILE + threadIdx.y;          // row
  if (x < cols && y < rows)
    tile[threadIdx.y][threadIdx.x] = src[y*cols + x];   // 合并读：同行 warp 连续 x
  __syncthreads();
  int xt = blockIdx.y*TILE + threadIdx.x;         // 转置后的目标坐标
  int yt = blockIdx.x*TILE + threadIdx.y;
  if (xt < rows && yt < cols)
    dst[yt*rows + xt] = tile[threadIdx.x][threadIdx.y]; // 合并写
}
```
Launch：`grid=(ceil(cols/16), ceil(rows/16))`、`block=(16,16)`。注意 dst 是 `[cols][rows]` 布局 → `dst[yt*rows+xt]`。

## 4. Bank conflict 与 padding（Day02 必答）
- 共享内存按 **32 bank × 4B** 组织，一个 warp 同时访问的 32 个 4B 地址若落在同一 bank 的不同行 → 冲突串行化（最坏 32 路）。
- 写 tile 时 `threadIdx.y` 行固定、`threadIdx.x` 变化 → 无冲突；
- **读回 tile 转置时**：`tile[threadIdx.x][threadIdx.y]`，warp 内 `threadIdx.x` 相同但变化在 `threadIdx.y` → 访问同一行不同列 = 都命中**同一 bank 组**（跨行同列）→ 32 路冲突！
- 解决：`tile[TILE][TILE+1]`（每行 +1 个 float 偏移）→ 行间错开 1 bank，转置读回时每线程落不同 bank，冲突降为 0（理想）。
- 代价：1/17 的共享内存浪费（16→17），可接受。

## 5. 验证与记录
- 与 CPU 版 diff（全量 1000×1025 与裁剪版两种）：`maxRel = ______`
- 计时：naive 全局读版 vs tile 版 vs tile+padding 版（各 `___ ms`），用 ncu `l1tex__data_bank_conflicts_pipe_lsu_mem_shared_op_ld.sum` 观察冲突数。
- 当 rows/cols 不是 TILE 倍数：边界判断已含（越界跳过）。

## 6. 自测 Q&A
1. 为什么先读共享内存再写回？→ 全局内存转置=读写都是非合并（若直接全局交换每线程对角），先 tile 到 smem 再转置写出使两边都合并。
2. 为何 __syncthreads() 必不可少？→ 相邻 block 无关，但**同一 block 内**必须等全 tile 写完后才能转置读，否则读到脏数据。
3. dst 布局为什么是 yt*rows+xt？→ 输出深度在行（每行一条 A-scan），行数=rows(线数)，列=cols(深度) → 索引 `col*rows+row`。
4. 若不 padding 会怎样？→ 写阶段没问题，转置读回 32 路冲突，LSU 停顿明显（实测可对比）。
5. 裁剪与转置怎么合一？→ kernel 只转置；裁剪=输出端 host `dst[d-start]` 或 kernel 内 `if(d>=start&&d<end)` 再写，任选。

## 7. DoD 打卡
- [ ] GPU 与 CPU 一致（§5 diff 通过）
- [ ] 笔记含 padding 原因（§4）

## 明日预告
DSC 参数精读与极→直公式。
