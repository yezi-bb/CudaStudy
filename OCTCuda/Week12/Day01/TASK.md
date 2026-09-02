# Week 12 / Day 01 — 任务说明

## 今日目标

精读 VGPU_UpdateValueIPA 全部参数与输出缓冲。

## 必读代码 / 文档

- VGPU_UpdateValueIPA 头文件长注释
- BackgroundIPAUpdateThreadController 中调用
- IPAZoneController 中调用

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_UpdateValueIPA`

**功能与实现要点：**

输入 InlineIPA；输出 IPA_L / RangeMean / IPA_A / IPA_T / colorbars；
受 InThresholdT、Mode_ID、pixelSapcing、isVivolightIPA 控制。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 参数→输出→UI 字段对照表

## 任务参考

- 01 §7 Update

## 完成标准（DoD）

- [ ] 对照表完成

## 明日预告

阈值变更完整数据流

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
