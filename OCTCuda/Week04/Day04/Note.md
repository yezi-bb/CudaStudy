# Week04 / Day04 — 学习记录（源码填充版）

> 主题：双线性 DSC —— CPU 黄金版与 CUDA naive 版对齐。

## 1. 今日目标（回顾）
把 Day03 最近邻升级为双线性取样（产品实时用的插值法），CPU→CUDA 逐点一致。

## 2. 双线性公式
在 rect 上取浮点坐标 (fr, fc)，取四个邻点加权：
```
r0=floor(fr), r1=r0+1, c0=floor(fc), c1=c0+1
tr=fr-r0, tc=fc-c0
v = (1-tr)*( (1-tc)*src[r0][c0] + tc*src[r0][c1] )
  +    tr *( (1-tc)*src[r1][c0] + tc*src[r1][c1] );
```
边界：c1 在 c0=raw_cols-1 时回绕到 0（角度是圆环）——**角度维循环、深度维夹取**。

## 3. CPU 黄金版（dsc_bilinear）与验证
- 输入 rect 用固定种子合成（双亮斑 + 斜边），期望：圆图上亮斑呈现为角向清晰、径向渐变的弧形；
- 最近邻与双线性对比：斜边应无锯齿（视觉）且数值两版差异 >0（平滑度证明生效）；
- 存 `cpu_dsc_bilinear.bin` 供 GPU diff。

## 4. CUDA naive kernel（参考）

```cpp
__global__ void dscBilinearKernel(const float* __restrict__ rect, float* __restrict__ polar,
                                  int raw_rows, int raw_cols, int H, int W,
                                  float cx, float cy, float dr) {
  int p = blockIdx.x*blockDim.x + threadIdx.x;
  if (p >= H*W) return;
  int x = p % W, y = p / W;
  float dx = x-cx, dy = y-cy;
  float r = sqrtf(dx*dx + dy*dy), th = atan2f(dy, dx);
  float fc = (th+PI_F)/(2*PI_F)*raw_cols;      // float 角度→线
  float fr = r/dr;
  if (fr < 0.f || fr > raw_rows-1.f) { polar[p] = 0.f; return; }
  int c0 = (int)floorf(fc); int c1 = c0+1;
  c0 = (c0+raw_cols)%raw_cols; c1 %= raw_cols;   // 角度回绕
  int r0 = (int)fr, r1 = r0+1; r1 = min(r1, raw_rows-1); // 深度夹取
  float tc = fc-c0 /*注意回绕后仍是原 frac*/, tr = fr-r0;
  ... 按 §2 四邻加权写 polar[p]
}
```
> 注意：fc 取模回绕后 `c0` 变了，frac 需用**回绕前**值：`tc = fc - floorf(fc)`；实现时先存 frac 再取整回绕。

## 5. 性能与正确性记录（自填）
| 版本 | diff(CPU) | 耗时/帧 |
| --- | --- | --- |
| CPU bilinear | — | ___ ms |
| GPU naive (1 线程/像素, 704²=495k) | maxRel≤1e-3 | ___ ms |
| （Day05 纹理版） | | ___ ms |

常见坑：atan2/π 精度、mod 负值、fr 越界是否写 0、row-major 索引 `src[r*raw_cols+c]` 方向写反。

## 6. 自测 Q&A
1. 为什么角度维要“循环”而深度维“夹取”？→ 360° 首尾是同一 A 线（连续性）；深度方向是成像范围，越界即无信号。
2. 为什么实时用双线性不用最近邻？→ 圆图 1000 线到 704² 需角向重采样，双线性显著降锯齿且成本低（3 次乘加）。
3. 输出像素数 704² 与 raw 数据量比，访存模式如何？→ 相邻像素角度连续 → rect 列跳跃访问；真实优化用纹理/查表（Day05）。
4. naive 版本为什么先不用共享内存？→ 输出逐像素独立、输入访问跨行跨列无 tile 复用收益大；先正确后优化。

## 7. DoD 打卡
- [ ] GPU bilinear DSC 与 CPU 一致（§5）
- [ ] 公式与边界策略写入笔记（§2）

## 明日预告
纹理/硬件加速版 DSC 与 W04 复盘。
