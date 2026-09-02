# Week 07 / Day 04 — 任务说明

## 今日目标

分析校准失败模式；e2e 增加 auto_cut 开关。

## 必读代码 / 文档

- ImageProcessingController 成功/失败分支

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Catheter_AutoCalibration`
- `VGPU_CheckImageInfo`

**功能与实现要点：**

失败可能是阈值或硬件；开源用开关切换手动/自动 cut。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- e2e 接 auto_cut
- 失败模式笔记

## 任务参考

- 02 链 A

## 完成标准（DoD）

- [ ] e2e 可切换 cut 来源

## 明日预告

W07 REVIEW（方法公开 vs 阈值私有）

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
