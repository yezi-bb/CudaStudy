# Week 02 / Day 03 — 任务说明

## 今日目标

CUDA：每线程一采样点乘窗；标定插值可先简化为 identity。

## 必读代码 / 文档

- BLOCK_DIM = 256

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Data_Resampling_For_Scan`

**功能与实现要点：**

__global__ apply_window；grid-stride；窗放 constant 或只读缓冲；与 CPU 比误差。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 实现 kernel + H2D/D2H
- max abs error 报告

## 任务参考

- CUDA Best Practices — coalescing

## 完成标准（DoD）

- [ ] 误差达标（如 1e-5）

## 明日预告

Vivo 与 Pullback 重采样分支

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
