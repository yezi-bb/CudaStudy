# Week05 / Day04 — 学习记录（源码填充版）

> 主题：光灵敏度测试 API `Data_Power_aline(_Vivo)` —— 独立于显示链的旁路统计。

## 1. 今日目标（回顾）
精读两条 Power_aline；说明其为何独立于主显示链；实现简单 reduction。

## 2. 真实声明（VGPU_Process.cuh L368-371）

```cpp
/*计算一帧取log后的均值(光灵敏度测试使用，计算过程保留去底噪前的设计)*/
bool VGPU_Data_Power_aline(U16* Original_data_scan, float ground_noise, float* aline_power_data);
bool VGPU_Vivo_Data_Power_aline(U8* Original_data_scan, double gain_multiplier, int offset_data,
                                float ground_noise, float* aline_power_data);
```
- 输入 = 一帧 raw（U16 或 U8Vivo + gain/offset），输出 `aline_power_data`（通常按线返回功率统计，大小由帧线数决定）；
- 注释要点：**“取 log 后的均值” + “保留去底噪前的设计”** → 结果来自 log 前/后谱的功率统计，用于光灵敏度校准/测试，不是成像用。

## 3. 为什么独立于显示链（DoD 口述答案）
- 成像链的 FFT→log→DSC 输出面向“图像对比度”，经过了窗、压缩、插值等**有损变换**，不能用于测量光功率/灵敏度；
- Power_aline 要的是**保留底噪、未经 log/压缩的功率谱**逐线统计 → 用独立的、近似原始谱的旁路计算；
- 触发场合：工程/产测（光灵敏度自检、光源一致性），平时不跑，不影响主链帧率。

## 4. 实现：reduction（参考）
统计每线功率均值：
```cpp
// 对每条 aline：power_mean[l] = mean_k( p[k] )，p[k] 为去底后功率（log 前）
__global__ void alinePowerKernel(const float* __restrict__ spect, float* __restrict__ out,
                                 int lines, int half) {
  int l = blockIdx.x;                                  // 一个 block 一条线
  int k = threadIdx.x; float sum = 0.f;
  const float* row = spect + (size_t)l*half;
  for (int i = k; i < half; i += blockDim.x) sum += row[i];
  // warp/block reduce → out[l] = sum/half
}
```
也可直接 `thrust::reduce(thrust::device, first, last, 0.f, plus<float>())` 后除元素数——任务允许两者其一。U8Vivo 版先 `(u8-offset)*gain` 再入谱。

## 5. 与 DSC 链关系笔记（DoD 交付）
```
成像链: raw → resample+窗 → FFT → log压缩 → 窗映射 → DSC圆图 → 显示
Power_aline(旁路): raw → (仅去底, 不做log/压缩) → 每线功率统计 → 灵敏度曲线
共同点: 都消费同一帧 raw, 可共用原始缓冲;
差异点: 成像链有损（log/窗/U16），旁路保留物理功率；故必须独立 API。
```

## 6. 自测 Q&A
1. “取 log 后的均值”到底算什么？→ 语义指在 log 域算均值(或 log 前谱的均值)，总之是功率量；重点是保留去底噪前设计 → 不应用成像链的 ground_noise 后处理。
2. 为什么不直接复用 FFT_Power 的中间谱？→ 成像链谱已被压缩/裁剪/缩放，量纲不同。
3. 逐线 reduce 用 block-per-line 的理由？→ 线间独立（约 1000 线），block-per-line 天然对齐 warp reduce。
4. 何时触发？→ 产测光灵敏度窗口，不是实时主循环。
5. Vivo 版多什么？→ U8 需 gain/offset 线性搬移回光强，与 Week02 的 `_Scan_Vivo` 同一换算。

## 7. DoD 打卡
- [ ] 能口述为何独立于显示链（§3）
- [ ] reduction 跑通并对比 CPU 均值（§4）

## 明日预告
W05 复盘 + 简历句 + W06 预习。
