# Week 03 / Day 04 — 任务说明

## 今日目标

读懂旧记录 Log 逆变换与 cutfront25；写兼容层设计。

## 必读代码 / 文档

- VGPU_Get_old_data_toLog_Result
- VGPU_Get_old_data_cutfront25_Result
- VGPU_Get_Denoising_data_toLog_Result
- GpuHandlingDataThreadController 导入分支

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Get_old_data_toLog_Result`
- `VGPU_Get_old_data_cutfront25_Result`
- `VGPU_Get_Denoising_data_toLog_Result`

**功能与实现要点：**

历史格式兼容：已 Log / 未裁前 25 点 / denoising→Log。实现：逐元素核 + width 维 offset。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- notes/W03_legacy_log.md 设计文档
- 可选实现 cut_front(n)

## 任务参考

- 02 链 C

## 完成标准（DoD）

- [ ] 说清旧数据与新 denoising 差异

## 明日预告

对照 Pullback_ProcessData_ToImage；写 W03 REVIEW

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
