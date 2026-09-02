# Week 12 / Day 02 — 任务说明

## 今日目标

追踪「改阈值 → Update → UI」线程与信号。

## 必读代码 / 文档

- BackgroundIPAUpdateThreadController.cpp
- UpdateIpaValueSignal 等相关信号
- 后台退出/取消标志

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_UpdateValueIPA`
- `VGPU_Calculate_Ipa_Result（对比轻重）`

**功能与实现要点：**

Calculate 重、Update 可反复；后台可取消。开源拆两阶段 API。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 序列图 notes/W12_ipa_threads.md

## 任务参考

- 02 链 D

## 完成标准（DoD）

- [ ] 序列图完成

## 明日预告

开源简化 Update 实现

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
