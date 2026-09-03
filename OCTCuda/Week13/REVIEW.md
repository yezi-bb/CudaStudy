# Week13 REVIEW — GPU 线程与 Streams（实时架构）

## 1. 周产出
| 日 | 主题 | 交付 |
| --- | --- | --- |
| D1 | 宿主线程模型解剖 | 线程生命周期图（L396-491） |
| D2 | 三职责分层重构 | oct::PipelineEngine + GpuWorker + PipelineState |
| D3 | 线程 vs Streams | 双流流水 demo + 事件同步 + fps 预算判断 |
| D4 | 开源状态机 | oct::PipelineState（Idle…Freed，非法抛异常） |
| D5 | 四问面试稿 | Q1-4 复盘（线程/流/状态机/显存横切） |

## 2. 宿主源码锚点
- GpuHandlingDataThreadController.cpp L396-423（线程函数）、L445-491（Start/Release）、分发 ~L150-280
- 状态机规格：02_数据流与调用链.md L134-140
- 显存横切：02 §L123-129；GlobalConstantValueBase / 各 Controller

## 3. 掌握清单
- [ ] 常驻线程 + 标志轮询 + 两级 __except("CJ") 模式
- [ ] 优雅停止三序（清任务→退循环→关句柄）
- [ ] 调度/算法/状态三职责 → 算法可脱离线程单测
- [ ] 线程=CPU 谁去调；Stream=GPU 怎么排；事件=流间依赖
- [ ] 状态机 = “允许的 API 子集”显式化；非法顺序抛异常

## 4. 下周（W14）预告
广度补齐：裁剪/圆图标尺/坐标映射与物理量纲（像素↔mm↔角度），作品集缺口盘点。
