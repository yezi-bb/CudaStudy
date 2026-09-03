# Week08 / Day05 — 学习记录（源码填充版）

> 主题：W08 REVIEW——检测类 API 复盘对比 + 合规边界；预告 W09（连续校准/拼接）。
> 周复盘文件：`Week08/REVIEW.md`；检测总图：`notes/W08_detect_hooks.md`。

## 1. 本周目标回顾
D1 造影剂（5/Afd 分支、全深度窗口）→ D2 导管折断（Scan 态上升沿、h 头默认阈值）→ D3 guiding（跨帧序列 + avgPixels + totalFrame）→ D4 三检测统一为 pre_dsc_checks 检测站。

## 2. 检测类 API 全景（VGPU_Process.cuh，行号已核对）
| API | 位置 | 一句话 | 判定风格 |
| --- | --- | --- | --- |
| `VGPU_Contrast_MediumCheck5` | L303 | 介质冲洗识别（少参版） | 单帧→bool |
| `VGPU_Contrast_MediumCheck_Afd` | L305-306 | AFD 版（isSmoke + 4 外部阈值） | 单帧→bool |
| `VGPU_CheckCatheterBreakDetection` | L310 | 导管折断（3 条件 + 可选检查图） | 单帧→bool + 检查图 |
| `VGPU_guidingDetectOneFrame` | L313 | 回拉 guiding 到达（跨帧序列） | 帧推入→到达即 true |
| `VGPU_CheckImageInfo` | L297 | 0=算法/1=硬件（复用诊断） | 查询 |

## 3. 对比维度表（能口述）
| 维度 | 造影剂 | 折断 | Guiding |
| --- | --- | --- | --- |
| 宿主状态门 | Purge/Smoke + Automatic | EScanState（上升沿） | EPullbackRecord + AFD |
| 输入窗口 | 全 FFT 深度（CheckImage 专用转置） | GPU 内部方图 | GPU 内部方图 |
| 是否跨帧状态 | 仅帧号递增 | 无 | avgPixels 累积序列 |
| 失败行为 | 保持状态再试 | 置位报警一次 | 下帧再判 |
| 出图协同 | 检测后仍走正常 Transpose→DSC→增强 | 同左 | 同左 |

## 4. 一周“抄作业”金句
1. 检测 = “在 DSC 前的方图上，把物理现象翻译成可算特征 + 阈值组合”。
2. 安全类事件（折断）用**上升沿 + 全局位**，只报一次；流程类事件（guiding）用**跨帧确认**。
3. 参数在 h 头给默认值（0.3/0.0019/90），使宿主“零配置可跑、按需可调”。
4. 排查现场图永远**按需回拷**（m_is_save_* / is_device_to_host）。
5. 三套检测都“同步嵌入帧链 + __except 保护”——GPU 崩不了采集线程，检测失败不会卡死 UI。

## 5. 合规边界复述（00 §7）
- 公开：检测点的**位置**（DSC 前方图）、判定**逻辑类型**（能量/间隙/序列到达）、**协同方式**；
- 私有：具体阈值与判定分支的**标定值/真值**、GPU 内核内部统计、AFD 全链路。

## 6. W09 预告：连续校准 / 拼接（真实声明，cuh）
| API | 位置 | 一句话 |
| --- | --- | --- |
| `VGPU_Get_Lumen_Stitching_FFT_Image` | L387 | 远近端 FFT 数据拼长段（含各自 cut/角度） |
| `VGPU_Get_Lumen_Stitching_Denoising_Data` | L388 | 去噪域拼接版（U16） |
| `VGPU_Continuous_Clibration_To_Circle_Image` | L392 | 连续校准预处理：指定帧号出圆图 |
| `VGPU_Get_All_Continuous_Calibration_Image` | L395 | 全 FFT → 连续校准后矩形+圆图 |
| `VGPU_Update_Frame_Continuous_Calibration_Image` | L398 | 增量更新帧 |
| `VGPU_GetContinuousCalibration` | L418 | 机型/新导管 → catheterCutStartHeight 预估 |
| `VGPU_Handle_All_Calibration_Image` | L333 | 全校准图生成（复习 W06） |

## 7. DoD 打卡
- [x] 对比表/金句/合规复述完成（本 Note + REVIEW.md + notes 总图）

## 明日预告
Week09：连续校准（逐帧 cut）与长段拼接（Lumen Stitching）的宿主数据流与公开实现。
