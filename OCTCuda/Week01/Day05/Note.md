# Week01 / Day05 — 学习记录（源码填充版）

> 吃透 `DOCMotionType` 与 `is_device_to_host`；本页含 Week01 复盘底稿（REVIEW 由你填写/上传）。

## 1. 今日目标（回顾）
① 弄清 motion 状态如何切换 device 缓冲与尺寸；② 弄清哪些阶段 GPU 结果留在 device、何时才 D2H；③ 完成周复盘。

## 2. 真实声明
- 枚举（VGPU_Process.cuh L109-114）：`typedef enum { DOC_SCAN=1, DOC_PULLBACK_BEFORE, DOC_PULLBACK_AFTER } DOCMotionType;`
- `is_device_to_host` 出现在各处理 API 末尾（如 `VGPU_DSC(...)` L266-267、`VGPU_Image_Enhancement(...)` L270-271、`VGPU_Transpose(...)` 等）；类型各异：多为 `bool`，个别为 `int`——只表达“最后一环输出是否拷回主机”，统一按 bool 语义理解。

## 3. 宿主实测：status 与 true/false 传参 ≥10 处（ImageProcessingController.cpp）

| 行号 | API | motion / 关键实参 | D2H 位 | 阶段 |
| --- | --- | --- | --- | --- |
| L340 | Resampling_For_Scan | `doc_motion_type`（回拉前采集段=SCAN 语义）+ `m_hanning_window_for_pullback_data` | false | 回拉补充采集 |
| L349 | Get_FFT_Power_Result | `m_power_for_pullback_data`, `m_coefficient_for_log` | **true** | 回拉段需要 host 谱 |
| L511 | Resampling_For_Scan | `m_hanning_window_for_scan_data` | false | 实时扫描加窗 |
| L521 | FFT_Power_Interpolation | `m_power_for_scan_data`, `m_interpolation_scan_data` | false | 实时 FFT+插值 |
| L534 | Transpose | `temp_cut_start/end_point`(裁剪) | false | 极坐标空间转置 |
| L625 | DSC | `cut 行数, g_scan_lines_number_`, 704×704, INTER_BILINEAR | false | 实时圆图 |
| L636/640 | Enhancement | 704×704, low/up_boundary, γ, Linear/Pow | false | 增强 |
| L651 | Gray2Color | `clolor_circle_mat`(cv::Mat) | **true** | 最后显示才 D2H |
| L725/735 | Pullback 加窗 / FFT | pullback 缓冲版本 | false | 整段回拉重建 |
| L779/813/838 | Transpose | 同 cut 参数 | false | 批量转置 |
| L849 | DSC | `g_pullback_lines_number_` | false | 回拉圆图 |
| L874 | Gray2Color | `cv::Mat::zeros(...CV_8UC3)` | **true** | 上色回显 |
| L951 | Gray2Color | 同 L874 变体 | true | 上色回显 |

> 规律：**中间计算全程 false（纯 device 内部流转）**；只有两处 true——需要 host 读谱的节点（L349）、以及最终形成 `cv::Mat` 显示的节点（L651/874/951）。另外 L706-711 `VGPU_Pullback_ProcessData_ToImage(NULL, vivo_buf, ...)/(orig, NULL, ...)` 用 NULL 选路区分 vivo 源与常规回拉源。

## 4. 记忆点
- `DOCMotionType` 决定 DLL 内部用**哪组缓冲/哪个长度维度**：SCAN=1000 线、PULLBACK_BEFORE=497 线补采、PULLBACK_AFTER=整段批处理（550 帧）。
- CopyPolicy 思路（开源）：`enum class Phase { Resample, FftLog, Transpose, Dsc, Enhance, Color };` 每阶段接口带 `CopyPolicy { StayDevice, ToHost }`，内部决定 kernel 后是否 `cudaMemcpy(D2H)`；**真实产品只在“需要宿主介入/显示”的点 D2H**，是性能关键（避免每帧全量拷贝）。

## 5. 链 A 前三步（口述答案）
```
① DMA 采集原始数据(环形 2000 线) → 取单帧 → Resample 重采样到规整半径 + 乘汉宁窗 (L511, false)
② FFT → 功率谱 + Log/插值压缩 → m_power_for_scan_data / m_interpolation_scan_data (L521, false)
③ Transpose 极坐标裁剪转置 → temp_cut_start..end 切片 (L534, false)
   ↓ 后续: DSC 704×704 圆图(L625) → 增强(L636) → Gray2Color 上色 D2H(L651)
```

## 6. Week01 REVIEW 底稿（可直接抄进 `Week01/REVIEW.md`）

**API 列表（周覆盖）**：Allocate/Free/SetFunctionConfig/SetCalibrationData/GetCudaErrorStatus/GetCurrentGPUMemory/ResetCudaMemory/Reallocate_memory + 链 A 上 VGPU_* 单帧链路。
**尺寸笔记**：环形 2000 行；Ls=1000；Lp=497；每线 2048（冠脉）/4096（颈动脉）；圆图 704×704；回拉 550 帧（55mm 规格）；去 DC 默认开。
**三个疑问（示例，建议替换成自己的）**
1. `noise_max_index/noise_width=0` 在不同 PIU 转速下何时非零？
2. Pullback 整段 buffer 是否真按 550×单帧显存规划？（待 Week06 批处理验证）
3. `VGPU_Reallocate_memory` 的触发者到底是哪个 DL 模块？（当前宿主无调用点）

## 7. 自测 Q&A
1. 为什么实时主路径中间不 D2H？→ 数据流全在 device 内，D2H 只会增加 PCIe 带宽与拷贝延迟，只有“宿主读/显示”才拷贝。
2. Gray2Color 后为什么 true？→ 输出要进 `cv::Mat`（OpenCV 在主机侧）做 UI 显示/录像，必须回拷。
3. DOC_SCAN 与 DOC_PULLBACK_BEFORE 区别在宿主侧体现为什么？→ 同一 Resample 函数但传入不同 motion 与不同窗缓冲（scan 窗 vs pullback 窗），DLL 按 motion 选内部尺寸。
4. 裁剪 cut_start/end 在哪一步？→ Transpose 前由 FFT 后有效深度决定（对应 DSC 只画有效半径）。
5. `CopyPolicy` 在开源仓里的作用？→ 把“何时拷贝”显式化：阶段接口参数化，宿主按需传 `ToHost`，避免每 kernel 硬编码。

## 8. DoD 打卡
- [ ] `Week01/REVIEW.md` 已写（用 §6 底稿）
- [ ] 能默述链 A 前三步（§5）
- [ ] 开源仓出现 CopyPolicy（Day04 工程中加入 `copy_policy.h`）

## 明日预告
进入 Week02：重采样与窗函数。
