# Week 07 / Day 03 — 任务说明

## 今日目标

实现公开简化版导管壁检测（CPU），不追求产品数值一致。

## 必读代码 / 文档

- 宏 POSITION_* / VALUE_THRESHOLD 等

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `（语义等价）VGPU_Catheter_AutoCalibration`

**功能与实现要点：**

每角度径向亮度峰 → 鲁棒中值 → cutHeight。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- cpu_catheter_peak + 合成圆环测试

## 任务参考

- 径向 profile 方法

## 完成标准（DoD）

- [ ] 合成环能检出近似半径

## 明日预告

嵌入 e2e 的 auto_cut

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
