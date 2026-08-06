# Week 04 / Day 04 — 任务说明

## 今日目标

实现双线性 DSC：CPU 黄金版 + CUDA naive（全局内存）。

## 必读代码 / 文档

- VGPU_DSC

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_DSC`

**功能与实现要点：**

每像素一线程；atan2+sqrt；双线性；越界写 0。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- dsc_bilinear.cu
- 与 CPU 误差报告

## 任务参考

- 01 §2 DSC

## 完成标准（DoD）

- [ ] CUDA 出圆图
- [ ] 误差报告

## 明日预告

texture 优化尝试 + W04 REVIEW

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
