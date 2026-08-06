# Week 11 / Day 02 — 任务说明

## 今日目标

CPU 整帧/小卷 μ；简化 lumen/labels 掩膜。

## 必读代码 / 文档

- 宿主 lumen/labels 用法

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Calculate_Ipa_Result 掩膜输入`

**功能与实现要点：**

仅在 lumen 外拟合；labels 跳过；media 简化为固定偏移。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- cpu_volume_mu
- 掩膜单测

## 任务参考

- 02 链 D

## 完成标准（DoD）

- [ ] 掩膜生效

## 明日预告

CUDA：一线一 block

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
