# Week06 / Day03 — 学习记录（源码填充版）

> 主题：方图/圆图批渲染（Handle_All_FFT_data / Handle_All_Calibration_Image）与数据来源分支。

## 1. 今日目标（回顾）
弄清 550 帧的方图/圆图如何“一函数出图”，以及校准前后两代接口的差异。

## 2. 真实声明与宿主调用

```cpp
// VGPU_Process.cuh L330
void VGPU_Handle_All_FFT_data(bool is_out_after_noise_data, float in_record_ground_noise,
    unsigned char* output_rectangle_data, unsigned char* output_circle_data,
    int start, int end, int output_circle_diameter,
    float in_low_boundary, float in_up_boundary);
// L333 校准后的整卷图像（icut_start/icut_size 取代 start/end）
void VGPU_Handle_All_Calibration_Image(bool is_out_after_noise_data, float in_record_ground_noise,
    unsigned char* output_rectangle_data, unsigned char* output_circle_data,
    int icut_start, int icut_size, int output_circle_diameter,
    float in_low_boundary, float in_up_boundary);
```
宿主（行号已核对）：
- 分析预览：IntegrationChannel.cpp L4225/4247 按数据来源选路后调用（传 `start/end` 深度裁剪、`output_circle_diameter`、矩形增强窗低高）；
- 校准图生成：ImageProcessingController.cpp L381 `VGPU_Handle_All_Calibration_Image(rectangle_data, circle_data, icut_start, rectangle_image_rows, g_circle_image_width_)`（此封装固定用当前校准的 icut 参数与圆图 704）。

## 3. 两代接口差异（DoD 口述）
| | `Handle_All_FFT_data` | `Handle_All_Calibration_Image` |
| --- | --- | --- |
| 深度段 | 调用方给 `start/end` | 用校准结果 `icut_start + icut_size`（自动） |
| 圆图直径 | 调用方给 | 同样调用方给（但常接校准的 704 宽） |
| 用途 | 预览/浏览方图圆图 | “校准后的图像”批出（进入纵切/拼接/回放缓存） |

其余相同：都“整卷一次出两组图”（方图 = 极坐标展开灰度图；圆图 = 每帧 DSC 圆图），输出 uchar 缓冲，按每帧方图+圆图写入由调用方按布局预分配的数组。

## 4. 数据来源分支（IntegrationChannel L4200-4250 概况）
- `GetGlobalPreviewPullbackDataType()`：
  - 自研/常规 U16-FFT 卷 → 直接 `Handle_All_FFT_data`（L4225）；
  - 竞品 C7/C8/DCM/raw → 先转成内部 FFT 布局（Week05 预习表那 3 个转换 API），再同一函数出图（L4247）。
- 语义：**对外统一“方图+圆图”产物**，来源差异在进入前被归一化。

## 5. 开源 render_all（骨架）
```cpp
struct RenderedVolume { std::vector<cv::Mat> rects; std::vector<cv::Mat> circles; };
// 1) 深度裁剪 [start,end) 每帧 → 灰度窗 [low,up] 到 uchar 方图
// 2) 每帧方图(DSC 复用 Week04 kernel) → 圆图 704
// 3) 组合 RenderedVolume（frames × 704×704 uchar）
// 与产品差异：产品一个 kernel 一次写两组卷；开源先帧级循环再优化
```

## 6. 自测 Q&A
1. 方图是什么形态？→ 极坐标展开（深度×线）灰度图；未做圆映射，适合校准/浏览与竞品对比。
2. 校准接口为什么换成 icut？→ start/end 在校准后变 icut（导管边缘裁剪段），接口语义表达“用已校准裁段”。
3. is_out_after_noise_data 参数何时 false？→ 想输出“去噪前/去噪后”两代产物（分析比较底噪影响）时切换。
4. output_circle_diameter 为什么独立参数？→ 圆图尺寸可不同于 Allocate 的 704（导出/缩略可小图），故调用方指定。
5. 整卷出图的 buffer 布局由谁定？→ 调用方预分配（帧数×每帧方图/圆图尺寸），DLL 按固定顺序写入——open 端要显式文档化，避免错位。

## 7. DoD 打卡
- [ ] 两代接口差异口述通过（§3）
- [ ] render_all 对合成小卷正确（§5）

## 明日预告
自适应对比度与单帧回放。
