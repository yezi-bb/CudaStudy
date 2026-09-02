# Week 04 / Day 05 — 任务说明

## 今日目标

DSC texture 优化尝试；Week04 复盘。

## 必读代码 / 文档

- cudaTextureObject 文档

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_DSC`

**功能与实现要点：**

rect 绑定 texture；对比 v1/v2 耗时与 Nsight 内存指标。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- Week04/REVIEW.md
- 性能对比表

## 任务参考

- Nsight Compute 内存指标

## 完成标准（DoD）

- [ ] 至少有 v1 计时；v2 有结论（成功或阻塞原因）

## 明日预告

Week05 增强与伪彩、e2e

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
