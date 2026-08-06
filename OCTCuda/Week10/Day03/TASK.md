# Week 10 / Day 03 — 任务说明

## 今日目标

精读 VGPU_Calculate_Ipa_Result 每一次实参的来源与尺寸。

## 必读代码 / 文档

- IPAAlgorithmController.cpp 中 VGPU_Calculate_Ipa_Result 调用
- reshaped_lumen / labels 从 DicomModel 拷贝
- media 常数 100
- GetGlobalFFTData

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Calculate_Ipa_Result`

**功能与实现要点：**

输入 FFT U16 卷；输出 miu 体 + line_ipa_miu（carpet）；
lipid 阈值→in_ipa_11_mat_cof；isVivoData 影响噪声等行为。
尺寸：depths=cols，theta=rows，alines=frames*theta。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 绘制链 D 详细版（每指针尺寸）

## 任务参考

- 02 链 D

## 完成标准（DoD）

- [ ] 尺寸公式与 GetGlobal* 对应无误

## 明日预告

开源 μ 估计 SPEC

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
