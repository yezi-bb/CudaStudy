# Week 11 / Day 04 — 任务说明

## 今日目标

精读并实现 All_Aline_Mu_Data_To_Image（复用 DSC）。

## 必读代码 / 文档

- VGPU_All_Aline_Mu_Data_To_Image
- IPAAlgorithmController 单帧/全卷调用

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_All_Aline_Mu_Data_To_Image`

**功能与实现要点：**

把 μ 方图当强度做 DSC+量化；支持 icut_start 数组与 isVivoData。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 复用 oct::Dsc 出 μ 圆图 PNG

## 任务参考

- 01 §7

## 完成标准（DoD）

- [ ] μ 圆图可出

## 明日预告

理解 carpet / line_ipa_miu；W11 REVIEW

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
