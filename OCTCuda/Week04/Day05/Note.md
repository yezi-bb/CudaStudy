# Week04 / Day05 — 学习记录（源码填充版）

> 主题：DSC 纹理优化（硬件双线性/归一化坐标）+ Week04 复盘。

## 1. 今日目标（回顾）
用 CUDA 纹理实现“采样即插值”，对比 naive 并量化收益；沉淀复盘。

## 2. 纹理方案思路
DSC 本质 = 对 rect（一张图）做**极坐标反向采样**，逐像素 `tex2D` 即可硬件完成线性插值/边界：
```cpp
texture<float, 2, cudaReadModeElementType> texRect;   // 或 cudaTextureObject_t
// 每像素: u = fc/raw_cols (0..1 归一化角度), v = fr/raw_rows
// normalized=true + 环状镜像/CLAMP 配合角度回绕（环形时用 u 的 fraction 手工 mod 更稳）
float val = tex2D(texRect, u, v);
```
- 纹理好处：硬件 2D 双线性、自动处理边界/寻址模式、数据驻留纹理缓存（空间局部性好）；
- 代价：整数纹理偏移、坐标归一化要小心 0.5/texel 对齐；
- 与 naive 对照同一合成 rect → 逐像素 diff（允许 ±1 LSB 量级差异，因硬件舍入与 floor 规则不同，采用 `fabs≤1e-2*max` 或 LSB 阈值）。

## 3. 实测表（自填）

| 版本 | 耗时/帧 | 相对 naive | 说明 |
| --- | --- | --- | --- |
| naive bilinear | ___ ms | 1× | Day04 |
| texture bilinear | ___ ms | _× | normalized=1, CLAMP |
| texture + 行合并/常量裁剪 | ___ ms | _× | 去掉 atan2（查表 tan/角度表）|

角度查表（可选优化）：把 `atan2 映射 → (cos,sin) 与 col` 做成 `LUT[W][H]`? 至少用 `__sincosf`；圆图固定 → 可预算每个像素的 (fr,fc) LUT 存常量/纹理，DSC 每帧只做取样 → 大提速（记录即可）。

## 4. Week04 REVIEW 底稿（抄进 `Week04/REVIEW.md`）

**API 范围**：`VGPU_Transpose(_CheckImage)`、`VGPU_DSC` + InterpolateType。
**核心结论**：
1. Transpose 深度裁剪 `[m_cut_start_point, m_cut_end_point)` 来自校准结果；CheckImage 不裁剪（0..AFT 全长）供造影/断裂检测（L534 / L762、794）；
2. DSC：极坐标 rect(深度×角度) → 704² 笛卡尔圆图；`inner_r/margin_r` 管内外环带；实时双线性（L625 INTER_BILINEAR）；
3. 映射公式：θ→col（回绕），r/dr→row（夹取）；坐标 LUT 化是最优结构；
4. shared-memory tile transpose + `TILE+1` padding 消除 bank conflict。
**收益句（简历可用）**：DSC/Transpose 在 704²×1000 线下从 X→Y ms；tile+pading 使 shared 冲突从 32 路→0。
**三个疑问（示例）**：dr 换算在 DLL 内如何与标定 mm/像素挂钩；`INTER_BITRIPLE` 何时启用；VGPU_Transpose 内部是 tile 还是只用裁剪+拷贝。

## 5. 自测 Q&A
1. 纹理坐标 0.5 对齐规则？→ texel (i) 中心位于 (i+0.5)/N（归一化），直接 i/N 会偏半像素——DSC 需减 0.5 校正或接受 ≤0.5px 偏移（用与 naive 的 diff 判断）。
2. 为什么说“先正确后优化”？→ 映射公式一个符号错全图翻转，纹理只是加速采样不改语义。
3. LUT 化的根本收益？→ atan2/sqrt 每帧 495k 次 → 一次预计算后每帧纯 tex2D（几何开销≈0）。
4. 圆图 704 是否必须 2 的幂？→ 不必；纹理尺寸任意，归一化寻址即可。
5. naive 与纹理差多少才算“加速成功”？→ 同输入同语义，主要看耗时降低比例与 diff 阈值内。

## 6. DoD 打卡
- [ ] 纹理版 DSC 完成并记耗时（§3）
- [ ] `Week04/REVIEW.md` 用 §4 底稿

## 明日预告
Week05：增强与伪彩色。
