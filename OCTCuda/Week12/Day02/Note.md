# Week12 / Day02 — 学习记录（源码填充版）

> 主题：「改阈值 → Update → UI」线程与信号全链；Calculate 重 vs Update 轻的拆两阶段动机。

## 1. 今日目标（回顾）
画序列图（notes/W12_ipa_threads.md）；说明后台可取消、DicomModel 加锁、异常过滤；论证“Calculate 重、Update 可反复”。

## 2. 两条触发路径（真实宿主）
### 路径 A：后台线程 BackgroundIPAUpdateThreadController::UpdateValueIPA（L856-913）
```
用户改阈值(UI) ──> pre_ipa.threshold 更新
  └> 后台(工作线程) 调 UpdateValueIPA:
     ① is_stop_thread_ 退出门（L860）
     ② SafeDicom unique_lock 锁住模型（L872）
     ③ Reset() 上次结果（L874）+ malloc 6 路输出（L879-884）
     ④ VGPU_UpdateValueIPA(line_ipa_miu,…,pre_ipa.threshold, 各输出)（L886-891）
     ⑤ 成功 → emit UpdateIpaValueSignal()（L896）
     ⑥ UpdatePostResultData() → 渲染线程用新结果重绘（L903）
  异常 __except(ExceptionFilter,"BP") 统一收口（L909）
```
### 路径 B：IPAZoneController::UpdateWhileThresholdChange（L124-162）
前向 UI 直接驱动（如轮廓改动连带 UpdateImagesWhileICAContourChange → L113-114 先改帧 μ 再 UpdateWhileThresholdChange），同步小路径。

## 3. 线程与取消要点（学习）
| 机制 | 宿主落点 | 为什么 |
| --- | --- | --- |
| 退出门 `is_stop_thread_` | L860/936/957（每次调用点查一次） | 关闭窗口/换卷可立即停，不跑残余帧 |
| 模型锁 `SafeDicom unique_lock` | L872-873 | 多线程共享 DicomModel，防撕裂 |
| 结果 Reset + 重 malloc | L874-884 | 尺寸可能变（换卷），先清后配 |
| 结构化异常过滤器 | “BP”（后台线程）/“PBL” | GPU/分配异常不跨线程传播 |
| 完成后信号 | UpdateIpaValueSignal | 渲染线程只消费“最终结果”，不锁算法 |
| 退后台标记 | is_ipa_update_in_backgroud_thread_quit_（IPAAlgorithmController L249-252） | IPA 内部也感知线程取消，主动 return |

## 4. Calculate（重）vs Update（轻）——拆两阶段的理由（口述）
- **Calculate**：输入 FFT 卷 + lumen/labels → 输出 μ 体(≈1.1GB/550帧)+line μ。算 μ 拟合（逐 A-line 滑窗），秒级、占显存大，且依赖轮廓分析结果（预处理完成后跑一次）。
- **Update**：输入**已缓存的 line μ** + 标量阈值 → 只做统计聚合 + LUT 上色。无重拟合、无大缓冲，毫秒级，可被 UI 反复触发（拖动阈值实时预览）。
- 因此产品分成两个 API：**一次重算，多次轻更新**——避免“拖一下阈值就重算 2.8 亿样本”。

## 5. 开源拆两阶段（oct::Ipa，对照设计）
```cpp
// 阶段1：重（仅当卷/轮廓变化）
void ipa_calculate(const VolumeFFT& vol, const Mask& lumen, const Mask& labels, Params p, Buffers& out); // → line_mu + mu_vol
// 阶段2：轻（阈值/模式变化时反复调用）
void ipa_update(const std::vector<float>& line_mu, int frames, double thr, double px, UpdateOut& out);
// UI 侧 = QThread + isStop 标志 + 信号 UpdateDone(QImage)，对照 BackgroundIPAUpdateThreadController
```

## 6. 自测
1. 画出两条路径序列图并标注每个锁/信号（见 notes/W12_ipa_threads.md）；
2. 想一个“用户连拖 10 次阈值”场景：为何轻 Update 能跟上而重 Calculate 不行？

## 7. DoD 打卡
- [ ] notes/W12_ipa_threads.md 序列图完成（含锁/信号/取消点）

## 明日预告
开源简化 ipa_update：line_mu>thr 着色 + 帧聚合 IPA_L + 示意 colorbar。
