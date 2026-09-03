# Week03 / Day05 — 学习记录（源码填充版）

> 主题：`VGPU_Pullback_ProcessData_ToImage` 单帧捷径 + Week03 e2e 计时复盘。

## 1. 今日目标（回顾）
看懂回拉“融合 API”如何一次调用从原始帧到插值谱；把 window→fft→log 连成 e2e 并计时。

## 2. 真实声明与宿主用法

```cpp
// VGPU_Process.cuh L237-238
bool VGPU_Pullback_ProcessData_ToImage(U16* Original_data, U8* Original_data_vivo, int current_pullback_frame,
    float ground_noise, double gain_multiplier, int offset_data, U16* h_One_FFT_Power_data, bool is_device_to_host);
```
- ImageProcessingController.cpp L703-711 回拉循环：自研卡 `(NULL, vivo_buf, iframe, 0, gain, offset, ...)`；常规卡 `(orig_buf, NULL, iframe, 0, ..., ...)` —— **一实一空选源**。
- L742-743 随后 `VGPU_Get_Current_Frame_FFT_data(...)` 取当前帧用于拍照。

语义：单帧 raw →（内部）Resample+Window → FFT+去底/Log → 压缩 → U16 插值谱（`h_One_FFT_Power_data`）；即把 Week02/03 逐 stage 的调用**融合成一个“逐帧快捷入口”**。

## 3. e2e（开源：window→fft→log）计时表

```cpp
cudaEvent_t s,e; cudaEventCreate(&s); cudaEventCreate(&e);
cudaEventRecord(s); /* resampleWindowKernel */ /* cufftExecR2C */ /* powerLogKernel */
cudaEventRecord(e); cudaEventSynchronize(e);
float ms; cudaEventElapsedTime(&ms, s, e);
```
| Stage | ms/帧(2048×1000) | 说明 |
| --- | --- | --- |
| resample+window | 自填 | Week02 kernel |
| cuFFT R2C (batch=1000) | 自填 | PlanMany 复用 |
| power+log | 自填 | 可并进上面 kernel? |
| **合计(不计拷贝)** | 自填 | 目标 < 10ms/帧（实时 60fps 预算） |

验收：与 CPU golden 抽查 maxRel≤1e-3；`nsys profile` 确认三个 kernel 顺序与时长。

## 4. Week03 REVIEW 底稿（抄进 `Week03/REVIEW.md`）

**API 范围**：FFT_Power / FFT_Power_Interpolation / After_Log / Current_Frame_FFT(_After_Interpolation) / U16↔F32 / old_toLog / cutfront25 / Denoising_toLog / Pullback_ProcessData_ToImage。
**核心结论**：
1. 实数 FFT → 半谱 N/2+1；计算 F32、存盘 U16，量化需元数据(scale)；
2. 两套“功率”接口差异=是否内嵌压缩成 U16 插值谱（实时链直接用后者，L521/735）；
3. 旧档=Log 后+cut25 包袱；新版=denoising(Log 前)，导入分支 GpuHandling L908/947-952；
4. Pullback_ProcessData_ToImage 是“单帧 raw→U16 谱”融合入口。
**e2e**：window→fft→log 合计 `___ ms`。
**三个疑问（示例）**：Power_Result 的 `times` 是否即 log 缩放系数（未在宿主直接验证）；`Current_Frame_FFT` 与 `_After_Interpolation` 实际拍照用哪个（宿主两处都用前者）；产品 denoising 具体算法（外部模块，见 Week06）。

## 5. 自测 Q&A
1. 融合 API 对宿主的价值？→ 一次调用完成整条子链，少 3-4 次 launch/接口往返，回拉循环里省 CPU 编排。
2. 为什么还要保留逐 stage API？→ 实时帧/拍照/特殊路径要灵活（如 power NULL、Current_Frame 随时取）。
3. Open 端要不要做“融合 API”？→ 先顺序调 stage 模拟（契约等价），确认性能热点后再考虑 fused kernel。
4. 计时用什么不依赖墙钟？→ cudaEvent 在同一 stream 上测 GPU 时间，排除驱动/CPU 抖动。
5. 实时预算怎么算？→ 1000 线/帧×60fps ⇒ ≤16.7ms/帧总预算，FFT+重采样需 ≤ 个位数 ms。

## 6. DoD 打卡
- [ ] `Week03/REVIEW.md` 完成（用 §4 底稿）
- [ ] e2e window→fft→log 计时表已填（§3）

## 明日预告
Week04：Transpose / DSC（圆图重建）。
