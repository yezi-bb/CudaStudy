# W10 — IPA 物理与临床直觉（公开表述，教学用）

## 模型
I(z) = I0·e^(−μz)·G(z)；ln I = ln I0 − μz + ln G(z)
μ = 组织光衰减系数（mm⁻¹）；脂质斑块区 μ 高。

## 数据规模（约）
550 帧 × 500 θ × 1025 depth ≈ 2.8e8 深度样本/卷 → 逐 A-line 窗式拟合 → GPU。

## 源码落点
- att_paras 定义：VGPU_Process.cuh L161-178
- 填参：IPAAlgorithmController.cpp IPAProcessing L46-244
- 公开估计方法：每 A-line 在 lumen 外深窗对 ln I 线性拟合斜率 ≈ −μ（滑窗 minwin/step 控制）

## 合规
可公开：模型/字段语义/方法；私有：产品标定数值与阈值-组织学映射。
