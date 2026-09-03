# Week08 REVIEW — 检测类（造影剂 / 折断 / Guiding）

> 依据：`00_全局规划.md` §7 合规；源码锚点为本地镜像已核对。检测总图见 `notes/W08_detect_hooks.md`。

## 1. 检测 API 与宿主触发
| 检测 | API (cuh) | 宿主 | 状态门 → 置位 |
| --- | --- | --- | --- |
| 造影剂(介质) | Contrast_MediumCheck5 L303 / Afd L305-306 | HandleDataOfRecording L755-820 | EVerifyPurgeState/ESmokeTestCheckState + Automatic → m_is_verifypurge_success=true |
| 导管折断 | CheckCatheterBreakDetection L310 | HandleDataOfScanning L541-555 | EScanState 上升沿 → GlobalCurrentCatheterBreakStatues=true |
| Guiding | guidingDetectOneFrame L313 | HandleDataOfRecording L821-836 | EPullbackRecordState + AFD → success=true / need=false |

## 2. 一周掌握清单
- [ ] 造影剂 5 vs Afd：何时走哪个（AFD&&use）、isSmoke=false/true 两组阈值
- [ ] 检测专用全深度 Transpose_CheckImage 与成像 cut 带 Transpose 的区别（L762 vs L779）
- [ ] 折断三条件默认值来自 ImageProcessingController.h L131-135（0.3 / 0.0019 / 90）
- [ ] guiding：跨帧 avgPixels + startRow=10 + totalFrame 的语义
- [ ] 三类检测同步嵌入帧链 + __except 保护 + bool→全局位 的通用模式

## 3. 开源练习交付
- cpu_medium_check（列均值亮度 + 暗列占比）
- cpu_break_check（能量 + 行峰一致性 + 无峰列）
- cpu_guiding_detect（滑动基线抬升到达判定）
- pre_dsc_checks.run(kind, frame, ctx) → CheckReport{kind, ok, why}
- 合成自测通过：ok 帧/失败帧/半遮挡/暗帧/平稳序列

## 4. 合规边界
- 公开：检测位置（DSC 前）、逻辑类型、协同方式、开源阈值自定义；
- 私有：标定真值、内核统计细节、AFD 全链路参数。

## 5. 下周预告（W09 连续校准/拼接，cuh L387-398/L418）
Lumen Stitching（远近端 FFT 拼接）、连续校准（Continuous_Clibration / Get_All_Continuous / Update_Frame）、GetContinuousCalibration（机型+新导管→cut 预估）。
