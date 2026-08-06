# Week 11 / Day 05 — 任务说明

## 今日目标

理清 out_carpet_att 与 line_ipa_miu 后续用途；复盘。

## 必读代码 / 文档

- Calculate 两路输出在宿主的保存位置
- pre_ipa_analysed_result

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Calculate_Ipa_Result 输出`

**功能与实现要点：**

line μ 供 UpdateValueIPA；carpet 服务毯展。开源可先 line_mu = reduce(depth)。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- Week11/REVIEW.md
- 输出缓冲区字典

## 任务参考

- 预习 BackgroundIPA / IPAZone

## 完成标准（DoD）

- [ ] 字典完成

## 明日预告

Week12 UpdateValueIPA 与线程

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
