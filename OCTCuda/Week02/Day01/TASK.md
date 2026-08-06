# Week 02 / Day 01 — 任务说明

## 今日目标

理解原始光谱 → 重采样加窗的物理与工程动机。

## 必读代码 / 文档

- VGPU_Data_Resampling_For_Scan / _Vivo / _For_Pullback 声明
- Algorithm/vgpu/include/windata.h（窗系数表用途）
- ImageProcessingController 中 Resampling 调用上下文

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Data_Resampling_For_Scan`
- `VGPU_Data_Resampling_For_Scan_Vivo`
- `VGPU_Data_Resampling_For_Pullback`

**功能与实现要点：**

SD-OCT 需在均匀波数网格上 FFT；窗抑制旁瓣。
Vivo：U8 + gain/offset 转浮点。Pullback：多帧入口。
实现：标定表引导插值 + 乘窗（Hann 等）。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 笔记：U16 vs U8 输入差异表
- CPU/Python 生成 Hann 并可视化

## 任务参考

- 公开 SD-OCT k-linearization 综述摘要
- 01_API接口全解.md §2 Resampling

## 完成标准（DoD）

- [ ] 能解释 FFT 前为何重采样+加窗
- [ ] Hann 数组可复现

## 明日预告

实现 CPU 黄金版 resample+window

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
