# Week12 REVIEW — IPA 更新与线程

## 1. 周交付物
| 日 | 主题 | 产出 |
| --- | --- | --- |
| D1 | UpdateValueIPA 参数→输出→UI 对照表 | Day01 Note §3 |
| D2 | 改阈值→Update→UI 线程与信号 | notes/W12_ipa_threads.md（序列图） |
| D3 | 开源简化 ipa_update | 阈值着色+帧聚合+colorbar（改阈值即时色图变化） |
| D4 | 显存争用与缓解 | 三层缓解 + Context allocator 草图 |
| D5 | IPA 口述稿 | Week12/talk_ipa.md |

## 2. 核心事实
- VGPU_UpdateValueIPA（cuh L478-480）：输入 InlineIPA=line_ipa_miu；输出 IPA_L/RangeMean(double[frames])、IPA_A(float[alines])、IPA_T(uchar[1250×frame_lines×3])、A/L colorbar。
- 宿主两处：BackgroundIPAUpdateThreadController L886-891（后台线程+UpdateIpaValueSignal L896）、IPAZoneController L148-153（同步短路径）。
- 线程纪律：is_stop_thread_ 退出门、SafeDicom 锁、__except("BP"/"PBL")、is_ipa_update_in_backgroud_thread_quit_。
- 显存监控：IPAAlgorithmController L203/248/378/420 + helper L534-547；BackgroundIPA L833-842。

## 3. 掌握清单（口述）
- [ ] Update 与 Calculate 的“重/轻”与拆两阶段动机
- [ ] 6 路输出缓冲尺寸与宿主字段一一对应
- [ ] 线程序列图（锁/信号/取消点）
- [ ] 显存争用三层缓解故事
- [ ] 简化 ipa_update 改阈值即时生效

## 4. 下周（W13）预告
GPU 线程与 CUDA Streams：后台线程抽象 → 多流并发/事件同步/双缓冲；对照宿主 GpuHandlingDataThreadController / BackgroundIPAUpdateThreadController 的线程模型。
