# Week15 / Day02 — 学习记录（源码填充版）

> 主题：正式性能表（docs/perf.md）——方法论与模板（真实数字留给你在 bench 上跑后填）。

## 1. 今日目标（回顾）
产出一张“可放简历”的性能表：每个 stage 的 GPU 时间、整链 fps、CPU 对比、DSC v1/v2 收益；原始结果归档。

## 2. 方法论（先定规则，防自嗨）
- 数据：合成 U16 卷（550 帧×500×1025，与产品同量级，无病患数据）；
- 计时：CUDA event 包 kernel（`cudaEventRecord` 起止）跑 **N=10 次取中位数**，排除首帧 warm-up；
- CPU 对比：同实现 CPU 版（W11 cpu_* 同款策略）计时同一合成卷；
- DSC v1（像素循环）vs v2（行内插）在同一卷、同一核函数入口分别计时；
- 机器信息：GPU 型号/驱动/CUDA 版本、编译 -O2、Nsight 版本（写进表尾）。

## 3. perf.md 模板（落 docs/perf.md）
```markdown
# 性能表（合成卷 550×500×1025 U16）

| Stage | GPU ms | CPU ms | 加速比 | 说明 |
|-------|--------|--------|--------|------|
| Resample+Window | _ | _ | _ | 每 A-line 查表插值 |
| FFT+Log | _ | _ | _ | cuFFT 批次 |
| Transpose+Crop | _ | _ | _ | 全局写合并 |
| DSC v1 | _ | _ | _ | 逐像素坐标+双线性 |
| DSC v2 | _ | _ | _ | 行缓存内插 |
| Enhance+Color | _ | _ | _ | 整链 e2e 中 |
| **整链 e2e (fps)** | _ ms → _ fps | _ ms | — | 含 H2D/D2H 抽样 |
| Pullback batch (整卷) | _ ms | _ | — | 02 状态机 PullbackBulk |

DSC v2 相对 v1 提升：_ %（同机同卷）。
原始结果归档：bench/output_YYYYMMDD.txt（附 nsys/ncu 摘要）。
```
> 写“同机同卷、中位数×10、Nsight 版本”三要素，数字才有可信度。

## 4. bench 工程落点
- bench/main_bench.cpp：调用 oct::E2E，逐 stage event 计时；输出 CSV+md 表；脚本 `bench/run_bench.ps1` 归档 stdout。
- 先保证“正确性断言”在 tests 全绿，再谈性能（性能表只对验证过的实现有效）。

## 5. DoD 打卡
- [ ] perf.md 表格全填 + 原始输出归档（机器信息齐全）
