# Week10 / Day03 — 学习记录（源码填充版）

> 主题：`VGPU_Calculate_Ipa_Result` 实参来源与尺寸精读（链 D 详细版）。

## 1. 今日目标（回顾）
把宿主调用语句的**每个实参**追到来源 GetGlobal* / DicomModel，并把每块内存的尺寸写死（可复核）。

## 2. 调用点（真实，IPAAlgorithmController.cpp L239-245）
```cpp
U16* original_fft_image_buffer = GetGlobalFFTData();            // L239
bool is_success = VGPU_Calculate_Ipa_Result(
    ipa_config_params_,          // ① att_paras（W10D2 三配置/派生填好）
    original_fft_image_buffer,   // ② in_all_raw_data：FFT U16 卷
    reshaped_lumen.get(),        // ③ lumen 掩膜（DicomModel 拷贝）
    100,                         // ④ in_reshaped_media：常数（宿主直传）
    labels_data.get(),           // ⑤ labels 掩膜（DicomModel 拷贝）
    this->miu_gray_array_,       // ⑥ out_all_aline_mu：μ 体 float
    line_ipa_miu.get(),          // ⑦ out_carpet_att / line μ：float[alines]
    lipid_plaque_threshold,      // ⑧ 脂质阈值 9.5/10.5/11
    0,                           // ⑨ ground_noise：非微光可任意（L244 注释）
    isVivoData);                 // ⑩ 是否活体（P60/P80 true；C7C8 false）
```

## 3. 每实参来源与尺寸表（尺寸公式来自宿主 L175-244）
| # | 形参名(01 §7) | 实参来源 | 尺寸 | 类型 |
| --- | --- | --- | --- | --- |
| ① | att_paras | 本类 ipa_config_params_（L56-180 填） | 16 字段 struct | 结构体 |
| ② | in_all_raw_data | `GetGlobalFFTData()` | frames×500×1025 U16 | U16* |
| ③ | reshaped_lumen | DicomModel.m_pre_ipa_analysed_result.reshaped_lumen（L191 memcpy） | number_alines=frames×500 | int[] |
| ④ | in_reshaped_media | 宿主直传 `100` | 标量 | int |
| ⑤ | labels_data | DicomModel.…labels_data（L192） | number_alines | int[] |
| ⑥ | out_all_aline_mu | 本类 miu_gray_array_（L221 分配） | frames×500×1025 float | float[] |
| ⑦ | out_carpet_att | line_ipa_miu（L236 分配） | number_alines | float[] |
| ⑧ | 脂质阈值 | 三配置分支（L66/79/93） | 标量 9.5/10.5/11 | float |
| ⑨ | ground_noise | 0（注释：只对微光生效） | 标量 | float |
| ⑩ | isVivoData | 分支 L59/89/103 | 标量 | bool |

**布局记忆**：μ 体 `miu_gray_array_` 按 **帧外层** 存（frame i 偏移 = i×rows×cols，宿主 L259-265 调试代码可证：`miu_gray_array_ + i*rows*cols`）。

## 4. 掩膜语义（公开推理）
- `reshaped_lumen`：每条 A-line 一个 lumen 内边界（深度指数）→ μ 拟合起点；
- `labels_data`：每条 A-line 组织分类标签 → 只允许健康/感兴趣组织参与拟合，跳过斑块外无效带；
- `media=100`：中膜外边界相关常数（宿主未从模型取，直传 100）——拟合窗外端约束；
- 两者都来自“预处理分析结果”（m_pre_ipa_analysed_result），即 **先有 lumen/label，才有 IPA**（链上依赖，W11 会体现）。

## 5. 自测
1. 写出 number_alines = ? 用 GetGlobal* 表达式（§3 ②⑥⑦ 长度同号自检）；
2. 若 frames=550：miu_gray_array_ 字节数 = 550×500×1025×4 ≈ **1.13 GB**——对照宿主为何 L207-216 只在“尺寸变化”时 delete 再 new（避免每帧重分配）；
3. ground_noise 为何能任意值？→ L244 注释明确“只对微光数据生效”，说明内核内部按 isVivoData/模式分支读底噪来源。

## 6. DoD 打卡
- [x] 链 D 详细版（§3 表：每指针来源+尺寸）完成，尺寸公式可复核

## 明日预告
开源 μ 估计 SPEC（W10D4）：每 A-line 滑窗拟合 + minwin/step/SNR 约束的 CPU 伪代码。
