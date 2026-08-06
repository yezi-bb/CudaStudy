# Week 08 / Day 03 — 任务说明

## 今日目标

精读 guiding 检测 API。

## 必读代码 / 文档

- VGPU_guidingDetectOneFrame
- 宿主搜索 guidingDetect

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_guidingDetectOneFrame`

**功能与实现要点：**

窗口内平均像素序列；threshold/window/startRow/totalFrame。实现：滑动均值。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- CPU sliding mean
- totalFrame 用法笔记

## 任务参考

- 01 §4

## 完成标准（DoD）

- [ ] 伪代码完成

## 明日预告

检测 hooks 总图

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
