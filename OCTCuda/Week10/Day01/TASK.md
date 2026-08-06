# Week 10 / Day 01 — 任务说明

## 今日目标

建立 IPA 公开层面的物理/临床直觉。

## 必读代码 / 文档

- 公开检索：OCT intraplaque attenuation / lipid plaque attenuation coefficient（读摘要）
- VGPU_Process.cuh IPA region 注释

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `（概念）IPA`

**功能与实现要点：**

μ 反映组织光衰减；与脂质斑块分析相关。本计划目标是工程数据流与可公开复现估计器，不复制产品阈值。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- notes/W10_ipa_physics.md（公开表述）

## 任务参考

- 公开综述摘要

## 完成标准（DoD）

- [ ] 能用自己的话解释 IPA 功能

## 明日预告

att_paras 逐字段对照宿主

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
