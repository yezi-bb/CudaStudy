# Week02 / Day04 — 学习记录（源码填充版）

> 主题：Vivo 与 Pullback 两个“亲戚接口”的宿主分支与 Open 端复用。

## 1. 今日目标（回顾）
搞清三入口：`_For_Scan`、`_For_Scan_Vivo`、`_For_Pullback` 各服务于哪条硬件/流程，并验证 Vivo 的 U8 换算。

## 2. 宿主真实分支（ImageProcessingController.cpp / ExportOCTdataView.cpp，行号已核对）

```cpp
// L503-506 实时：自研采集卡(Vivo U8) vs 常规卡(U16)
if (GetGlobalIsSelfInnovateCard()) {
    VGPU_Data_Resampling_For_Scan_Vivo(doc_motion_type, GetGlobalGainMultiplier(),
        GetGlobalOffsetData(), original_data_buffer_for_one_frame_vivo,
        this->m_hanning_window_for_scan_data, false);          // U8 路径
} else {
    VGPU_Data_Resampling_For_Scan(doc_motion_type, ...scan_data..., m_hanning_window_for_scan_data, false); // U16 路径
}
// L717-720 回拉段内：同样自研卡走 Vivo
// ExportOCTdataView.cpp L983：导出重处理历史数据也走 _Vivo，且窗口传 NULL(默认窗)
```
另：回拉批处理入口 `VGPU_Pullback_ProcessData_ToImage(NULL, vivo_buf, iframe_num, 0, ...)` 以 `NULL` 占位让 DLL 区分源（L703-711）：`NULL + vivo` = U8 源；`orig + NULL` = U16 源。

## 3. Vivo 换算与 kernel 增补

`_Scan_Vivo` 语义推断：对每条线
```
v = (float)rawU8[l*N+k];            // U8 原始
v = (v - offset_data) * gain_multiplier;   // 光强线性化（注意类型/溢出，host 只传 double 与 int）
f = calib位置(k)  -> 插值；         // 与 Scan 相同几何处理
out = 插值结果 * w[k];
```
Open 端方案：把 `InputKind` 加入统一入口：
```cpp
enum class InputKind { U16, U8Vivo, U8Plain };
template<InputKind K> struct InScale;   // U16: 1.0f; U8Vivo: gain,offset
```
kernel 里通过 `if constexpr/分支` 处理换算与位深，避免三个重复 kernel。

## 4. Pullback 批量（frame_sum）
- 语义：一次调用处理 `frame_sum` 帧的 Resample+Window（DLL 内部按状态决定缓冲起点/长度，逐帧或批量内核）；
- 宿主主要走 `Pullback_ProcessData_ToImage`/逐帧循环实现整段重建；`_For_Pullback` 是更原子的“批量重采样”接口（宿主极少直调，属导出冗余/扩展接口）。
- Open 复现：封装 `resampleWindowFrame(raw, out, N, Ls, w)`，在 host 层 for frame 循环或 `cudaMemcpy2D`/批量 grid（`gridDim = frames*(Ls/…)`）二选一；先“逐帧循环对 golden”，再优化为批量（Day05 观察带宽）。

## 5. 对照验收（三路均应与 CPU golden 一致）
| 模式 | 输入 | 期望 |
| --- | --- | --- |
| U16 identity | 合成 U16 | out==raw*w |
| U8Vivo identity | 合成 U8 + (gain,offset) | out==((u8-offset)*gain)*w |
| Pullback（frame_sum=3） | 3 帧串 | 等于逐帧调用结果的拼接 |

## 6. 自测 Q&A
1. 自研卡为什么要 gain/offset？→ 其光电前端输出 U8，真实光强=线性搬移；不做会在对数谱引入非线性。
2. 窗口指针 NULL 的语义在复现端怎么做？→ 提供“默认窗”常量（如内置 Hann 数组），`nullptr`→默认。
3. `VGPU_Pullback_ProcessData_ToImage(NULL, ...)` 两个数据指针为何一空一实？→ 用指针选中源类型（U8Vivo/U16），避免再加枚举参数。
4. frame_sum 复用同一个 host 窗数组吗？→ 是，窗只与 k 有关，与帧号无关。
5. 批量与逐帧在显存上有何差异？→ 批量需整段帧集显存（或分块），逐帧只需单帧缓冲；产品为兼顾实时回放用批入口+内部池。

## 7. DoD 打卡
- [ ] Vivo U8 换算 + Pullback 3 帧批量通过 diff（§5 表）

## 明日预告
性能观察：profile 重采样 kernel。
