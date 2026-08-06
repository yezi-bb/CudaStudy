# Week 07 / Day 02 — 任务说明

## 今日目标

对照旧校准 API 与 cs 测试接口、CheckImageInfo。

## 必读代码 / 文档

- VGPU_AutoCalibration_new / _connect / *_cs
- VGPU_CheckImageInfo
- 宿主中注释掉的旧调用

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_AutoCalibration_new`
- `VGPU_AutoCalibration_connect`
- `VGPU_AutoCalibration_new_cs`
- `VGPU_AutoCalibration_connect_cs`
- `VGPU_CheckImageInfo`

**功能与实现要点：**

cs 接口直接吃 Host transpose，便于离线单测；CheckImageInfo：0 阈值 / 1 硬件。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 新旧对照表
- 设计开源 calib_from_transpose

## 任务参考

- 01 §3

## 完成标准（DoD）

- [ ] 对照表完成

## 明日预告

CPU 简化寻峰校准

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
