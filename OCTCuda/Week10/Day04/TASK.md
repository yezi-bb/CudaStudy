# Week 10 / Day 04 — 任务说明

## 今日目标

设计开源 μ 估计规格（教学用），不宣称等于产品。

## 必读代码 / 文档

- minwin / step_* / SNR 字段

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Calculate_Ipa_Result（实现假设）`

**功能与实现要点：**

每 A-line：在 lumen 外深度窗对 log(I) 线性拟合得斜率≈μ；
窗口搜索受 minwin/step 约束；labels 掩膜跳过无效线。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 开源仓 oct::Ipa/SPEC.md
- CPU 伪代码

## 任务参考

- 最小二乘拟合

## 完成标准（DoD）

- [ ] SPEC 可供他人实现

## 明日预告

W10 REVIEW

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
