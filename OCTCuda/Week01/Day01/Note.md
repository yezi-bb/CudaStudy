# Week01 / Day01 — 学习记录（源码填充版）

> 用途：对照 `Week01/Day01/TASK.md` 精读并自查。先读结论 → 再回到源码验证 → 完成 DoD 打勾。
> 路径约定：本工作区 `E:\CUDA\source\` 即公司仓镜像（= `E:\OCT10\AIOCT\`），下文所有引用均指向该本地镜像，可直接打开核对。

## 1. 今日目标（回顾）
建立 OCTCuda 学习上下文：认清「无 .cu 源码」的真实边界，搭好笔记目录与 API 术语索引，为后续“宿主调用 + 接口 + 公开算法重写”的学习法打底。

## 2. 必读与真实代码锚点（先对照读一遍）

| 本地镜像文件 | 要点 |
| --- | --- |
| `E:\CUDA\source\Algorithm\vgpu\include\VGPU_Process.cuh` | 全仓唯一的 GPU 计算“事实源”，extern "C" `__declspec(dllexport)` 声明、枚举与结构体。 |
| `E:\CUDA\Learning\CudaStudy\OCTCuda\01_API接口全解.md` | 每个 API 的字段级说明。 |
| `E:\CUDA\Learning\CudaStudy\OCTCuda\02_数据流与调用链.md` | 链 A–H（实时/回拉/分析/IPA 等）宿主调用序列。 |

验证结论（可在本机重跑）：
- 整个 `E:\CUDA\source\Algorithm\` 下**没有 `.cu` 实现文件**（只有 include 头）→ 内核在闭源 GPU DLL 内；
- 宿主只通过 `VGPU_Process.cuh` 的函数声明调用 DLL（`.cpp` 中搜索 `VGPU_` 可见大量调用点，例如 `ImageProcessingController.cpp`）。

## 3. Region 目录与函数名索引（照头文件 1:1 建立）

读 `VGPU_Process.cuh` 的 `#pragma region`，得到 6 大块 + 散点函数，按类别归位：

| Region / 范围（行号） | 代表 API | 类别 |
| --- | --- | --- |
| 参数配置与显存分配（L181-223） | `VGPU_Allocate_Parameter_Manager`、`Free_Parament_Manager`、`SetFunctionConfig`、`SetCalibrationData`、`Reallocate_memory`、`GetCudaErrorStatus`、`GetCurrentGPUMemory`、`ResetCudaMemory` | 生命周期/监控 |
| 扫描回拉过程计算（L225-275） | Resampling(Scan/Vivo/Pullback)、FFT_Power、Pullback_ProcessData_ToImage、After_Log、Transpose、DSC、Enhancement、Gray2Color | 成像主干（实时/回拉） |
| 导管校准相关（L277-298） | `Catheter_AutoCalibration`、`AutoCalibration_new`、`AutoCalibration_connect`、`CheckImageInfo` | 校准检测 |
| 自动回拉造影剂检测（L301-307） | `Contrast_MediumCheck5` / `_Afd` | 校准检测 |
| （散点）L309-313 | `CheckCatheterBreakDetection`、`guidingDetectOneFrame` | 检测 |
| 回拉后处理 / 分析预处理（L315-361） | `Check_pullback_Data_memory`、`Set_Original_pullback_Data_To_GPU`、`Handle_All_*`、`Get_All_FFT_data`、`OneFrameRawData_To_Image`、`Set_all_*_FFT_data`、`CalculatedContrastRange` | 批处理（整段回拉） |
| 拼接 / 连续校准（L364-418） | `Get_Lumen_Stitching_*`、`Continuous_Clibration_To_Circle_Image`、`Get_All_Continuous_Calibration_Image`、`GetContinuousCalibration` | 批处理 |
| IPA 计算相关（L420-481） | `Calculate_Ipa_Result`、`All_Aline_Mu_Data_To_Image`、`UpdateValueIPA` | IPA |

记忆点：
- 头里枚举即“全局配置”：`DOCMotionType`、`WinType`、`InterpolateType`、`GrayEnhanceType`、`ColorsMapType`、`GPUCalibrationType`、`GPULightSourceType`、`att_paras`（IPA 结构体，L161-178）。
- 常量速记：`BLOCK_DIM=256`、`VALID_R=900`、`RESIZE_HW=128`、`COLOR_LEVEL=256`、`ALINE_NUM=2*ALINES_PER_FRAME`。

## 4. “一页纸”：公司仓 vs 未来开源仓职责对比（答案参考）

| 维度 | 公司仓（`E:\CUDA\source`） | 开源仓（`oct-cuda-pipeline`，Day04 建） |
| --- | --- | --- |
| GPU 计算 | 调用闭源 DLL（只见声明） | 自写 CUDA kernel（resample/FFT/DSC…） |
| 宿主编排 | Qt 控制器 + 线程控制器完整链路 | 最小 host 驱动（单帧主链起步） |
| 学习价值 | 学“接口契约 / 数据流 / 边界” | 学“kernel 实现 / 显存 / 优化” |
| 合规 | 本仓内容不可直接复制提交 | 只放公开算法与自写实现 + 合规声明 |

## 5. 动手任务记录

- [x] `notes/` 目录结构（W01_api_index.md 等内容建议并入 `Week01` 笔记归档，保持单仓即可）
- [ ] 本机环境记录区（自查自填）：
  - CUDA Toolkit 版本：`nvcc --version` → `__________`
  - GPU 型号 / 显存：`nvidia-smi` → `__________`
- [ ] 5 分钟口述练习：能说出为什么简历只写「调用过 VGPU_Process」不够 → 答：调用只是 API 编排，内核、显存布局、性能优化都在黑盒里；要证明能力必须有自己的 kernel/优化实践。

## 6. 自测五问（先答再看答案）

1. 为什么本仓没有 .cu？→ 内核随 DLL 分发，仅头文件导出符号。
2. 共几个 region？各归哪类？→ 6 region，见上表。
3. `extern "C"` + `__declspec(dllexport)` 说明什么？→ C 链接 + Windows DLL 导出，供 Qt/宿主直接调用。
4. 学习路线为何先“API+宿主”再“重写”？→ 用契约定义清晰、可验证的输入/输出，重写时能对照测试。
5. 头文件里的常量（BLOCK_DIM 等）能说明什么？→ 内核粒度/边界设计线索，重写时要参考。

## 7. 疑点 / 待办

- `VALID_R=900` 与圆图 704 的关系待 Week04 DSC 验证。
- `notes/` 内容组织：建议按 `WeekXX/` 内嵌，避免重复维护。

## 8. DoD 打卡

- [ ] 能口述：为何简历不能只写「调用过 VGPU_Process」
- [ ] 已有 region 函数名索引（本笔记 §3 可作为底稿）
- [ ] 已记录本机 CUDA 环境

## 明日预告
精读 Allocate / Free / Memory / Status 等生命周期 API。
