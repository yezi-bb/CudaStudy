# Week14 REVIEW — 广度补齐

## 1. 周产出
| 日 | 主题 | 交付 |
| --- | --- | --- |
| D1 | 导入矩阵 | notes/W14_import_matrix.md（cuh L336-352 四入口 + OneFrame 单帧主路径 L217/593/1251/3871） |
| D2 | 缩略/导出子集 | notes/W14_thumbnail_subset.md（RecordingThumbnailView L4786-5065） |
| D3 | NVAPI 温度/显示 | notes/W14_nvapi.md（GpuController L45-79 / SystemDiagnosticsView L107-207 / ServiceView L210-240） |
| D4 | VTK 体绘制 | notes/W14_vtk.md（ThreeDimensionsImageController L17-38/70-90） |
| D5 | 复盘 + P0 缺口 | 本 REVIEW §2 |

## 2. 三句要点
1. 导入/导出/缩略全部复用“同一成像链”，差别只在入口适配与出口编码（ImportAdapter/Exporter）。
2. compute(VGPU/CUDA) vs display(NVAPI) vs 渲染(VTK/GL) 是三个不同 GPU 占用方，共卡需统一记账（W12 Context）。
3. P0 知识全覆盖；W15 动作 = 把 16 周笔记的 cpu_* 片段落入 OCTCudaProject 并跑绿 DoD。

## 3. P0→W15 执行表
（详见 Week14/Day05/Note.md §2：14 项 P0 每项含 状态/出处/落点）

## 4. 下周（W15）
按 gap list 落地源码：每模块 oct::Xxx 合成数据验收 + 端到端 demo + README/演示页 + 作品集归档。
