# Week13 / Day05 — 学习记录（源码填充版）

> 主题：W13 REVIEW + 实时架构四问面试稿。
> 周复盘文件：`Week13/REVIEW.md`。

## 1. 本周回顾
D1 宿主 GPU 线程模型（CreateThread 常驻循环 + 标志 + 两级异常）→ D2 三职责分层（PipelineEngine/GpuWorker/State）→ D3 线程 vs Stream 与双流流水 → D4 开源状态机（非法顺序抛异常）→ D5 复盘。

## 2. 面试四问（对着镜子答）
### Q1 “你这个实时链的线程模型？”
“采集线程把原始帧放下置标志；一条常驻 GPU 线程轮询处理（Host 用 Win32 CreateThread + while(active)，进程内不每帧建线程），状态机决定该处理成预览帧还是回拉帧；结果在临界区里更新，UI 只读结果。任何一帧异常被 __except 吃掉，不让线程退。”
### Q2 “线程和 CUDA Stream 什么关系？”
“线程是 CPU 侧执行者，决定‘谁去调 GPU’；Stream 是 GPU 侧调度，决定 kernel 之间是否并发/乱序。宿主这类串行单依赖链默认流即可，流编排封装在算法库内；我在开源按帧间流水做双流+事件，先量化 fps 预算再决定流数。”
### Q3 “为什么状态机重要？”
“一批 GPU API 依赖‘前置缓冲已配/数据已到位’（Allocate 后才能 Stream，轮廓分析后才能 IPA）。状态机把‘当前允许的 API 子集’显式化，线程每轮查状态决定动作，非法顺序直接抛异常而不是晚点崩在 kernel。”
### Q4 “显存紧张时怎么办？”（横切，02 §L123）
“重计算前先 GetCurrentGPUMemory/Check_pullback_Data_memory 看预算；不足走 GetCudaErrorStatus 定位，D2H 后再 Reallocate_memory；严重故障 ResetCudaMemory 再 Allocate。重任务整体可取消，把显存让给实时采集。”

## 3. 学习点归档
| 主题 | 一句话 | 出处 |
| --- | --- | --- |
| 线程 | 常驻线程 + 轮询 + 两级异常，停用“清任务→退循环→关句柄” | GpuHandlingDataThreadController L396-491 |
| 分层 | 调度/算法/状态三职责分家 → 算法可单测 | W13D2 |
| Stream | 事件做流间依赖；串行链不滥用多流 | W13D3 |
| 状态机 | 允许子集显式化，非法即抛 | 02 L134-140 / W13D4 |

## 4. DoD 打卡
- [x] 四问对答流畅（Q1-Q4）
- [x] Week13/REVIEW.md 生成

## 明日预告
Week14：广度补齐（裁剪+圆图标尺+坐标映射/物理量纲：DSC/像素/标尺换算）与面试作品集缺口盘点。
