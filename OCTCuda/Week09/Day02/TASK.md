# Week 09 / Day 02 — 任务说明

## 今日目标

精读 GetContinuousCalibration 与 machine_model。

## 必读代码 / 文档

- VGPU_GetContinuousCalibration
- 注释：0 冠脉 / 1 颈动脉 / 2 颅内
- 宿主搜索 ContinuousCalibration

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_GetContinuousCalibration`

**功能与实现要点：**

输出每帧 catheterCutStartHeight；机型参数不同。公开版：逐帧寻峰 + 时序平滑。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 三机型差异笔记（仅宿主可见信息）
- int cuts[frames] 设计

## 任务参考

- 01 §6

## 完成标准（DoD）

- [ ] 与单帧校准差异表

## 明日预告

Continuous_* 出图 API

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
