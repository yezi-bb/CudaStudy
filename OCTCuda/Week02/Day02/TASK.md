# Week 02 / Day 02 — 任务说明

## 今日目标

实现 CPU 版重采样 + Hann（合成数据）。

## 必读代码 / 文档

- WinType 枚举
- SetCalibrationData 与 Resampling 关系

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_SetCalibrationData`
- `VGPU_Data_Resampling_For_Scan`

**功能与实现要点：**

简化假设线性映射；每 A-line 插值到 N 点后乘 Hann；输出 float。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- oct-cuda-pipeline: cpu_resample_window + 固定种子合成 chirp 单测

## 任务参考

- 线性插值数值方法

## 完成标准（DoD）

- [ ] CPU 输出稳定可测
- [ ] 测试锁定

## 明日预告

CUDA naive window kernel

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
