# Week10 / Day05 — 学习记录（源码填充版）

> 主题：W10 REVIEW——字段/调用/SPEC 归档，进入实现周（W11）。
> 周复盘文件：`Week10/REVIEW.md`。

## 1. 本周交付物清单
| 产物 | 位置 | 内容 |
| --- | --- | --- |
| IPA 物理 | notes/W10_ipa_physics.md | 模型/规模/一句话 |
| att_paras 三配置 | notes/W10_att_paras.md | P60/P80/C7C8 全表 + 尺寸派生 + 新旧 API |
| 链 D 详细版 | 本日 Note §3（W10D3） | 10 实参来源与尺寸逐项 |
| μ 估计器 SPEC | W10D4 Note §3-6（落点 OCTCudaProject/oct/Ipa/SPEC.md） | 可独立实现规格 |

## 2. 关键“心智锁”（口述自检）
1. att_paras 两种字段：**物理量**（z0/zR/zw/SNR…）与**派生量**（step=ceil(比例×minwin)）——调参只调小集合。
2. 三套配置本质是“机型×数据类型”查表：P60/P80(vivo)、C7C8(竞品, isVivoData=false)。
3. 尺寸三兄弟：depth=1025(cols)、theta=500(rows)、alines=frames×theta；μ 体按**帧外层**布局。
4. 输入依赖链：lumen/labels 先由预处理得到（DicomModel.m_pre_ipa_analysed_result）→ 才有 IPA。
5. GPU 内存管理：μ 体 ≈1.1GB（550帧）→ 仅当尺寸变化才 delete/new（L207-216），避免每卷重复分配。

## 3. 合规复述
SPEC 首行声明“教学复现、不宣称等价”；数值（9.5/10.5/11 等）仅在私有笔记；对外不发布标定关系。

## 4. 实现周前检查（为 W11）
- [x] 已能默写三配置数值（私有限定）与字段语义
- [x] 已能画出链 D 数据流（FFT→lumen/labels→μ体+line_μ）
- [x] 已有 CPU 伪代码与验收标准（合成 μ 三带相对误差 <15%）

## 5. DoD 打卡
- [x] SPEC + 参数表 + 链 D 图齐全（Week10/REVIEW.md 索引）

## 明日预告
Week11：CPU/CUDA 实现 μ 估计器（逐 A-line 滑窗拟合 + 合成卷验收）。
