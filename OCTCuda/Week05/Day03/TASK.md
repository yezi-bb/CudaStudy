# Week 05 / Day 03 — 任务说明

## 今日目标

开源仓串联链 A 主干：Resample→FFT→Transpose→DSC→Enhance→Color。

## 必读代码 / 文档

- 02 链 A
- ImageProcessingController 单帧顺序

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `链 A 全部主干 API`

**功能与实现要点：**

Host：run_scan_frame；中间 KeepDevice；最终 ToHost。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- e2e demo + 合成 PNG
- 每 stage cudaEvent

## 任务参考

- 00_全局规划.md §1

## 完成标准（DoD）

- [ ] 结果图 + stage 耗时表

## 明日预告

Power_aline 旁路 API

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
