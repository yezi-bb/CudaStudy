# Week 09 / Day 01 — 任务说明

## 今日目标

精读管腔拼接两个 API。

## 必读代码 / 文档

- VGPU_Get_Lumen_Stitching_FFT_Image
- VGPU_Get_Lumen_Stitching_Denoising_Data
- 头文件长注释
- 宿主搜索 Lumen_Stitching

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Get_Lumen_Stitching_FFT_Image`
- `VGPU_Get_Lumen_Stitching_Denoising_Data`

**功能与实现要点：**

远/近端按帧范围拼接；近端旋转角。实现：帧拷贝 + 圆周移位（角度滚动）。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- IO 图
- CPU 滚动拼接原型

## 任务参考

- 01 §6

## 完成标准（DoD）

- [ ] 旋转=圆周移位写清

## 明日预告

GetContinuousCalibration

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
