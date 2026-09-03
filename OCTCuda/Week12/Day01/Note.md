# Week12 / Day01 — 学习记录（源码填充版）

> 主题：`VGPU_UpdateValueIPA` 参数→输出→UI 字段对照表。

## 1. 今日目标（回顾）
把 Update 的全部输入/输出缓冲与宿主字段、UI 呈现一一对上。

## 2. API 声明与长注释（真实，VGPU_Process.cuh L460-480）
```cpp
bool VGPU_UpdateValueIPA(
    float* InlineIPA,          // 回拉序列线 IPA μ（一帧的线数×帧数 = line_ipa_miu）
    int iFrameNumbers,         // 帧数
    int iAllLineNumbers,       // 总线数（一帧线数×帧数）
    double pixelSapcing,       // 帧间距（mm/帧）
    bool isVivolightIPA,       // 是否微光数据
    double InMode_ID,          // 非工作站=0；工作站版 0..3（可选模式）
    double InThresholdT,       // 脂质阈值：P60 9.5 / 其它 10.5 / 竞品 11（注释原文）
    double* ipa_l_data,        // IPA_L          1×iFrameNumbers
    double* ipa_l_range_mean_data, // IPA_L_RangeMean 1×iFrameNumbers
    float*  IPA_A,             // IPA_A
    unsigned char* IPA_T,      // IPA_T（彩色毯展）
    double* IPA_A_colorbar, int* IPA_L_colorbar);
```

## 3. 参数→输出→UI 对照表（真实宿主字段，两处调用一致：BackgroundIPAUpdateThreadController L886-891 与 IPAZoneController L148-153）
| 方向 | API 参数 | 宿主实参（DicomModel） | 分配/语义 | UI 呈现 |
| --- | --- | --- | --- | --- |
| 输入 | InlineIPA | pre_ipa.line_ipa_miu | float[total_line_numbers]（W11 算的每线 μ） | —（隐藏） |
| 输入 | iFrameNumbers | pre_ipa.total_frame_numbers | int | — |
| 输入 | iAllLineNumbers | pre_ipa.total_line_numbers | frames×frame_lines（497×frames） | — |
| 输入 | pixelSapcing | pre_ipa.lpixel_sapcing | GetPixelSpacing()[2]（帧间距 mm） | 长度换算 |
| 输入 | isVivolightIPA | pre_ipa.is_vivolight_ipa | bool（微光模式开关） | 数据模式 |
| 输入 | InMode_ID | pre_ipa.ipa_mode | double（工作站 0..3 / 非工作站 0） | 模式下拉 |
| 输入 | InThresholdT | pre_ipa.threshold | 9.5/10.5/11（**用户改的就是它**） | 阈值编辑框/滑杆 |
| 输出 | IPA_L | ipa_l_image | double[frames] | 帧级脂质长度曲线 |
| 输出 | IPA_L_RangeMean | ipa_l_range_mean_image | double[frames] | L 的范围均值曲线 |
| 输出 | IPA_A | ipa_a_iamge | float[total_line_numbers] | 线级衰减（与原 μ 配套） |
| 输出 | IPA_T | ipa_t_image | uchar[1250×frame_lines×3]（宿主注释“彩色毯展图 1250*497*3”） | 轴向彩毯视图 |
| 输出 | IPA_A_colorbar | ipa_a_colorbars | double* | A 色条图例 |
| 输出 | IPA_L_colorbar | ipa_l_colorbars | int* | L 色条图例 |

## 4. 语义解读（公开推理，避免过度解释）
- 用户只改 **1 个标量（InThresholdT）**，却要重算 **6 路输出**——因此“更新”本质是**同一 line μ 在不同阈值下的投影**：着色判定（>thr）、帧聚合（L/RangeMean）、线值（A）、色图（T）、图例（colorbars）。
- 这也是为什么 **Update 比 Calculate 轻**：μ 不用重算（W12D2 展开）。

## 5. 自测 Q&A
1. InlineIPA 是整卷都传？→ 是，宿主传 line_ipa_miu（frames×frame_lines），但算法内部只做“统计+着色”，不重算 μ。
2. 为什么 mode 影响输出？→ 工作站不同“计算选项”对应不同聚合规则/色图（宿主仅转发，黑盒）。
3. IPA_T 的 1250 是什么？→ 宿主注释仅给尺寸与“彩色毯展图”；1250 为毯展纵向像素（长度轴），3=RGB（私有 LUT 细节不外推）。

## 6. DoD 打卡
- [x] 对照表完成（§3）

## 明日预告
改阈值 → 线程 Update → UI 信号：序列图（notes/W12_ipa_threads.md）。
