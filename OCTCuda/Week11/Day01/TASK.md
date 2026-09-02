# Week 11 / Day 01 — 任务说明

## 今日目标

CPU 实现单 A-line μ 拟合；合成指数衰减验证。

## 必读代码 / 文档

- 开源 SPEC
- IPAAlgorithmController::ProcessingOneFrame 路径

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Calculate_Ipa_Result`

**功能与实现要点：**

合成 I(z)=A*exp(-2μz)+noise；估计 μ 应接近真值。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- cpu_aline_mu_test
- 误差报告

## 任务参考

- log(eps+I) 数值稳定

## 完成标准（DoD）

- [ ] 合成数据相对误差可接受

## 明日预告

扩展到一帧多线

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
