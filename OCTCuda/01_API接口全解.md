# 01 — VGPU_Process.cuh API 接口全解

> 源文件：`Algorithm/vgpu/include/VGPU_Process.cuh`  
> 说明：DLL 导出接口。下列「如何实现」指**开源复现时的合理 CUDA 拆分**，非断言闭源内部实现。  
> 宿主「谁调用」以当前工程常见路径为准，便于精读。

---

## 0. 全局约定

### 0.1 `is_device_to_host`

几乎所有成像阶段末尾都有该布尔参数：

| 值 | 含义 |
|----|------|
| `false` | 结果留在 Device；供下一阶段 kernel 接着用（实时主路径） |
| `true` | 本阶段结束后 D2H，供 UI / 存盘 / OpenCV `Mat` |

**实现要点：** 开源仓用 `enum class CopyPolicy { KeepDevice, ToHost }`；KeepDevice 时跳过 `cudaMemcpy`。

### 0.2 `DOCMotionType`

| 枚举 | 含义 | 典型缓冲 |
|------|------|----------|
| `DOC_SCAN` | 实时扫描 | 单帧 scan buffer |
| `DOC_PULLBACK_BEFORE` | 回拉进行中 | 帧序列写入中 |
| `DOC_PULLBACK_AFTER` | 回拉结束 | 全卷已在 GPU 或 Host |

同一套 kernel，不同 status 切换**不同的 device 指针 / 尺寸**（Allocate 时已按 scan/pullback 线数分配）。

### 0.3 常量（头文件）

| 符号 | 值/含义 | 实现启示 |
|------|---------|----------|
| `BLOCK_DIM` | 256 | 1D kernel 默认 block |
| `WARPSIZE` | 32 | reduce / shuffle |
| `COLOR_LEVEL` | 256 | LUT 伪彩 |
| `EPS` | 极小量 | log 保护 |
| `VALID_R` / `ALINE_BAND_*` | 校准/检测几何带 | 校准与造影剂算法 |

### 0.4 关键结构体 `att_paras`（IPA）

| 字段 | 典型来源（宿主） | 含义（工程语义） |
|------|------------------|------------------|
| `z0,zR,zC,zw` | P60/P80/C7 配置分支 | 衰减拟合 / 窗口几何相关参数 |
| `SNRmax,noise_level` | 同上 | SNR / 噪声门限 |
| `minwin` | 41 或 46 等 | 最小拟合窗口 |
| `stepsucc/stepfail` | 0.5 / 0.2 | 窗口步进比例 |
| `step_success/fail` | `ceil(ratio*minwin)` | 整数步进 |
| `scandepth` | 约 5 mm | 扫描深度 |
| `number_frames` | 总回拉帧 | |
| `number_depths` | FFT 后每线点数（如 1025） | |
| `number_theta` | 每帧线数（如 500） | |
| `number_alines` | frames × theta | 全卷 A-line 数 |

---

## 1. Region：参数配置与显存分配

### `VGPU_Allocate_Parameter_Manager`

| 项 | 内容 |
|----|------|
| **功能** | 按 PIU 转速、线数、每线点数、圆图高宽、回拉总帧、标定数据，**一次性分配**后续管线所需 GPU 缓冲与计划（含 cuFFT plan 等，推断） |
| **输入** | `current_piu_speed`, `noise_*`, `original/scan/pullback_lines_number`, `points_per_aline`, `image_h/w`, `pullback_total_fram_numer`, `calibration_data` |
| **输出** | `bool` 成功与否；副作用：全局 Device 状态 |
| **宿主** | `ImageProcessingController` 初始化路径 |
| **如何实现** | 类 `PipelineContext`：`cudaMalloc` 多缓冲 + `cufftPlanMany`；标定表拷入 `const`/`device`；按最大 pullback 帧预留 bulk buffer |
| **精读任务周** | W01 |

### `VGPU_SetFunctionConfig`

| 项 | 内容 |
|----|------|
| **功能** | 开关：是否去直流/底噪（`is_need_remove_dc`） |
| **如何实现** | 全局 flag；在 FFT/Log 前 kernel 里减均值或减噪声底 |

### `VGPU_SetCalibrationData`

| 项 | 内容 |
|----|------|
| **功能** | 更新光谱标定/λ 映射用浮点表 |
| **如何实现** | H2D 到 `d_calib[points_per_aline]`；重采样 kernel 读取 |

### `VGPU_Free_Parament_Manager`

| 项 | 内容 |
|----|------|
| **功能** | 释放参数管理器；`isfree_CalibrationConfig` 控制是否连标定配置一起释放 |
| **如何实现** | `cudaFree` + `cufftDestroy`；注意与 IPA/DL 共用 GPU 时的顺序 |

### `VGPU_Reallocate_memory`

| 项 | 内容 |
|----|------|
| **功能** | 深度学习等占用后，**重建**计算显存 |
| **宿主** | 分析流程结束后调用场景 |
| **如何实现** | Free + Allocate 同样尺寸；记录 peak VRAM |

### `VGPU_GetCudaErrorStatus` / `VGPU_GetCurrentGPUMemory` / `VGPU_ResetCudaMemory`

| 项 | 内容 |
|----|------|
| **功能** | 健康检查、读 total/free/used、异常时 reset 进程 CUDA 上下文侧资源 |
| **宿主** | MainWindow、IPA、Background 线程日志 |
| **如何实现** | `cudaGetLastError`/`cudaPeekAtLastError`；`cudaMemGetInfo`；严重错误时 `cudaDeviceReset`（慎用）+ 重新 Allocate |

---

## 2. Region：扫描 / 回拉过程计算（核心成像链）

### `VGPU_Data_Resampling_For_Scan` / `_Vivo` / `_For_Pullback`

| 项 | 内容 |
|----|------|
| **功能** | 原始光谱 **重采样到均匀 k**（或等价插值）并乘 **Hann 等窗**；Vivo 路径输入为 U8 + gain/offset |
| **输入** | `DOCMotionType`、原始 U16/U8、窗数组、（Vivo）gain/offset |
| **输出** | Device 上加窗后实数序列（或可选 D2H） |
| **宿主** | `ImageProcessingController` 实时帧循环 |
| **如何实现** | ① Host 预生成窗 `windata` 风格常量；② kernel：每线程一采样点或一 A-line；③ 标定表引导插值（线性/三次）；④ Vivo：`f = gain * u8 + offset` 再进同一路径 |
| **精读周** | W02 |

### `VGPU_Get_FFT_Power_Result` / `VGPU_Get_FFT_Power_Interpolation_Result`

| 项 | 内容 |
|----|------|
| **功能** | 对加窗数据做 **FFT**，取功率（及 log 相关），可选插值与底噪 `ground_noise` |
| **如何实现** | `cufftExecR2C` batch=线数；后接 kernel：`log(eps + re^2+im^2)` 或缩放；Interpolation 版输出 U16 压缩谱 |
| **精读周** | W03 |

### `VGPU_Pullback_ProcessData_ToImage`

| 项 | 内容 |
|----|------|
| **功能** | 回拉过程中**单帧捷径**：Raw→图像相关结果（可跳过完整逐步调试路径） |
| **如何实现** | 融合 kernel 或顺序调用内部等价于 Resample→FFT→… 的 device 函数；`current_pullback_frame` 写到 bulk 缓冲偏移 |

### `VGPU_Get_After_Log_Result` / `old_data_toLog` / `cutfront25` / `Denoising_data_toLog` / `U16fft↔F32fft`

| 项 | 内容 |
|----|------|
| **功能** | Log 域与存储格式互转；旧数据兼容；裁剪前 25 点 |
| **如何实现** | 逐元素 kernel；U16 量化需约定 scale；cutfront25 为 width 维 offset |
| **宿主** | `GpuHandlingDataThreadController` 导入旧记录等 |

### `VGPU_Get_Current_Frame_FFT_data` / `_After_Interpolation_data`

| 项 | 内容 |
|----|------|
| **功能** | 取出当前帧 FFT（拍照/存盘） |
| **如何实现** | D2H 当前 frame slice |

### `VGPU_Transpose` / `VGPU_Transpose_CheckImage`

| 项 | 内容 |
|----|------|
| **功能** | Log 功率数据 **转置 + 深度裁剪** `[start,end)`，输出方图方向；CheckImage 供检测用 |
| **如何实现** | shared-memory tile transpose；裁剪用指针偏移或第二维 limit |
| **精读周** | W04 |

### `VGPU_DSC`

| 项 | 内容 |
|----|------|
| **功能** | **数字扫描变换**：极坐标（深度×角度）→ 笛卡尔圆图；支持最近邻/双线性/三次 |
| **参数** | `raw_rows/cols`，输出 `polar_rows/cols`（圆图高宽），`inner_r/margin_r`，`InterpolateType` |
| **如何实现** | 每像素一线程：`(x,y)→(r,θ)` → 在 rect 上插值；优化：texture object、只算圆环带 |
| **精读周** | W04–W05 |

### `VGPU_Image_Enhancement`

| 项 | 内容 |
|----|------|
| **功能** | DSC 后灰度增强：Linear / Pow / Log / Exp；`low_bound/up_bound/pow_index` |
| **如何实现** | 逐像素归一化到窗后映射；注意 `is_device_to_host` 类型在头文件为 `int` |

### `VGPU_Gray2Color`

| 项 | 内容 |
|----|------|
| **功能** | LUT 伪彩（金/灰/RGB 族）；写出 `cv::Mat` |
| **如何实现** | 256×3 LUT 在 constant memory；kernel 写 BGR；最后通常 `ToHost=true` |

---

## 3. Region：导管校准

| API | 功能摘要 | 实现要点 |
|-----|----------|----------|
| `VGPU_AutoCalibration_new` / `_connect` | 参考臂/连接校准（旧） | 在转置图上搜导管壁峰，输出 `delt_y` / 内部 cut |
| `VGPU_Catheter_AutoCalibration` | **11 版主路径**；区分连接/术中、光源、新旧导管 | 多帧 `indexFrams`；输出 `out_calibration_data` |
| `*_cs` 测试接口 | Host 传入 transpose 缓冲的校准 | 便于离线单测 |
| `VGPU_CheckImageInfo` | 0 阈值问题 / 1 硬件问题 | 状态机 |

**精读周：** W07  
**宿主：** `ImageProcessingController` 校准分支。

---

## 4. Region：造影剂 / 折断 / guiding

| API | 功能 |
|-----|------|
| `VGPU_Contrast_MediumCheck5` | 10 版介质冲洗识别 |
| `VGPU_Contrast_MediumCheck_Afd` | AFD 变体；烟雾 `isSmoke` + 多 gap 阈值 |
| `VGPU_CheckCatheterBreakDetection` | 导管折断；输出检查图 |
| `VGPU_guidingDetectOneFrame` | guiding catheter 检测；输出 `avgPixels` |

**实现方向：** 沿 A-line 或环形带统计亮度/空隙；阈值与 `LINE_AVERAGE_GAP`、`PULL_BACK_THRESHOLD` 相关。  
**精读周：** W08

---

## 5. Region：回拉后处理 / 分析预处理

| API | 功能 |
|-----|------|
| `VGPU_Check_pullback_Data_memory` | 回拉前显存检查 |
| `VGPU_Set_Original_pullback_Data_To_GPU` | 整卷 Raw（U16 与/或 Vivo U8）上传 |
| `VGPU_Handle_All_Preview_data` | 全帧生成 FFT 预览 |
| `VGPU_Get_All_FFT_data` | 全帧 FFT 下载（U16 denoising） |
| `VGPU_Handle_All_FFT_data` | FFT→方图+圆图 |
| `VGPU_Handle_All_Calibration_Image` | 带校准裁剪的方/圆图 |
| `VGPU_OneFrameRawData_To_Image` | 单帧 Raw→圆图 |
| `VGPU_PullbackRawData_To_FFT_Data` | 竞品 raw→FFT 方图 |
| `VGPU_C7C8_PullbackFFT_Data_To_Image` | 竞品 FFT→图 |
| `VGPU_PullbackDcm_Data_To_Image` | DCM 方图→方/圆 |
| `VGPU_PullbackRawData_To_Image` | 竞品 raw→方/圆 |
| `VGPU_Set_all_U16_FFT_data_to_Gpu` / `Set_all_FFT_data_to_Gpu` | 分析侧把 FFT 灌回 GPU |
| `VGPU_CalculatedContrastRange` | 自适应对比度上下界 |
| `VGPU_Hnad_One_Frame_Data` | 按帧取图（拼写为 Hnad） |
| `VGPU_Data_Power_aline` / `Vivo_*` | 光灵敏度：一线功率均值 |

**精读周：** W06、W14  
**实现要点：** 批量 H2D → 循环或 grid-stride 跨帧 → 少次 D2H；与实时路径共享 kernel，仅 grid 尺寸变。

---

## 6. Region：管腔拼接与连续校准

| API | 功能 |
|-----|------|
| `VGPU_Get_Lumen_Stitching_FFT_Image` | 远/近端 FFT 按帧范围与旋转角拼接 |
| `VGPU_Get_Lumen_Stitching_Denoising_Data` | U16 降噪域拼接 |
| `VGPU_Continuous_Clibration_To_Circle_Image` | 连续校准预处理出圆图 |
| `VGPU_Get_All_Continuous_Calibration_Image` | 全卷连续校准图 |
| `VGPU_Update_Frame_Continuous_Calibration_Image` | 单帧更新 |
| `VGPU_C7C8_Get_All_Continuous_Calibration_Image` | 竞品连续校准 |
| `VGPU_GetContinuousCalibration` | 计算每帧 `catheterCutStartHeight`；`machine_model` 0冠脉/1颈动脉/2颅内 |

**精读周：** W09

---

## 7. Region：IPA

### 旧 API（对照）`IpaAlgorithmKernel.cuh`

- `GUP_SetIpaalgorithmConfig(att_paras, h_isOption)` — 初始化/释放 IPA GPU 配置  
- `GPU_Calculate_Ipa_Result(...)` — 输入 float raw；多 `out_ipa_fin`

现已合并进 `VGPU_Calculate_Ipa_Result`（输入 U16 FFT 等）。

### `VGPU_Calculate_Ipa_Result`

| 项 | 内容 |
|----|------|
| **功能** | 基于管腔/中膜/标签与衰减参数，估计每 A-line **衰减系数 μ**，输出 μ 体数据与毯展相关 `out_carpet_att` |
| **输入** | `att_paras`，`in_all_raw_data`（工程中为 FFT U16），`reshaped_lumen`，`in_reshaped_media`（宿主常传 100），`labels_data`，`in_ipa_11_mat_cof`（脂质阈值 9.5/10.5/11/14），`ground_noise`，`isVivoData` |
| **输出** | `out_all_aline_mu`，`out_carpet_att` |
| **宿主** | `IPAAlgorithmController::IPAProcessing` |
| **如何实现（公开版假设）** | ① 每 A-line 一 block 或一 warp；② 在 lumen→media 深度窗内对 log 强度做线性拟合得斜率≈μ；③ SNR/`minwin`/`step_*` 控制窗搜索；④ labels 区分健康组织是否参与；⑤ 写 μ 矩阵 `[theta, depth, frame]` 布局需与 `All_Aline_Mu_Data_To_Image` 一致 |
| **精读周** | W10–W11 |

### `VGPU_All_Aline_Mu_Data_To_Image`

| 项 | 内容 |
|----|------|
| **功能** | μ 方图体数据 → 每帧圆图（复用 DSC 思想） |
| **宿主** | `IPAAlgorithmController` 单帧/全卷 |

### `VGPU_UpdateValueIPA`

| 项 | 内容 |
|----|------|
| **功能** | 改阈值后，由线 IPA μ **重算** IPA_L / RangeMean / IPA_A / IPA_T 毯展色图与 colorbar |
| **宿主** | `BackgroundIPAUpdateThreadController`、`IPAZoneController` |
| **如何实现** | 可为 CUDA 或 CPU；按 `InThresholdT`、`pixelSapcing`、`InMode_ID` 聚合帧级指标并 LUT 上色 |
| **精读周** | W12 |

---

## 8. 接口 ↔ 开源模块映射表

| 开源模块名 | 覆盖的 VGPU API |
|------------|-----------------|
| `oct::Context` | Allocate / Free / Realloc / Memory / Status |
| `oct::ResampleWindow` | Data_Resampling_* |
| `oct::FftLog` | Get_FFT_Power_* / Log / U16↔F32 |
| `oct::TransposeCrop` | Transpose* |
| `oct::Dsc` | DSC |
| `oct::EnhanceColor` | Enhancement / Gray2Color |
| `oct::PullbackBatch` | Set_Original / Handle_All_* |
| `oct::Calib` | Catheter_AutoCalibration* |
| `oct::Detect` | Contrast / Break / guiding |
| `oct::StitchContCalib` | Stitching / Continuous* |
| `oct::Ipa` | Calculate_Ipa / Mu_To_Image / UpdateValueIPA |

---

## 9. 自学勾选

在精读完每个 region 后，于本文件对应小节末尾自行添加：

```text
- [ ] 已读宿主调用
- [ ] 已画 IO 图
- [ ] 已在开源仓有对应模块（或明确延期到哪一周）
```
