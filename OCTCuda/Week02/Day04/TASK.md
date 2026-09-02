# Week 02 / Day 04 — 任务说明

## 今日目标

对照 Vivo / Pullback 重采样 API，补全开源分支。

## 必读代码 / 文档

- ImageProcessingController 中 _Vivo 与 Pullback 相关分支

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Data_Resampling_For_Scan_Vivo`
- `VGPU_Data_Resampling_For_Pullback`

**功能与实现要点：**

Vivo 先 scale；Pullback 带 frame_sum。开源 InputKind { U16, U8Vivo }。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 扩展 resample(InputKind,...)
- 宿主选分支笔记

## 任务参考

- 02 链 A/B

## 完成标准（DoD）

- [ ] 分支表写入 notes
- [ ] 代码含 U8 路径

## 明日预告

W02 profile + REVIEW

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
