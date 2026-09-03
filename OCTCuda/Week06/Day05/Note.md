# Week06 / Day05 — 学习记录（源码填充版）

> 主题：W06 复盘 + W07（导管校准）预习。

## 1. 今日目标（回顾）
沉淀“回拉批处理状态机”的完整认知，并预习校准 API 族。

## 2. Week06 REVIEW 底稿（抄进 `Week06/REVIEW.md`）

**API 范围**：Check_pullback_Data_memory / Set_Original_pullback_Data_To_GPU / Handle_All_Preview_data / Get_All_FFT_data / Handle_All_FFT_data / Handle_All_Calibration_Image / OneFrameRawData_To_Image / Hnad_One_Frame_Data / CalculatedContrastRange / Set_all_FFT_data_to_Gpu / 竞品转换 4 API / PullbackVolume。
**核心结论**：
1. 回拉状态机：`Check(前置显存) → 采集ring → Set_Original(整卷 raw 上传) → Handle_All_Preview(批 FFT+去噪 KeepDevice) → Get_All_FFT_data(U16 下载)`；
2. 方/圆图批渲染两代接口差在深度段来源（start/end vs 校准 icut_start+icut_size）；来源分支先归一化为“内部 FFT 卷”（竞品 4 个转换 API）；
3. 自适应窗对“已驻留 GPU 的卷”做统计返回 black/white level 与暗图像标志；
4. 单帧回放两类：Hnad_One_Frame(卷内取帧) / OneFrameRawData(单帧 raw 即算即出)。
**量级**：整卷 FFT（550 帧 × __ 线 × 2048）在 device 一次完成；U16 下载 `___ MB`。
**三个疑问（示例）**：整卷 raw 的每帧行数=扫描线 or 497？（运行时核对 PrintShape）；竞品数据的“方图”列序是否与自研一致；Calibration_Image 与 FFT_data 版本在校准后的实际切换点。

## 3. W07 预习（校准 API，见 VGPU_Process.cuh L277-307）
| API | 注释要点 |
| --- | --- |
| `VGPU_Catheter_AutoCalibration` | 导管自动校准（单帧图像），image_hight/输入原始+窗/输出校准结果+图 |
| `VGPU_AutoCalibration_new` | 新校准算法（多帧/更大搜索） |
| `VGPU_AutoCalibration_connect` | 连续段校准连接/拼接用 |
| `VGPU_CheckImageInfo` | 图像信息（可能含灰度/统计，用于判断可校准） |
| `VGPU_Contrast_MediumCheck5 / _Afd` | 自动回拉造影剂检测 |
| `VGPU_CheckCatheterBreakDetection` | 导管折断检测 |
| `VGPU_guidingDetectOneFrame` | 回拉过程 guiding 检测 |

预习问题：校准输入的是什么图（方图还是实时圆图）？输出哪些校准量（导管中心、半径、cut start/end、直径换算）？

## 4. 自测 Q&A
1. 批量处理最重要的设计原则？→ 显存前置检查 + 数据归一化后再批处理（来源差异进门前解决）。
2. 为什么 CalculatedContrastRange 可以“只返回窗值”？→ 输入卷已驻留 GPU，是“后处理统计”而非图像处理。
3. 为什么要先预览 FFT 再下载？→ Preview 在 device 内校验卷质量（白/暗、噪底）而无需 1GB 级下载先行。
4. open 端最值得优先做哪个？→ 一个 `PullbackPipeline::process_volume` 串起 upload→preview→download→render，作为 W08 检测的基础数据源。

## 5. DoD 打卡
- [ ] `Week06/REVIEW.md` 完成（§2 底稿）
- [ ] 校准预习表已建（§3）

## 明日预告
Week07：导管自动校准。
