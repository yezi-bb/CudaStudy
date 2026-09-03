# Week10 / Day04 — 学习记录（源码填充版）

> 主题：开源 μ 估计器 SPEC（教学用，不宣称等于产品）。

## 1. 今日目标（回顾）
写一份“别人照此可实现”的估计器规格 + CPU 伪代码，落点为开源仓 `OCTCudaProject/oct/Ipa/SPEC.md`（本 Note 即完整 SPEC 底稿）。

## 2. 目标与边界
- 目标：输入 FFT/log 方图卷 + lumen 掩膜 + labels，估计逐 (aline, depth) 的衰减 μ 与每线代表值。
- 边界：不复制产品阈值；数值由合成数据标定；方法对应 att_paras 公开语义。

## 3. 数据模型
- 卷帧 f∈[0,F)，theta 线 a∈[0,T)，深度 z∈[0,D)（D=1025）
- 强度 A(f,a,z)（log 后，dB 已归一）
- 掩膜：lumen_b(f,a)∈[0,D)；media_end(f,a)≈常量/掩膜；label(f,a)∈{0(跳过),1(参与)}
- 输出：μ(f,a,z)（float 体，帧外层布局同宿主 miu_gray_array）；line_μ(f,a)=μ(f,a) 沿有效深度的稳健代表

## 4. 估计器（CPU 伪代码）
```python
MINWIN = 41            # 最小窗；窗口 < MINWIN/2 判无效
STEP_S = ceil(0.5*MINWIN); STEP_F = ceil(0.2*MINWIN)
SNR_MAX, NOISE = 0.25, 7
for f, a in all_alines:
    if label[f,a] == 0: μ[f,a,:]=0; continue
    z0 = lumen_b[f,a] + 1
    zend = min(media_end(f,a), D)
    if z0 >= zend: continue
    z = z0; best = None
    while z < zend:
        w = min(MINWIN, zend - z)
        if w < MINWIN/2: break
        # 取样本 A[f,a, z:z+w]
        seg = A[f,a, z:z+w]
        if max(seg) - min(seg) < NOISE:      # 无动态范围 → 噪声带
            z += STEP_F; continue            # 失败：小步前移（stepfail）
        # 束腰校正（可选）：对每个深度乘 G(z; z0,zR,zw)，再取 log
        slope = lstsq_fit(z:z+w, seg)        # 最小二乘斜率
        if valid(slope) and slope < 0:       # 衰减期望为负斜率
            μ[f,a, z:z+w] = -slope
            best = -slope; z += STEP_S       # 成功：大步推进（stepsucc）
        else:
            z += STEP_F
    line_μ[f,a] = robust_median(μ[f,a, valid]) or best or 0
```
- `G(z; z0,zR,zw)`：公开实现可**默认关**（几何调制），spec 说明与产品物理校正的差异。
- 复杂度：F×T≈2.7e5 条线 × O(D) 窗拟合 → CPU 慢、CUDA 每线一线程即快（W11 实现）。

## 5. 验收
1. 合成“已知 μ 的衰减介质卷”（μ=0.3/0.9/1.8 三带）→ 估计 μ 相对误差 <15%；
2. 带 lumen 掩膜下，估计仅在 lumen 外有效（管内 μ≈0/无效）；
3. 加噪声带（超过 NOISE）→ 对应深度被步进跳过，不产生伪 μ。

## 6. 合规声明（写进 SPEC 首行）
“本 SPEC 为教学复现，方法公开、数值自定义，与产品无等价关系；字段名参照公开头文件注释。”

## 7. DoD 打卡
- [x] SPEC（§3-6）可独立实现 + CPU 伪代码给出

## 明日预告
W10 REVIEW：字段/调用/SPEC 三件套归档（Week10/REVIEW.md）。
