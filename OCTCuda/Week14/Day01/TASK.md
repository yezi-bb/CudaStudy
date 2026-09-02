# Week 14 / Day 01 — 任务说明

## 今日目标

精读竞品与导入类 API，做入口格式对照表。

## 必读代码 / 文档

- VGPU_PullbackRawData_To_FFT_Data
- VGPU_C7C8_PullbackFFT_Data_To_Image
- VGPU_PullbackDcm_Data_To_Image
- VGPU_PullbackRawData_To_Image
- ImportationExportationController 搜索 VGPU_

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_PullbackRawData_To_FFT_Data`
- `VGPU_C7C8_PullbackFFT_Data_To_Image`
- `VGPU_PullbackDcm_Data_To_Image`
- `VGPU_PullbackRawData_To_Image`

**功能与实现要点：**

入口格式不同，后方汇合到方图/圆图核。开源：ImportAdapter。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- notes/W14_import_matrix.md

## 任务参考

- 01 §5
- 02 链 C

## 完成标准（DoD）

- [ ] 对照表完成

## 明日预告

缩略图 / 导出路径抽样

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
