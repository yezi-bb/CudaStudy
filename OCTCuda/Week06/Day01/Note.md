# Week06 / Day01 — 学习记录（源码填充版）

> 主题：回拉显存自检 + 整卷原始数据上传（U16 / Vivo U8 双通道）。

## 1. 今日目标（回顾）
读透 `Check_pullback_Data_memory` / `Set_Original_pullback_Data_To_GPU`，估算整卷字节并开源 `PullbackVolume::upload`。

## 2. 真实声明与宿主调用

```cpp
// VGPU_Process.cuh L316-321
bool VGPU_Check_pullback_Data_memory();   // 为回拉检测数据分配/校验显存
bool VGPU_Set_Original_pullback_Data_To_GPU(int pullback_frame_sum, float ground_noise,
    double gain_multiplier, int offset_data,
    U16* h_Original_data_pullback, U8* h_Original_data_pullback_vivo);
```
宿主（行号已核对）：
- `MainWindowView.cpp` L1777：开始扫描前 `VGPU_Check_pullback_Data_memory()` + `VGPU_GetCudaErrorStatus()` 双保险；失败写 EventLog 并自动关机（L1826）。
- `GpuHandlingDataThreadController.cpp` L449：扫描线程启动前同样先 Check。
- `ImageProcessingController.cpp` L1203：整卷 U16 上传 `(pullback_total_frame, 0, 1, 0, all_raw_data, NULL)`；L1233：Vivo U8 上传 `(pullback_total_frame, 0, gain, offset, NULL, all_raw_data_vivo)`。
- 后续接 L1257 `VGPU_Handle_All_Preview_data(0)`。

## 3. 字节估算（DoD，公式 + 宿主变量对应）
```
volume_bytes = pullback_frame_sum × alines_per_frame × points_per_aline × bytes_per_sample
```
| 项 | 宿主来源 | 冠脉参考值 |
| --- | --- | --- |
| pullback_frame_sum | 调用参数（= 宿主 `pullback_total_frame`） | 550（55mm 档） |
| alines_per_frame | 采集定义（扫描线；按工程定义与 `GetGlobalScanLines/PullbackLines` 核对） | 需运行时确认 |
| points_per_aline | `GetGlobalPointsNumberPerLine()` | 2048 |
| bytes_per_sample | U16=2 / Vivo U8=1 | 2 |
```
例（假设 alines=497/帧）：550 × 497 × 2048 × 2B ≈ 1.12 GB；若 alines=1000 → ≈ 2.25 GB。
```
> 上传入口只给“总帧数 + 连续 host 缓冲”，DLL 按内部帧布局知道每帧宽高——open 端 `PullbackVolume::upload` 必须自带 `FrameLayout{lines,points}` 参数，避免隐式约定。

## 4. 上传策略（实现要点）
- 先 `Check_memory`：不只是在单次调用里 cudaMalloc，而是“分配/复用整卷 bulk buffer + 验 cuda 状态”，把失败前置到扫描开始前（避免扫完才爆显存）。
- H2D 可整块 `cudaMemcpyAsync`（若 DMA 缓冲连续）；否则分块（每帧一行一帧传），用 stream 与后续 FFT 重叠（W13 深入）。
- 双通道：U16 常规 / U8Vivo 用 `h_Original_data_pullback_vivo`，`gain/offset` 在校准侧同步（与 Week02 Vivo 同一换算）。
- 显存复用的关键：Check 时估算大小与**当前 GPU free 显存**（`VGPU_GetCurrentGPUMemory`）比对，返回 bool 给宿主决定是否继续。

## 5. 开源 PullbackVolume（骨架）

```cpp
struct PullbackLayout { int frames, alines, points; size_t bytes(bool vivo) const {...}; };
class PullbackVolume {
  DeviceBuffer d_raw_;            // bulk，首次按 layout.bytes() 分配后复用
  bool upload_volume(const uint16_t* u16, const uint8_t* u8vivo,
                     float gain, int offset, cudaStream_t s);
  bool check_memory(const PullbackLayout& L, float* free_gb);
};
```

## 6. 自测 Q&A
1. Check 为什么要“前置到扫描前”？→ 显存失败要在用户开始前暴露（UI 可拒），而不是采集整段后才崩。
2. 大卷上传为什么可能必须分块？→ 单次大 H2D 会占满总线且若设备缓冲不连续则无解；分块+stream 可与后续计算重叠。
3. 为什么 API 不用显式每帧尺寸？→ DLL 在 Allocate 已记录帧布局，宿主只需给连续缓冲+帧数；open 端要显式传 layout 以防隐式不一致。
4. Vivo 上传与 U16 上传的区别？→ 样本 1B 与换算参数（gain/offset）随卷记录，后续 preview/FFT 直接使用。

## 7. DoD 打卡
- [ ] 估算公式与宿主帧数变量对应（§3）
- [ ] `PullbackVolume::upload` 骨架（§5）

## 明日预告
全帧 FFT（Preview）与下载。
