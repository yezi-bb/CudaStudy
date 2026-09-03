# Week09 REVIEW — 连续校准与管腔拼接

## 1. 一周主题
单帧 cut → **per-frame cuts[]（连续校准）**；两段 FFT 卷 → **长卷拼接（Lumen Stitching）**；出图粒度：探测/全卷/单帧更新。

## 2. API 与宿主落点
| 能力 | API | 宿主行（IntegrationChannel.cpp） |
| --- | --- | --- |
| 拼接 | Get_Lumen_Stitching_FFT/Denoising | L5477-5478 |
| 连续校准 | GetContinuousCalibration | L6066/6070/6094/6098 |
| 全卷出图 | Get_All_Continuous_Calibration_Image | L4285/4360/6192/6284 |
| 竞品源 | C7C8_Get_All_Continuous_Calibration_Image | L4291/4366/6198/6290 |
| 单帧更新 | Update_Frame_Continuous_Calibration_Image | L6361-6363 |

## 3. 掌握清单
- [ ] GetContinuousCalibration：machine_model(0/1/2)、is_new_catheter、输出 int* catheterCutStartHeight[]
- [ ] 全卷 vs 单帧更新的缓存复用策略（Update_Frame 只重算目标帧）
- [ ] 拼接两段各自用自己 cut[0]，近端按 (360-rotate_angle) A-line 圆周移位
- [ ] C7C8 适配器：数据源差异被隔离在入口层
- [ ] CPU 实现：cpu_continuous_calib（逐帧寻峰 + 5 点中值平滑）、cpu_rolling_stitch（std::rotate 线维）

## 4. 开源练习交付
- Demo：300 帧合成卷，真实 cut 正弦漂移；连续 cut 环高方差 ≤ 统一 cut 的 1/3；update_frame 仅目标帧变化；stitch 断言全绿。
- 文档：notes/W09_continuous_calib_demo.md

## 5. 下周预习（IPA 三周开端）
- att_paras（cuh L161-178）：z0/zR/zC/zw、SNRmax/noise_level/minwin/步长、卷尺寸
- 机型分支（IPAAlgorithmController.cpp L56-180）：P60→9.5/z0=0；P80→10.5/z0=0.5；C7C8→竞品换算
- 主线：VGPU_Calculate_Ipa_Result / All_Aline_Mu_Data_To_Image / UpdateValueIPA
