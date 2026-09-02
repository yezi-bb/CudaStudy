# Week 06 / Day 04 — 任务说明

## 今日目标

分析侧灌回 FFT 与单帧 Raw→图。

## 必读代码 / 文档

- VGPU_Set_all_U16_FFT_data_to_Gpu
- VGPU_Set_all_FFT_data_to_Gpu
- VGPU_OneFrameRawData_To_Image
- IntegrationChannel 相关搜索

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Set_all_U16_FFT_data_to_Gpu`
- `VGPU_Set_all_FFT_data_to_Gpu`
- `VGPU_OneFrameRawData_To_Image`

**功能与实现要点：**

分析改参时 Host 已有 FFT，需再 H2D。OneFrame 用于单帧预览。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 开源 upload_fft_volume
- 调用序笔记

## 任务参考

- 02 链 C

## 完成标准（DoD）

- [ ] 说清「成像上传 Raw」vs「分析上传 FFT」

## 明日预告

实现批处理骨架；W06 REVIEW

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
