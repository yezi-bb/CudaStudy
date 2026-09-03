# Week06 / Day02 — 学习记录（源码填充版）

> 主题：全帧 FFT（Handle_All_Preview_data）+ 下载 U16（Get_All_FFT_data）→ 链 B 中段。

## 1. 今日目标（回顾）
理解“卷在 device 上一次性 FFT 并保持到 Get”，口述链 B 中段。

## 2. 真实声明与宿主调用

```cpp
// VGPU_Process.cuh L323-327
void VGPU_Handle_All_Preview_data(float ground_noise);   // 处理所有帧，生成 fft 数据（留 device）
void VGPU_Get_All_FFT_data(U16* all_denoising_data, int pullback_frame_sum, float ground_noise); // 下载 U16
```
宿主（ImageProcessingController.cpp L1203→1257→1272）：
```
L1203/1233   Set_Original_pullback_Data_To_GPU(...)   // 整卷 raw 上传
L1257        VGPU_Handle_All_Preview_data(0)          // 卷内批 FFT+denoising（device 内）
L1272        VGPU_Get_All_FFT_data(denoising_data, pullback_total_frame, 0) // U16 下载供分析/IPA
```

## 3. 链 B 中段（口述交付）
```
(前端) 实时回拉采集 → CPU ring（或直接 device ring）
回拉结束：Set_Original_...(整卷 raw, U16/U8Vivo)
→ Handle_All_Preview(批 FFT + 去噪, KeepDevice)
→ Get_All_FFT_data(U16 下载)  → 分析模块/IPA/保存
```
要点：**FFT 在设备侧一次性处理整卷**（550 帧 ×1000 线），比逐帧启动快（内核/plan 复用、帧间无 CPU 往返）；`Handle_All_Preview` 输出仍留 device，只有“确实要被分析/存储”才 Get 下载。

## 4. 开源 batch_fft_volume（实现要点）
- cuFFT `PlanMany` 维度扩展：把 `frames` 与 `alines` 合成 batch = `frames × alines`（每 aline N 点，同 Week03 plan，仅 batch 放大）——N 相同即可复用同一个 plan；
- 若 N/尺寸在帧间不一致（Vivo 用不同 points？）则分两个 plan；
- denoising：产品在 FFT 后做“去噪处理”（对应 `all_denoising_data` 命名）；open 端先实现 log+U16 输出与“去噪占位接口”（W08 检测类再细）；
- 下载 U16：一次 `cudaMemcpy`（卷连续）或按帧拷贝，看宿主使用布局（`frames × lines × half`，行主序）。

## 5. 缓冲区布局记忆
- 卷内每帧：`alines × (N/2+1)` 谱样本；
- 下载 buffer `all_denoising_data` 顺序 = 与预览/回放一致的 3D 布局 `[frame][line][half]`（与 GetGlobal 语义一致）。

## 6. 自测 Q&A
1. 为什么 FFT 批处理前必须先 Set_Original？（顺序）→ Handle_All 在**已有卷缓冲**的设备上执行；没上传就处理=空卷。
2. Get_All_FFT_data 为什么又传 ground_noise？→ 下载的是“去噪后 U16”，若该卷当初未指定去噪底噪，Get 时可再补（两处都能给底噪语义）。
3. KeepDevice 的价值再确认？→ 550 帧谱若每帧 D2H 再传回，浪费 ~2× 卷大小 PCIe；批处理后按需下载一次。
4. Handle_All_Preview 与逐帧 API 谁先有？→ 逐帧（实时）先有；卷批处理是“分析/预览”复用同一套 FFT 内核的批模式。
5. batch plan 复用条件？→ 仅当所有帧 alines×N 相同；不同回放数据可能不同 → 用 Layout key 缓存 plan。

## 7. DoD 打卡
- [ ] 能口述链 B 中段（§3）
- [ ] batch_fft_volume 与 CPU 小卷 diff 通过（§4）

## 明日预告
方图/圆图批渲染与校准裁剪。
