# Week10 REVIEW — IPA 参数与规格

## 1. 本周产出（全部归档）
- notes/W10_ipa_physics.md — IPA 物理直觉（公开）
- notes/W10_att_paras.md — att_paras 三配置表（P60/P80/C7C8）+ 尺寸派生 + 新旧 API
- Week10/Day03/Note.md §3 — 链 D 详细版：10 实参来源与尺寸
- Week10/Day04/Note.md §3-6 — μ 估计器 SPEC（落点 OCTCudaProject/oct/Ipa/SPEC.md）
- Week10/REVIEW.md（本文件）

## 2. 核心表：三配置（源 IPAAlgorithmController.cpp L56-103）
| 字段 | P60 | P80 | C7C8 |
| --- | --- | --- | --- |
| 脂质阈值 | 9.5 | 10.5 | 11 |
| z0/zR/zw | 0/3/10 | 0.5/2/7 | 0.91/0.99/5 |
| noise_level | 7 | 7 | 4 |
| minwin | 41 | 46 | 41 |
| isVivoData | true | true | false |
预设 stepsucc=0.5/stepfail=0.2；step=ceil(比例×minwin)。

## 3. 尺寸公式
- number_depths = RawToFFTDataCols (1025)；number_theta = RawToFFTDataRows (500)
- number_alines = frames×theta；μ 体 = frames×theta×depth float（帧外层布局）

## 4. 链 D 数据流（每指针尺寸见 Day03 §3）
FFT U16 卷 + reshaped_lumen[alines] + media=100 + labels[alines]
→ VGPU_Calculate_Ipa_Result(att_paras, …, 脂质阈值, ground_noise=0, isVivoData)
→ μ 体 float + line_μ[alines] → All_Aline_Mu_Data_To_Image 出图 / UpdateValueIPA 重算毯展

## 5. 下周（W11）
CPU μ 估计器实现 + 合成卷验收；CUDA 每线一线程并行化；μ→圆图。
