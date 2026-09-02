# Week 04 / Day 03 — 任务说明

## 今日目标

精读 DSC 全部参数；推导极→直公式。

## 必读代码 / 文档

- VGPU_DSC 声明
- InterpolateType
- ImageProcessingController DSC 调用

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_DSC`

**功能与实现要点：**

圆图像素 (x,y)→(r,θ)→在极坐标 rect 上插值。inner_r/margin_r 控制有效环带。
插值：最近邻 / 双线性 / 三次。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 手推公式写入 notes
- CPU 最近邻 DSC 出图

## 任务参考

- scan conversion 公开资料

## 完成标准（DoD）

- [ ] 公式 + CPU 最近邻结果图

## 明日预告

双线性 DSC CPU + CUDA

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
