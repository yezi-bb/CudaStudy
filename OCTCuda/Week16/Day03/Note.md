# Week16 / Day03 — 学习记录（源码填充版）

> 主题：限时手写 tile transpose / reduction / DSC——把「会写」升级为「无 IDE 白板能写、边说边写」。

## 1. 今日目标（回顾）
三题各 30–45 分钟模拟白板：先只读题目计时写，再对照参考答案与易错点；每题末出声练「口述词」。

## 2. 白板三件套（notes/whiteboard/）
| 题目 | 时长 | 考点 | 落点 kernel |
| --- | --- | --- | --- |
| `01_tile_transpose.md` | 40 min | shared tile、padded 防 bank conflict、块索引↔输出维度 | `transpose_tile.cu` |
| `02_reduction.md` | 35 min | warp shuffle、两级归约、每线程 4 元素 ILP、atomicAdd | `reduce_aline.cu` |
| `03_dsc.md` | 45 min | 极→直逆映射、atan2 平移 +π、越界写 0、双线性回绕 | `dsc_polar2cart.cu` |

## 3. 从链 A/B/D 反推「为什么考这三题」
- **transpose（链 A）**：W04 实步骤；考 shared/合并访问，能引出「读 tile 写 tile、块内一次同步」；
- **reduction（链 B / IPA）**：批量 A-line 与 μ 体数据都做窗统计；考 shuffle 与块间汇总，最常被追问；
- **DSC（链 A 标志输出）**：704² 每像素一线程的 gather 逆映射；考数学推导 + 边界，最能体现影像功底。

## 4. 各题最大翻车点（复盘记录）
- transpose：`out` 是 `[N][M]`，blockIdx.x 按 N 铺网格——写反则越界/花屏；
- reduction：忘 host 先 `cudaMemset(out,0)`、shared 数组写成 `BLOCK` 而非 `BLOCK/32`；
- DSC：`atan2` 负半圈不 +π、col 换列不取模、float rowf 提前转 int 丢小数边界。

## 5. DoD 打卡
- [x] 三题均能限时写完（对照答案自查，差异标红）
- [x] 白板稿落 `notes/whiteboard/`（文本版；可后续补照片）

## 明日预告
投递名单：`apply_list.md`（≥15 家/方向 + 每家主打故事标签）。
