# notes/whiteboard/ — 白板三件套练习

> 来源：Week16 Day03 任务。目的：把「会写代码」升级为「**无 IDE、限时、边说边写**」——这是面试核心场景。
> 用法：每次计时 30–45 分钟，先只读「题目」，在纸上/白板写；写完再对照「参考答案」与「易错点」。可录屏复盘流畅度。

## 三题一览

| 题目 | 时长 | 对应链 | 落点（OCTCudaCmake/src/kernels/） |
| --- | --- | --- | --- |
| [01_tile_transpose.md](01_tile_transpose.md) | 40 min | 链 A Transpose+Cut | `transpose_tile.cu` |
| [02_reduction.md](02_reduction.md) | 35 min | 链 B 批量统计 / IPA 归约 | `reduce_aline.cu` |
| [03_dsc.md](03_dsc.md) | 45 min | 链 A DSC（极→圆） | `dsc_polar2cart.cu` |

## 练习纪律

1. 每题**先只读「题目」节**，计时器开启，一气呵成（含画图：输入/输出布局）。
2. 完成后才翻「参考答案」；用红笔标差异（不是抄一遍）。
3. 每题末的「口述词」要**出声说一遍**——白板题考的是表述。
4. 月循环：见 `Week16/maintenance_plan.md`（白板三件套每月 1 轮限时）。

## 为什么是这三题
- **transpose**：测 shared memory / bank conflict / 合并访问，链 A 真实步骤；
- **reduction**：测 warp shuffle / 两级归约 / 大数组分块，链 B、IPA 通用模式；
- **DSC**：测坐标映射数学 + 逐像素逆映射 + 边界（越界写 0），链 A 标志性输出。

> 合规：练习仅用合成数据 + 公开算法，与 `VGPU_Process.dll` 内部实现无关。
