# Week 06 / Day 03 — 任务说明

## 今日目标

精读 FFT→方图/圆图与校准裁剪批处理、对比度、单帧取图。

## 必读代码 / 文档

- VGPU_Handle_All_FFT_data
- VGPU_Handle_All_Calibration_Image
- VGPU_CalculatedContrastRange
- VGPU_Hnad_One_Frame_Data

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Handle_All_FFT_data`
- `VGPU_Handle_All_Calibration_Image`
- `VGPU_CalculatedContrastRange`
- `VGPU_Hnad_One_Frame_Data`

**功能与实现要点：**

复用 DSC/Enhancement；icut_start/size；自适应对比度；按帧取图（注意 API 拼写 Hnad）。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 开源 render_volume_to_circles
- Calibration vs All_FFT 差异笔记

## 任务参考

- 01 §5

## 完成标准（DoD）

- [ ] 差异表完成

## 明日预告

Set_all_FFT / OneFrameRaw

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
