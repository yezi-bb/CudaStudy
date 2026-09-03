# Week06 / Day04 — 学习记录（源码填充版）

> 主题：自适应对比度（CalculatedContrastRange）+ 单帧回放（Hnad_One_Frame / OneFrameRawData_To_Image）。

## 1. 今日目标（回顾）
理解暗/亮图像自动定窗（black/white level）与“单帧取图”两类接口。

## 2. 真实声明与宿主调用

```cpp
// VGPU_Process.cuh L360
bool VGPU_CalculatedContrastRange(float& low_boundary, float& up_boundary);   // 返回是否暗图像
// L365
void VGPU_Hnad_One_Frame_Data(int iframe, Mat& out_mat, int start, int end,
    float low_boundary, float up_boundary, GrayEnhanceType enhance_type, float coefficient_for_enhance);
// L336
bool VGPU_OneFrameRawData_To_Image(U16* raw_data, int iwidth, int iheight,
    Mat& out_mat, int start, int end, float low_boundary, float up_boundary);
```
宿主（行号已核对）：
- ImageProcessingController.cpp L1296-1301：`CalculatedContrastRange(low,up)` 封装；
- IntegrationChannel.cpp L535/577：注释明确“**不用传图像参数，图像已在调用 SetOriginalFftImageData()/…ForPci() 时设置在 GPU 上**”，返回 black_level/white_level，并用返回值判断“是不是暗图像”。
- Hnad_One_Frame_Data：ImageProcessingController.cpp L1505/1509（实时播放模式，LinearEnhanceType 或 PowEnhanceType + `GetGlobalDefaultGammaValue()`），L1529/1533（录制回放用 `GetGlobalCurrentRecordGammaValue()`）；
- OneFrameRawData_To_Image：RecordingThumbnailView.cpp L5062-5065（缩略图：`low=50,up=130` 硬编码默认窗，704×704 出图）、ImportationExportationController.cpp L217/L593/L1251/L3871（导入竞品/单帧导出逐个 raw 帧 → 圆图 Mat）。

## 3. 自适应窗原理（学习实现）
- 背景：回拉卷 FFT/去噪后动态范围随卷而异（暗卷、高噪声卷）；固定窗会全黑/全白。
- 产品做法：对“已在 GPU 的整卷 FFT 数据”统计亮度分布（无需传图像参数 → 数据已被 Set* 送入 GPU），得到 black_level（如低分位）/white_level（如高分位），返回 bool 提示暗图像（如整体过低）。
- 宿主用它更新 `m_low_boundary / m_up_boundary`，驱动后续方/圆图与 Hnad_One_Frame 的窗。
- open 端参考：对 fft 卷做分位数（percentile 1%/99%）或直方图累计找 0.1%/99.9%；> 计算一次后缓存，供每帧增强用。

## 4. 单帧取图两条路（笔记交付）
| 接口 | 输入 | 场景 | 特点 |
| --- | --- | --- | --- |
| `Hnad_One_Frame_Data(iframe,…)` | **GPU 内整卷 + iframe** | 回放/逐帧浏览 | 已有 FFT 卷；不重算 FFT；可带增强类型与 gamma |
| `OneFrameRawData_To_Image(raw, w,h,…)` | **单帧 raw U16** | 缩略图/竞品单帧导入导出 | 即用即算（单帧全链）；low/up 由调用方给（缩略图 50/130） |

## 5. 自测 Q&A
1. CalculatedContrastRange 为什么没图像参数？→ 数据已由 Set* 接口驻留 GPU，属于“对已驻留卷的统计”，参数自然少。
2. 返回值“bool”含义？→ 是否暗图像（判断黑屏还是真暗卷），宿主可据此提示“请确认探头/介质”。
3. Hnad_One_Frame 与实时单帧链区别？→ 前者只从**已算好的卷**取一帧（重放、快、可任意跳帧）；实时链是逐帧算完即显。
4. 缩略图默认 50/130 为什么硬编码？→ 缩略图只求“看清轮廓”，统一窗省去每卷统计，快速渲染。
5. 为何回放 gamma 用 Record 而实时用 Default？→ 回放要还原录制时选择的增强曲线，实时用当前默认曲线——两者独立，避免“重放看起来不同”。

## 6. DoD 打卡
- [ ] 自适应窗（分位数）CPU 版可算出 black/white（§3）
- [ ] 单帧两路差异表完成（§4）

## 明日预告
W06 复盘 + W07 校准预习。
