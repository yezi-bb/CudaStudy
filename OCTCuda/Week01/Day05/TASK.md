# Week 01 / Day 05 — 任务说明

## 今日目标

吃透 DOCMotionType 与 is_device_to_host；完成 Week01 复盘。

## 必读代码 / 文档

- VGPU_Process.cuh 枚举 DOCMotionType
- ImageProcessingController 中 status 与 true/false 传参（至少统计 10 处）
- 02_数据流与调用链.md 链 A

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `DOCMotionType`
- `is_device_to_host`

**功能与实现要点：**

SCAN vs PULLBACK_* 切换不同 device 指针/尺寸。
实时主路径中间阶段 is_device_to_host=false，最后显示再 D2H。
开源：CopyPolicy + PipelinePhase。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 撰写 Week01/REVIEW.md（API 列表、尺寸笔记、三个疑问）
- 更新 03_进度追踪.md
- 可选：5 分钟口述显存生命周期

## 任务参考

- 02_数据流与调用链.md

## 完成标准（DoD）

- [ ] REVIEW.md 已写
- [ ] 能默述链 A 前三步
- [ ] 开源仓出现 CopyPolicy

## 明日预告

进入 Week02：重采样与窗函数

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
