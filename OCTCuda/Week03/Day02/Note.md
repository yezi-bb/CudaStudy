# Week03 / Day02 — 学习记录（源码填充版）

> 主题：开源实现 FftLogStage —— cuFFT PlanMany + Exec + log_power kernel。

## 1. 今日目标（回顾）
用 `cufftPlanMany`（batch=线数）一次变换整帧，写功率/对数 kernel，与小 N CPU DFT/第三方 FFT 对照验证。

## 2. 数据布局
- 输入：windowed `float[Ls][N]`，每行一条 aline（连续 N 个 float）。
- cuFFT R2C：每行 N → N/2+1 复数；实部/虚部为 `cufftReal/cufftComplex`。
- 输出谱 buffer：`cufftComplex[Ls][N/2+1]`，行距 `N/2+1`。

## 3. PlanMany 配置（参考）

```cpp
int rank=1, n[1]={N}, istride=1, idist=N, inembed[1]={N};
int onembed[1]={N/2+1}, ostride=1, odist=N/2+1;
cufftHandle plan;
cufftPlanMany(&plan, rank, n, inembed, istride, idist,
              onembed, ostride, odist, CUFFT_R2C, /*batch=*/Ls);
// 每帧：cufftMemcpyAsync(输入到 cufftReal*) → cufftExecR2C(plan, in, out)
```

## 4. power/log kernel（参考）

```cpp
// in  = cufftComplex[Ls][N/2+1]; out_f32 = power[Ls][N/2+1]（可直接叠加 log）
__global__ void powerLogKernel(const cufftComplex* __restrict__ in,
                               float* __restrict__ out, int half, float times) {
  int i = blockIdx.x*blockDim.x + threadIdx.x; int total = gridDim... /*由调用方定*/
  int k = i % half; int l = i / half;
  float re=in[i].x, im=in[i].y;
  float p = re*re + im*im;                 // 功率
  p = logf(p + 1e-12f);                    // log 压缩（去底后更稳）
  out[i] = p * times;                      // 缩放位：产品端 times 语义（见 Day01）
}
```

> 注：产品端把“FFT→Log 求和”放进**一个 DLL API**；开源端可分解为 `Exec(plan)+powerLogKernel`，契约等价即可（验收按“插值 U16 与产品显示一致/逐点 golden”）。log 前加 `1e-12` 避免 log0；若产品是幅值 log，则把 `p` 改为 `sqrtf(p)` 后 log——**用真实谱与显示效果校准**，两条都留。

## 5. 验证：小 N 对照
- 选 `N=256, Ls=4` 固定种子数据：结果 = CPU `numpy.fft.rfft`（C2C 也行），maxRel diff 应 < 1e-4。
- 更大 N（2048×1000）跑 `diff(CPU-N2 golden采样点)`：只抽查若干线（全量 CPU 太慢）。
- 正确性第一：`cufftExecR2C` 返回 `CUFFT_SUCCESS`；再 `cudaDeviceSynchronize`。

## 6. 练习记录（自填）
- plan 参数（istride/idist/odist）：`________`
- 小 N diff：`maxRel = ______`
- 坑记录：`______________________________`

## 7. 自测 Q&A
1. 为什么要 batch=Ls 而不是逐条 Exec？→ 一次 launch + 库内并行，避免 Ls 次 API 往返（对 1000 线是 ~1000× 差异）。
2. R2C 输出为什么是 N/2+1 复数？→ 实信号谱共轭对称，仅存半谱省一半内存/带宽。
3. log 前加小常数目的？→ 数值稳定；谱可能为 0，log0=-inf 会让后续像素失效。
4. 归一化：R2C 无 1/N 归一化（默认），log 域缩放用 times 或 log1p 对齐，要跟产品端“显示亮度”标定——这是**重写最容易错**的环节。
5. 为什么不直接把 magnitude 放 product 链？→ OCT 图像是对数域亮度，幅度/功率在 log 前差 2×，仅影响常数缩放，但 U16 量化范围会受影响，所以先对齐。

## 8. DoD 打卡
- [ ] batch FFT 跑通（PlanMany 配置见 §3）
- [ ] 小尺寸误差可接受（≤1e-4）

## 明日预告
U16 压缩（interpolation 量化）与 Current_Frame 取出（拍照保存）。
