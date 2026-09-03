# 白板 02 — Reduction（35 min）

## 题目（面试口吻）
> 「批量回拉里我要对每条 A-line 的深度序列（~1000+ 个 float）求统计量（比如窗底噪均值）来归一化。你写一个 CUDA 归约 kernel，把一整卷 `n` 个 float 的和归约到单个输出。要块间也能并起来。注意解释 warp shuffle。」

- 输入 `in[n]`，float，行主序一维；输出 `out[0] += 总和`（out 先由 host 清零）。
- 提示可自选分块策略（每线程多元素更优——**口述时主动说**）。

## 参考答案

```cuda
#define BLOCK 256

// 每线程 4 个元素的 grid-stride 读取 + warp shuffle + 块间 atomicAdd
__global__ void reduce_sum(const float* __restrict__ in,
                           float* __restrict__ out, int n) {
    int tid = threadIdx.x;
    int i   = blockIdx.x * (BLOCK * 4) + tid;   // 本线程第一元素

    float s = 0.f;
    #pragma unroll
    for (int k = 0; k < 4; ++k) {               // 每线程 4 元素：少启动、多 ILP
        int idx = i + k * BLOCK;
        if (idx < n) s += in[idx];
    }

    // —— 一级：warp 内 shuffle 归约（无需 shared）——
    for (int off = 16; off > 0; off >>= 1)
        s += __shfl_down_sync(0xffffffffu, s, off);

    // —— 二级：每 warp 一个代表值进 shared ——
    __shared__ float swarp[BLOCK / 32];         // = 8
    if ((tid & 31) == 0) swarp[tid >> 5] = s;
    __syncthreads();

    // —— 三级：单线程串起 warp 代表（块内总量很小，足够快）——
    if (tid == 0) {
        float v = 0.f;
        for (int k = 0; k < BLOCK / 32; ++k) v += swarp[k];
        atomicAdd(out, v);                      // 块间汇总：结果顺序无关
    }
}
// 启动：blocks = ceil(n / (BLOCK*4))；host 先 cudaMemset(out, 0, 4)。
```

## 易错点 / 检查单
- [ ] **shared 数组尺寸按 warp 数**：`BLOCK/32` 而不是 `BLOCK`；
- [ ] `__shfl_down_sync` 的第一个参数 `0xffffffffu` = 全 mask（完整 warp 才合法）；写错会 undefined；
- [ ] 每线程取 4 个元素时**步长用 `k*BLOCK` 跨线程交错**（grid-stride），不是连续 4 个（会撕裂合并访问）；
- [ ] host 必须先把 `out` 清零再启动（atomicAdd 从非 0 开始 = 错）；
- [ ] 精度：float 累加顺序敏感 → 和 CPU 比时用相对误差阈值（如 <1e-3）而不是 ==。

## 口述词（出声练）
「归约分三层。每线程先沿数组以跨线程步长累 4 个值，减少线程数和访存指令。然后 warp 内用 shuffle_down 把 32 个部分和两两合并，5 步就归成一个数，完全不用 shared、不占同步。接着每个 warp 往 shared 里写一个代表值，块内 8 个 warp 再串行加——块规模小时串行比再开一次同步树划算。最后块之间用 atomicAdd 汇总，因为浮点加法顺序无关、我们只求总和。」

## 落点
OCTCudaProject/OCTCudaCmake/src/kernels/reduce_aline.cu（统计每 A-line/每帧聚合量，链 B 与 IPA 通用）。
回链笔记：`Week11/Day02`（cpu_volume_mu 的归约语义）与 `Week04/Day03`（窗统计思路）。
