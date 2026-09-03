# Week13 / Day03 — 学习记录（源码填充版）

> 主题：线程 vs CUDA Streams——宿主用“线程”（Win32 单循环），开源补“流并行 + 双缓冲”实践。

## 1. 今日目标（回顾）
说清：Win32 线程 = CPU 侧“谁去调”；CUDA Stream = GPU 侧“kernel 排队/并发”。产品 DLL 内流管理不可见（黑盒），开源侧在 oct::E2E 演示多流 + 事件双缓冲。

## 2. 为什么宿主不需要“每帧一个流对象”
- 宿主链是**单串行数据依赖**（FFT→Log→Transpose→DSC→增强），天然按序 → 默认流串行即可保证正确；
- 线程解决的是“不与 UI/采集互卡”（CPU 侧并发）；流解决“GPU 内并行”，二者不同维度。
- 所以 GpuHandlingDataThreadController 里看不到 cudaStream——流的编排封装在 DLL 内核（黑盒），宿主只保证“单线程单数据流”的简单性。

## 3. 开源实践（oct::E2E，多流 + 双缓冲）
适合并行的点：**U16→F32 与 FFT 的卷拷贝**可与上一帧的 DSC/增强重叠（帧间流水线）。
```cpp
cudaStream_t s0, s1; cudaStreamCreate(&s0); cudaStreamCreate(&s1);
// 帧 k：H2D/D2H 走 s0；FFT/重采样主算走 s1（用事件让 s0 等待 s1 或反向）
for (int k = 0; k < nFrames; ++k) {
    // 流水：copy_in[k+1] 与 compute[k] 并行（双缓冲 ping-pong）
    cudaMemcpyAsync(d_in[cur], h_in[k+1], bytes, cudaMemcpyHostToDevice, s0);
    cudaEventRecord(ev, s0);
    cudaStreamWaitEvent(s1, ev, 0);          // s1 等 s0 拷完
    process_fft(d_in[cur] → d_out[cur], s1); // 重 kernel 在 s1
    cudaEventRecord(ev2, s1);
    cudaStreamWaitEvent(s0, ev2, 0);         // s0 等计算完再拷结果/下一帧输入
    cudaMemcpyAsync(h_out[cur], d_out[cur], bytes, cudaMemcpyDeviceToHost, s0);
    cur ^= 1;                                // 双缓冲切换
}
cudaStreamSynchronize(s1); cudaStreamSynchronize(s0);
```
要点：**事件做流间依赖**，而不是用 cudaDeviceSynchronize 全等（会毁掉并行）。

## 4. 什么时候不该多流（判断力）
- 数据依赖强、单帧耗时 ≈ 帧间隔 → 多流收益小，复杂度高；
- 帧间相互独立、逐帧流水 → 多流 + 双缓冲收益明显（本案例：批回拉帧间独立 → 可流水）。
- 量纲：fps 预算 = 1/帧时间；先量 kernel 耗时再决定流数（W05 强调“ms + fps”）。

## 5. 开源落点与自测
- 放 oct::E2E 的 `framepipe`：`FramePipe::run(s0, s1, frames)`；
- 自测：1000 帧合成 U16 卷，对比 单流 vs 双流总耗时（应缩短 ~20-40%）与数值一致性（逐像素 ==）；
- 记录 nsight/nvprof 时序截图到笔记（如无可跑工具，记录 CPU 计时 + kernel 分段计数）。

## 6. 面试一句
“产品里线程负责‘不要让 UI/采集卡住’，流是 DLL 内核的编排；我在开源演示里按帧间流水线做双流 + 事件同步，先算清 fps 预算再决定流数。”

## 7. DoD 打卡
- [ ] 双流流水 demo：总耗时下降且数值一致
- [ ] 能区分“线程解决的问题”与“流解决的问题”
