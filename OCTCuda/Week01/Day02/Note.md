# Week01 / Day02 — 学习记录（源码填充版）

> 用途：对照 TASK 精读显存生命周期 API，边读边自查。
> 路径约定：`E:\CUDA\source\` = 公司仓本地镜像；引用的行号均已在本机核对。

## 1. 今日目标（回顾）
精读显存生命周期 API（Allocate / Free / SetFunctionConfig / SetCalibrationData），建立「管线先分配再算」的内存模型。

## 2. 真实声明（VGPU_Process.cuh，region「参数配置与显存分配」L181-222）

```cpp
// L183-185
bool VGPU_Allocate_Parameter_Manager(int current_piu_speed, int noise_max_index, int noise_width,
    int original_data_buf_lines_number, int scan_lines_number, int pullback_lines_number,
    int points_per_aline, int image_height, int image_width, int pullback_total_fram_numer,
    float* calibration_data);
// L188
void VGPU_SetFunctionConfig(bool is_need_remove_dc);
// L191
bool VGPU_SetCalibrationData(float* calibration_data, int points_per_aline);
// L209
bool VGPU_Free_Parament_Manager(bool isfree_CalibrationConfig);
```

## 3. 宿主真实调用（ImageProcessingController.cpp）

| 宿主函数 | 行号 | 实参 → 含义 |
| --- | --- | --- |
| `CpuAndGpuMemoryAllocation()` | L229-231 | `speed=GetGlobalCurrentPiuSpeed()`；`noise_max_index=0, noise_width=0`（示例设备未用）；`g_original_data_buf_lines_number_=2000`（DMA 环形缓冲线数）；`g_scan_lines_number_=1000`；`g_pullback_lines_number_=497`；`m_gpu_imagme_points_number_per_line=2048`(冠脉)/4096(颈动脉)；`image_height=image_width=704`；`pullback_total_fram_numer=g_pullback55_total_frams_number_=550`；`calibration_data=m_calibration_data` |
| `CpuAndGpuMemoryAllocation()` | L233 | `VGPU_SetFunctionConfig(GetGlobalIsNeedRemoverDc())` → 默认开“去 DC/底噪” |
| `SetGpuCalibrationData()` | L98-116 | 神经颈动脉取 `GetGlobalCalibrationDataZ()`，否则 `GetGlobalCalibrationData()`，再 `VGPU_SetCalibrationData(calib, GetGlobalPointsNumberPerLine())` |
| `CpuAndGpuMemoryRelease()` | L245 起 | 释放顺序：Mat/CPU 缓冲 → `VGPU_Free_Parament_Manager(...)`（`isfree_CalibrationConfig` 语义见下） |

CPU 侧同尺寸 malloc 可作“device 缓冲草图”参照（L194-224）：
- scan 汉明窗：`1000 × 2048 × sizeof(float)`
- scan FFT power：`1000 × (2048/2+1) × sizeof(float)`
- scan 插值 U16：`1000 × (2048/2+1) × sizeof(U16)`
- 回拉（pullback）同 scan 三份但行数 497；DSC：`704×704×float`；增强：`704×704×uchar`

## 4. 记忆点

- **Allocate 输入 = “全部形状参数”**：转速（决定单帧 DMA 长度/插值参数）、缓冲线数（环形）、每线点数（FFT 长度）、圆图尺寸、回拉总帧数（一次性为整段回拉预分配 + 预留 cufft plan）。
- **SetCalibrationData 何时用**：运行时更换标定表/模式（神经 vs 冠脉）可热更；Allocate 里的 `calibration_data` 是首次分配时一起上传。
- **SetFunctionConfig**：管线级布尔开关（去掉 DC 分量 = 去底噪）。
- **Free 的 bool 参数**：`isfree_CalibrationConfig=true` 表示连标定配置显存一并释放；若仅临时释放计算缓冲而想保留标定表，则传 `false`（对偶于 Reallocate 语义，见 Day03）。
- 所有 buffer 均可由 `cudaMalloc/cudaFree/cudaMemcpy(H2D)` 对应，重写时用 RAII。

## 5. Device Buffer 估算练习（答案参考，冠脉 2048 例）

| # | buffer | 估算公式（约值） |
| --- | --- | --- |
| 1 | 原始数据环形 raw | `2000(环形线) × 2048 × 2B ≈ 8.2 MB` |
| 2 | 单帧加窗输入 raw_frame | `1000 × 2048 × 2B = 4.096 MB` |
| 3 | FFT 复数 in/out（cufft） | `1000 × (2048/2+1) × 8B ≈ 8.2 MB`（实部虚部） |
| 4 | Power 谱（去 DC 后） | `1000 × 1025 × 4B ≈ 4.1 MB` |
| 5 | 插值压缩 U16 | `1000 × 1025 × 2B ≈ 2.05 MB` |
| 6 | DSC 圆图 float / 增强 uchar / 上色 | `704×704×(4+1+3)B ≈ 3.9 MB` |
| 7 | 回拉批处理全集（FFT 各帧结果） | `550 帧 × 单帧 power ≈ 2.26 GB?` —— 错！批处理只放大内存，实际按“帧池/两段式”分批；这正是 `pullback_total_fram_numer` 进 Allocate、且 DLL 用统一池管理的原因（对比 01_API 文档 §1 的回拉缓冲说明） |

> 说明：公式先按 CPU malloc 的“尺寸结构”逐项列出；回拉“整段”显存按 `handle_all_*` 的批处理语义理解，而非简单 550×单帧叠乘（见 02_数据流 链 B/D）。

## 6. 练习：为什么回拉帧数要进 Allocate？（口述答案）
回拉处理要把整段（最多 550 帧，环形更早帧须保留）原始数据在 GPU 侧连续处理、还要支持“一边扫一边算”与回放；提前按最大帧数分配可避免运行中 `cudaMalloc` 抖动/失败、便于 55mm 规格一次性算 FFT 与后续批量分析；同时 Allocate 也可一并建好 cufft plan（plan 与长度绑定）。

## 7. 自测 Q&A
1. Allocate 参数中 `original_data_buf_lines_number` 与 `scan_lines_number` 差别？→ 前者=采集 DMA 环形缓冲（2000 行，保留未处理数据），后者=单帧输出线数(1000)。
2. SetCalibrationData 传 `points_per_aline` 干嘛？→ 让 DLL 判断该标定表是否匹配当前采样点数（2048/4096），不匹配则无法正确索引每线校正表。
3. SetFunctionConfig 为什么是“bool is_need_remove_dc”？→ 成像/回拉通常需要去 DC，但造影剂等特殊采集想保留原始谱做差异，故做成开关。
4. Free 传 true/false 分别回收什么？→ true=连标定配置一起释放；false=保留标定配置，适合重开成像不重传标定的场景。
5. 何时 SetCalibrationData 早于 Allocate？→ 首次启动流程中先读标定文件（`GetCalibrationFileData()` L122-164 读 `Calibration.txt`），再 Allocate。

## 8. 疑点 / 待办
- `noise_max_index / noise_width=0` 在哪些转速/设备上非 0？→ Week02/03 重采样与 FFT 时再验证。
- DLL 内部是否真的用 cufft plan 预建：从 API 无 plan 参数看是内部持有，重写时用 `cufftPlan1d` 复现。

## 9. DoD 打卡
- [ ] 写出 ≥6 类 device buffer 估算公式（§5 对照）
- [ ] 能解释回拉帧数为何进入 Allocate（§6 口述）

## 明日预告
错误状态、显存查询、Reallocate / Reset。
