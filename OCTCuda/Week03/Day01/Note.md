# Week03 / Day01 — 学习记录（源码填充版）

> 主题：FFT 功率与插值两套 API 的缓冲图与差异。

## 1. 今日目标（回顾）
精读 `VGPU_Get_FFT_Power_Result` / `VGPU_Get_FFT_Power_Interpolation_Result`，画出 windowed→complex→logpower 缓冲图，记清 `is_device_to_host`。

## 2. 真实声明（VGPU_Process.cuh L232-234 / L240-241）

```cpp
/*对加窗数据进行FFT变换和Log求和*/
bool VGPU_Get_FFT_Power_Result(DOCMotionType status, float* h_Power_data, float times, bool is_device_to_host);
bool VGPU_Get_FFT_Power_Interpolation_Result(DOCMotionType status, float ground_noise,
    float* h_Power_data, U16* h_interpolation_data, bool is_device_to_host);
/*对压缩后的数据取Log*/
bool VGPU_Get_After_Log_Result(DOCMotionType status, float* h_Log_data, bool is_device_to_host);
```

宿主真实调用（ImageProcessingController.cpp）：
- L521（实时）：`VGPU_Get_FFT_Power_Interpolation_Result(doc, 0, m_power_for_scan_data, m_interpolation_scan_data, false)` —— ground_noise 传 0；中间结果留 device。
- L735（回拉）：同上但用 `m_power_for_pullback_data / m_interpolation_pullback_data`。
- ExportOCTdataView.cpp L898 / L991：`(doc, 0, NULL, FFTData+offset, true)` —— **power 可传 NULL**（只取插值 U16，且拷回 host 供导出）。

## 3. 缓冲图（本日交付物）

```
 windowed aline   float[Ls][N]            (Week02 输出, device)
        │ cuFFT R2C (batch=Ls, 每线 N → N/2+1 复数)
        ▼
 complex aline    cufftComplex[Ls][N/2+1]
        │ power kernel: p[k]=|X[k]|^2 (或幅值)  + 去底(ground_noise)
        ▼
 power (f32)      h_Power_data[Ls][N/2+1]      ← _Power_Result 的 times/缩放应用点
        │ log + 缩放(times) + (插值压缩到 U16 输出域)
        ▼
 interpolation U16 h_interpolation_data[Ls][N/2+1] ← Interpolation 版本特供“圆图宽度”输入
        │ （实时链后续给 Transpose；本 API 内部已做压缩，无需再取 log 的浮点）
```

两 API 差异（可口述）：
- `_Power_Result`：只给浮点功率（可继续 `Get_After_Log_Result` 再 log，或 `times` 缩放）。
- `_Interpolation_Result`：一次给出“去底 + 功率 + 压缩成 U16 的插值谱”，实时链直接消费；`ground_noise` 去除底噪，`h_Power_data` 可 NULL（省显存/带宽）。
- `is_device_to_host`：实时链 false（留在 device 给 Transpose）；导出/重处理 true。

## 4. 记忆点
- cuFFT plan 应在 Allocate（初始化）时建好并复用：plan 按 `N`（点数/线）创建，与转速无关，不必每帧建。
- 每线 N 点实数 → 谱线长度 N/2+1（=1025 for 2048；GetGlobalPointsNumberPerLineAfterFFTlength() 即此值），是后来 width/裁剪的依据。
- “Log 求和”理解为：log 域功率谱是圆图亮度基础（视网膜/血管内 OCT 动态范围大，必须取 log 压缩对比度）。

## 5. 自测 Q&A
1. 实时链路为什么在 FFT 阶段就 D2H=false？→ 后续 Transpose/DSC 都在 device，避免来回拷贝。
2. `h_Power_data` 传 NULL 说明什么？→ 功率缓冲是“可跳过产物”，接口按需输出，是省带宽设计。
3. N/2+1 从哪来？→ 实数 FFT 的厄米对称，只存前半谱，DSC 圆图也只用有效深度谱段。
4. ground_noise 语义？→ 谱底噪/背景（反射噪声基线），减掉避免 log 后出现整体偏置与伪影；宿主通常传 0（按配置去 DC）。
5. 两 API 谁能直接喂 Transpose？→ `_Interpolation_Result`（U16，已经是“可显示/可转置”宽度谱）。

## 6. DoD 打卡
- [ ] IO 图完成（§3）
- [ ] 能解释两 API 差异（§3 口述）

## 明日预告
实现 cuFFT 的 FftLogStage（PlanMany + log_power kernel）。
