# Week 08 / Day 01 — 任务说明

## 今日目标

精读造影剂检测 Check5 与 Afd。

## 必读代码 / 文档

- VGPU_Contrast_MediumCheck5
- VGPU_Contrast_MediumCheck_Afd
- 宏 LINE_AVERAGE_GAP / PULL_BACK_THRESHOLD
- 宿主搜索 Contrast_Medium

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Contrast_MediumCheck5`
- `VGPU_Contrast_MediumCheck_Afd`

**功能与实现要点：**

判断介质冲洗是否充分以允许回拉。公开版：环带亮度比例与 gap 统计；Afd 多阈值 + isSmoke。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 参数释义笔记
- 与回拉许可的状态关系笔记

## 任务参考

- 01 §4

## 完成标准（DoD）

- [ ] 能口述检测目的与插入时机

## 明日预告

导管折断检测

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
