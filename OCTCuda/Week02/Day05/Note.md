# Week02 / Day05 — 学习记录（源码填充版）

> 主题：profile 重采样 kernel + Week02 复盘。

## 1. 今日目标（回顾）
用 NSight 看清 kernel 的耗时/占用/访存，产出可写进简历的量化结论，并沉淀 Week02 复盘。

## 2. 常用命令（自填区）

```bash
# 时间（应用层）
./bench_resample --mode identity --lines 1000 --points 2048 --iters 100
# 看单 kernel 占用（ncu）
ncu --set full ./bench_resample ...
# 关键 metric
--metrics gpu__time_duration.avg,sm__throughput.avg.pct_of_peak_sustained_elapsed, \
gpu__compute_memory_throughput.avg.pct_of_peak_sustained_elapsed,dram__bytes_read.sum
```

## 3. 观察表（跑完自填）

| 配置 | 耗时/帧 | SM% | 访存% | 瓶颈猜测 |
| --- | --- | --- | --- | --- |
| blockDim=256, grid=8000, N runtime div | ___ms | | | 整数除法/取模 |
| blockDim=256, N 编译期常量 | ___ms | | | |
| blockDim=512 | ___ms | | | |
| 行分组/共享内存窗缓存版 | ___ms | | | |

结论写法参考：`resample kernel 在 2048 点/1000 线下从 X ms 降到 Y ms（-Z%），瓶颈从取模指令转为 DRAM 带宽(~B%)`——简历量化句可复用。

## 4. Week02 REVIEW 底稿（抄进 `Week02/REVIEW.md`）

**API 范围**：`Resampling_For_Scan / _Scan_Vivo / _For_Pullback` 三入口 + 宿主分支点（ImageProcessingController.cpp L503-506、L717-720、ExportOCTdataView.cpp L983）。
**三行核心**：
1. SD-OCT 要在 k 均匀网格 FFT，故需按标定表重采样（插值），乘 Hann 窗压旁瓣；
2. U16(常规) / U8+gain+offset(自研Vivo) / 批量 frame_sum(回拉) = 一个几何算法三种壳；
3. `windata.h::h_win_data[2049]` 是 DLL 内置窗表；宿主侧可传 NULL 用默认。
**产出**：CPU golden + CUDA kernel + Vivo/Pullback 复用 + diff≤1e-3 + profile 表。
**三个疑问（示例）**
1. 真实标定表 `Calibration.txt` 的“表↔像素坐标”到底如何索引？（无法从闭源 DLL 验证，只能对照 I/O 图）
2. DLL 是否一次调用内部做整帧多 kernel？——宿主只看到单接口返回（L511 一步到位）。
3. Vivo 的 U8 是否已做去噪/坏点校正？——API 未暴露，视为“输入已预处理”。

## 5. 自测 Q&A（本周累计）
1. 为什么强调“先对 CPU golden，再谈性能”？→ 保证重写与契约一致，优化不改变正确性。
2. 为什么 NSight 结论能进简历？→ 量化(ms→ms / SM%/访存%)且讲得清瓶颈归属。
3. 与产品 DLL 相比我们缺什么？→ 缺真实标定表/真实噪声/专用采集路径，但有等价合成测试与接口契约。

## 6. DoD 打卡
- [ ] profile 表已填（§3）
- [ ] `Week02/REVIEW.md` 已用底稿完成
- [ ] 简历量化句已落笔（§3 参考）

## 明日预告
Week03：FFT（cuFFT）与 Log。
