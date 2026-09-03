# Week12 / Day05 — 学习记录（源码填充版）

> 主题：15 分钟 IPA 口述稿 + W10-12 三周复盘。
> 产出：`Week12/talk_ipa.md`（讲稿）、`Week12/REVIEW.md`。

## 1. 讲稿结构（talk_ipa.md 大纲）
```
物理 → 参数 → Calculate → 圆图 → Update → 线程 → 合规与拓展
1. 一句话：IPA = 每 A-line 深度衰减 μ 拟合（脂质斑块可被识别）
2. 参数：att_paras 物理量 vs 派生量；P60/P80/C7 是“机型×数据类型”查表
3. Calculate（重）：FFT U16 + lumen/labels + media → μ 体 + line μ
4. 圆图：μ 方图走 DSC 量化成 uchar；单帧/全卷 = 帧偏移 + 写回
5. Update（轻）：line μ + 阈值 → 聚合(L/RangeMean/A/T) + colorbar
6. 线程：后台可取消 + SafeDicom 锁 + UpdateIpaValueSignal；Calculate 重/Update 轻拆两阶段
7. 合规：教学复现 ≠ 产品；参数黑盒
```

## 2. 三周复盘（W10-12 金句）
- W10：“先有 lumen/labels，才有 IPA”（预处理依赖）；参数只调小集合，其余派生。
- W11：“μ 体 ≈1.1GB，按帧外层布局”；单帧更新 = 一切按 frame 偏移取段。
- W12：“Calculate 一次重、Update 多次轻”= 响应式分析的标准拆分；显存争用三层缓解：监控→健康恢复→可取消。

## 3. 知识自检表（对着能讲）
| 你能讲清吗 | 覆盖 |
| --- | --- |
| att_paras 三种字段类型 | W10D2 |
| μ 估计=窗式对数斜率 | W10D4/W11D1 |
| 掩膜与 media=100 | W11D2 |
| 单帧 vs 全卷更新 | W11D5 |
| UpdateValueIPA 6 输出 | W12D1 |
| 两阶段拆分与线程 | W12D2/D3 |
| 显存争用故事 | W12D4 |

## 4. DoD 打卡
- [x] talk_ipa.md 按稿自讲一遍无明显卡壳
- [x] Week12/REVIEW.md 生成

## 明日预告
Week13：GPU 线程与 Streams（后台线程 → CUDA Streams/事件/双缓冲）。
