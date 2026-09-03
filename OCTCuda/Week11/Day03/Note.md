# Week11 / Day03 — 学习记录（源码填充版）

> 主题：CUDA μ kernel 骨架（ipa_mu.cu）——一 A-line 一 block，块内滑动拟合，小卷 GPU≈CPU。

## 1. 今日目标（回顾）
把 cpu_aline_mu 翻译成 kernel：shared memory 载入该线 depth 段；块内并行做对数窗统计/归约；写 μ 体；与 CPU 对比数值一致。

## 2. 并行策略（公开设计，产品内核不可见）
- **网格**：每 (frame×theta) 一条 A-line 一个 block → blockIdx.x = aline；
- **块内**：D=depth(1025) 个样本，由 kThreads(256) 线程分块处理：
  1. 全部线程协作把该线 logI 载入 `__shared__ float sLine[1025]`；
  2. 块内对“滑动窗集合”做归约式拟合太贵 → 折中：**每窗一个 warp/线程组**，各线程算 1-2 个深度样本的部分和，warp 归约得窗斜率；
  3. 写 `mu_vol[aline*depth+z]` 与 `line_mu[aline]`（用 lane 0 原子/单独归约）。
- 说明：真实实现窗口调度（stepsucc/fail 串行推进）有数据依赖，教学版用**每 z 固定窗**先验证并行正确性，串行调度留作优化项。

## 3. 骨架（落点 OCTCudaProject/oct/Ipa/ipa_mu.cu）
```cuda
#define BLOCK_DIM 256
__device__ inline float d_log1p(float v){ return logf(1.f + v); }

__global__ void ipa_mu_kernel(const float* __restrict__ logI,
                              const int*    __restrict__ lumen_b,
                              const int*    __restrict__ labels,
                              float* __restrict__ mu_vol,
                              float* __restrict__ line_mu,
                              int depth, int media_off, int minwin, float noise_lv)
{
    const int aline = blockIdx.x;                       // 一 block 一 A-line
    const int tid   = threadIdx.x;
    extern __shared__ float sLine[];
    // 1) 整线载入 shared（可再 log-预处理由上游做，这里假定已是 logI）
    for (int i = tid; i < depth; i += BLOCK_DIM) sLine[i] = logI[(size_t)aline*depth + i];
    __syncthreads();
    if (labels[aline] == 0) { if (tid==0) line_mu[aline] = 0.f; return; }
    const int lb = lumen_b[aline];
    const int zE = min(lb + media_off, depth);
    // 2) 每个线程组处理一个滑动窗起点 z = lb+1 + tid*kStep (固定窗简化)
    //    做 最小二乘斜率 的部分和（每线程累加 x,y,xx,xy）
    __shared__ float sh_sum[BLOCK_DIM][4];
    float sx=0,sy=0,sxx=0,sxy=0;
    for (int z = lb + 1 + tid*minwin; z + minwin <= zE; z += BLOCK_DIM*minwin) {
        sx=sy=sxx=sxy=0;
        for (int i=0;i<minwin;++i){ float x=i, y=sLine[z+i];
            sx+=x; sy+=y; sxx+=x*x; sxy+=x*y; }
        sh_sum[tid][0]=sx; sh_sum[tid][1]=sy; sh_sum[tid][2]=sxx; sh_sum[tid][3]=sxy;
        __syncthreads();
        // 3) 块内树形归约 → 得斜率 → lane0 铺 μ（简版：整窗写 μ）
        for (int s = BLOCK_DIM/2; s > 0; s >>= 1) {
            if (tid < s) { for(int k=0;k<4;++k) sh_sum[tid][k]+=sh_sum[tid+s][k]; }
            __syncthreads();
        }
        if (tid == 0) {
            double n=minwin, denom = n*sh_sum[0][2]-sh_sum[0][0]*sh_sum[0][0];
            float slope = fabs(denom)<1e-9?0.f:(float)((n*sh_sum[0][3]-sh_sum[0][0]*sh_sum[0][1])/denom);
            if (slope < 0.f) { float mu=-slope;
                for (int i2=z;i2<z+minwin && i2<zE;++i2) mu_vol[(size_t)aline*depth+i2]=mu; }
        }
        __syncthreads();
    }
    // 4) line_mu = 体数据的简单归约代表（warp reduce 由 CPU 参考）
    if (tid == 0) line_mu[aline] = /*参考值: 均值或中位数占位*/ 0.f;
}
```
调用方：`ipa_mu_kernel<<<frames*theta, BLOCK_DIM, depth*sizeof(float)>>>(...)`。

## 4. 与 CPU 对比
- 小卷（F=3,θ=64,D=1025）跑 cpu_volume_mu 与 kernel；
- 断言：非掩膜线的 mu_vol 有效深度样本 **均方根差 < 1e-4**（同样固定窗策略时）；
- 时间比：CPU 全卷 ~分钟级 → kernel 毫秒级（报加速比与 kernel 时间）。
> 注意：固定窗简化与 CPU 的滑窗推进不同时，对比前提是把两边都改成同一窗口策略，先把“并行实现正确性”与“调度策略”解耦（产品内部策略不可见）。

## 5. DoD 打卡
- [ ] ipa_mu.cu 编译通过，小卷 GPU≈CPU（<1e-4）
- [ ] 已记录 CPU vs GPU 耗时对照

## 明日预告
μ 方图 → 圆图：复用 DSC 完成 All_Aline_Mu_Data_To_Image 等价出图。
