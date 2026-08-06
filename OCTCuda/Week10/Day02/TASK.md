# Week 10 / Day 02 — 任务说明

## 今日目标

对照宿主填写 att_paras：P60 / P80 / C7；对比旧 SetConfig API。

## 必读代码 / 文档

- IPAAlgorithmController.cpp IPAProcessing 填参（约 56–180 行）
- att_paras 定义
- 08Code/.../IpaAlgorithmKernel.cuh

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `att_paras 全字段`
- `GUP_SetIpaalgorithmConfig（旧）`

**功能与实现要点：**

做三张配置表；step_success=ceil(stepsucc*minwin)。
旧：先 SetConfig；新：Calculate 直接传 h_paras。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- notes/W10_att_paras.md 三配置表
- 新旧 API 差异

## 任务参考

- 01 §7
- IpaAlgorithmKernel.cuh

## 完成标准（DoD）

- [ ] 三配置表完成
- [ ] 新旧差异写明

## 明日预告

Calculate 实参来源精读

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
