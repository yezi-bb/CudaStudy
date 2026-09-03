# Week02 / Day03 — 学习记录（源码填充版）

> 主题：把 CPU golden 翻译成 CUDA kernel，并逐点 diff。

## 1. 今日目标（回顾）
编写 `resampleWindowKernel`，与 CPU golden 一致（1e-3 相对误差内），会看 launch 配置对性能/正确性的影响。

## 2. Kernel 设计（参考骨架）

```cpp
// 输入 raw U16[Ls*N], calib float[Ls*N](table模式)或null, w float[N]
// 输出 out float[Ls*N]
__global__ void resampleWindowKernel(const unsigned short* __restrict__ raw,
                                     const float* __restrict__ calib,
                                     const float* __restrict__ w,
                                     float* __restrict__ out,
                                     int Ls, int N, int mode) {
  int idx = blockIdx.x*blockDim.x + threadIdx.x;      // 展平 Ls*N
  if (idx >= Ls*N) return;
  int l = idx / N, k = idx - l*N;                     // 除法取线号
  float f = (mode==0) ? (float)k : calib[idx];        // identity | table
  int lo = (int)f; int hi = lo+1;                     // 端点在表设计里合法(0..N-1, 不越界)
  float t = f - lo;
  const float* rl = raw + (size_t)l*N;                // 该 line 基址
  float x = rl[lo]*(1.f-t) + rl[hi]*t;                // 线性插值(逐点)
  out[idx] = x * w[k];                                // 乘窗
}
```

要点：
- `int idx = blockIdx.x*blockDim.x + threadIdx.x` 一维展平最简单；`Ls=1000, N=2048` → 2.048M 线程。
- 每线程读一次 raw 附近 2 元素 → **未合并**程度低（每 warp 32 连续 k，访问连续地址，实际合并良好）。
- `__restrict__` + 只读标记给编译器优化空间；`N` 为常量时可用模板参数避免运行时除法。
- 若追求更优：每 block 处理几条完整 aline，用共享内存缓存 `w` 与行数据，减少全局读（Day05 再做性能对比，今天是“对得上”）。

## 3. 配置自查
`N=2048`：推荐 `blockDim=256`、`grid=(Ls*N+255)/256=8000`；对比 `blockDim=512`。启动后 `cudaDeviceSynchronize(); cudaGetLastError();` 必须通过。

## 4. 验证：与 Day02 golden diff

```cpp
double maxRel = 0, sumAbs=0;
for (size_t i=0;i<Ls*N;i++){ double rel=fabs(g[i]-k[i])/max(1.0,fabs(g[i])); maxRel=max(maxRel,rel); sumAbs+=rel; }
printf("maxRel=%.3e meanRel=%.3e\n", maxRel, sumAbs/(Ls*N));
```
标准：`maxRel < 1e-3`（float 精度与同一算法时更可达 ~1e-6）。若不对，先查：窗表长度/端点策略、索引 `lo/hi` 边界、行主序假设、类型转换（U16→float）。

## 5. 练习记录（自填区）
- 本机 GPU：`________`；`blockDim=256` 耗时：`______ ms/帧`
- diff 结果：`maxRel = ______`
- 遇到的坑：`______________________________`

## 6. 自测 Q&A
1. 为什么用 `raw + l*N` 拿行基址而不是 `idx/N` 后重复寻址？→ 同一行内多线程共享一次取模/行基址，可读性好且利于后续 L2 命中。
2. `N` 编译期常量为什么重要？→ 消掉 `%`、`/`，且 `w[k]` 可用常量/`__ldg`；性能差可达 20-50%。
3. 为什么不直接 `out[idx] = x * w[l*N+k]`？→ 窗只与 k 相关（每线同窗），存 `float[N]` 更省且 L1 友好。
4. kernel 正确性优先级高于性能：本节最该跑什么？→ `diff(CPU,GPU)` + `cuda-memcheck`/`compute-sanitizer` 过一遍。

## 7. DoD 打卡
- [ ] `resampleWindowKernel` 与 golden 对齐（≤1e-3）
- [ ] 记录两种 blockDim 的性能与 diff 结果

## 明日预告
Vivo(U8+gain/offset) 与 Pullback(批量) 两路。
