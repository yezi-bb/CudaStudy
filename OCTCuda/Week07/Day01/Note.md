# Week07 / Day01 — 学习记录（源码填充版）

> 主题：GPUCalibrationType / GPULightSourceType 与 `VGPU_Catheter_AutoCalibration` 主接口。

## 1. 今日目标（回顾）
吃透“连接校准 vs 术中自动、光源、新旧导管”对校准的影响；画清校准如何改 Transpose 的 start/end。

## 2. 真实声明与枚举

```cpp
// VGPU_Process.cuh L286-287
bool VGPU_Catheter_AutoCalibration(GPUCalibrationType calibrate_type, GPULightSourceType light_source_type,
    bool is_new_catheter, float ground_noise, int indexFrams, double cutHeight,
    int TransPose_height, int Transpose_width, cv::Mat& out_calibration_data,
    bool is_device_to_host, bool is_twice_check);
```
- `GPUCalibrationType`：`GpuAutoCalibration`（术中自动）/ `GpuConnectCalibration`（连接参考臂校准）等（头 L143-147）；
- `GPULightSourceType`：光源类型（A/B/…），决定谱形态与校准预期。

宿主（ImageProcessingController.cpp，行号已核对）：
- L497：`catheterCutHeight = round(GetGlobalSystemOCTCatheterDiameter()/2/GetGlobalCurrentRecordPixelSpacing()) + 15;`——导管半径换算到“深度像素行”+15px 余量。
- L561-565：校准用图高 `image_hight = cut_end-cut_start`；若当前视野 `>7mm` 则统一按 7mm 折算 `image_hight = floor(7.0/2.0/pixelSpacing)`。
- L572-574（术中自动）：`VGPU_Catheter_AutoCalibration(GpuAutoCalibration, m_light_source_type, GetIsCatheterType(), 0, 37, catheterCutHeight, image_hight, 1000, save_Calibration_mat, m_is_save_flag, !GetIsFirstCatheterSelfChecking())`——用第 **37 帧** 作参考帧；`is_device_to_host=m_is_save_flag`（只有存图/调试才回拷）。
- L586-594（连接校准）：`GpuConnectCalibration` + `m_check_frame_index`（连续递增帧）；二次校验开关 = `GetIsFirstCatheterSelfChecking()` 取反。
- 成功 → 状态 `ECalibrationState → EScanState`（L608），失败保持在校准态并持续保存校准图（L603-615）。

## 3. 参数释义表（DoD 交付）

| 参数 | 含义 | 典型来源 |
| --- | --- | --- |
| calibrate_type | 自动校准类型 | GpuAutoCalibration / GpuConnectCalibration |
| light_source_type | 光源类型 | 当前配置 |
| is_new_catheter | 新旧导管(算法参数集) | `GetIsCatheterType()` |
| ground_noise | 底噪(去 DC 用) | 0 |
| indexFrams | 参考帧序号 | 自动=37；连接=递增 m_check_frame_index |
| cutHeight | 导管半径对应深度像素+余量 | L497 公式 |
| TransPose_height/width | 输入转置图尺寸 | image_hight(≤7mm 视野) × 1000 |
| out_calibration_data | 调试/保存用校准图 | CV_32FC1 |
| is_device_to_host | 是否回拷校准图 | 仅 m_is_save_flag 时 true |
| is_twice_check | 二次校验 | 首次自检为 false |

## 4. 校准如何改 Transpose start/end（图，DoD 交付）

```
校准前(无校准)： start=0, end=AFT 全长 1025   → 全深度转置（L495 起临时值）
      │ 自动校准(取 37 帧) 成功
      ▼ 输出内部校准量：导管中心/半径、有效深度带
宿主更新 m_cut_start_point / m_cut_end_point（如 100..700）
      ▼
实时链 DSC 前 Transpose 只取 [cut_start, cut_end)（L534）→ 圆图聚焦血管腔
失败 → 保持 0..AFT 或 停在校准态等用户重试
```
DSC raw_rows 随之 = `cut_end-cut_start`（L625），**校准的产出物理上就是“给成像链的深度窗口”**。

## 5. 自测 Q&A
1. 为什么用“第 37 帧”当参考？→ 马达稳定后/首帧坏帧排除；帧号即采样时间点，实现上“选稳定帧”。
2. 回拷只在 m_is_save_flag？→ 校准算法自身只需 device 内图，回拷仅调试存图用——又见“只在需要处 D2H”。
3. 7mm 以上视野为何按 7mm 折算？→ 大视野里导管壁可能超出深度范围/分辨率差，用统一 7mm 校准可重复。
4. cutHeight 的 +15 像素作用？→ 导管半径定位误差余量，保证 cut 起点在导管壁内侧而不是贴壁。
5. is_twice_check 什么时候 false？→ 首次导管自检（要快速粗检）；复检再开二次校验提高置信度。

## 6. DoD 打卡
- [ ] 参数释义表完成（§3）
- [ ] 校准→cut 联动图画清（§4）

## 明日预告
旧 AutoCalibration_new / _connect / *_cs 与 CheckImageInfo。
