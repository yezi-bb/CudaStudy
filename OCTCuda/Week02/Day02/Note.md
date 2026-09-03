# Week02 / Day02 — 学习记录（源码填充版）

> 主题：CPU 黄金版 Resample+Window，作为 kernel 的验收 oracle。

## 1. 今日目标（回顾）
读透标定表用法 → 写逐行线性插值重采样 → 乘窗 → 存 CPU golden，供 CUDA 版 diff。

## 2. 数据形状（冠脉参考，来自宿主分配）

| 量 | 值 |
| --- | --- |
| 每帧线数 `scan_lines`(Ls) | 1000（回拉 497，见 GlobalConstantValueBase.h `g_scan_lines_number_` / `g_pullback_lines_number_`） |
| 每线点数 `points_per_aline`(N) | 2048（颈动脉 4096） |
| 输入 | `U16` 原始 DMA 数据（帧大小 `Ls×N×2B`） |
| 标定表 | `calibration_data[点]`：每个输出样本在“原始像素”上的目标位置（float，来自 `Calibration.txt`，宿主 `SetCalibrationData` 传入） |
| 窗 | `float[N]` Hann |

## 3. CPU golden 算法（参考实现）

```
对 每帧:  输入 raw[Ls*N] U16
  for line l in [0, Ls):
    for k in [0, N):
      if 使用标定表:  f = calib[l*N + k]           # 目标点在原像素域的浮点位置
      else(identity/线性映射简化):  f = k          # 或 f = k*scale + shift
      lo = floor(f); hi = lo+1; t = f-lo
      x  = interp(raw[(l*N+lo) mod N], raw[(l*N+hi) mod N], t)   # 端点回绕按表设计
      输出 out[l*N+k] = x * w[k]                    # 乘窗
```

要点：
- **逐 aline 独立** → 天然并行（线之间无依赖）。
- 标定表“到底映射什么”由标定文件决定（本仓只有闭源 DLL 行为，无法看内核），因此黄金版先支持 **identity + 单表两模式**，留 `map_mode` 参数；
- 输出域建议 `float`（比产品端可能保留的 U16 更利于 diff）。

## 4. 测试数据（合成，保证可复现）

```cpp
// 正弦扫描模拟一个接近“反射峰”的信号：
// raw(l, k) = 30000 + 1000*sin(2*pi*k/97) + noise(固定种子)
// 期望：identity 模式下 out 应等于 raw*w；peak 位置保持；窗后频谱旁瓣下降
```
golden 输出格式：`cpu_resample_window.bin`（float，`Ls*N`）+ 摘要（min/max/均值）。

## 5. 练习/验收
- [ ] `resample_window_cpu.h` 支持 `mode{identity, table}`，单测 `GOLDEN_MODE=identity` 通过；
- [ ] 对 `N=2048,Ls=1000` 一帧运行 <100ms（CPU 未优化量级），并记录数值范围；
- [ ] 为 Day03 kernel 保留逐行 diff 接口（`diff_max_rel`）。

## 6. 自测 Q&A
1. 为什么用浮点索引做插值而不直接取整？→ 标定目标不在整数像素上，直接取整会让 k 网格有 0.5 像素级错位，损伤轴向分辨率。
2. 逐线独立意味着 kernel 怎么铺线程？→ 可按 `(line, k)` 二维展平成一维 `Ls*N`（每线程一个输出样本），或一个 block 处理多条线以复用窗系数。
3. 帧原始数据布局是行主序吗？→ 是：`raw[l*N + k]`，同一 aline 连续，利于按行访问/共享内存搬运。

## 7. DoD 打卡
- [ ] CPU golden 通过（含 identity 模式）
- [ ] 数值摘要记录在笔记/代码注释

## 明日预告
把 CPU golden 搬到 CUDA kernel。
