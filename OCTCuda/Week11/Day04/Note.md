# Week11 / Day04 — 学习记录（源码填充版）

> 主题：μ 方图 → 圆图（VGPU_All_Aline_Mu_Data_To_Image 等价实现，复用 DSC）。

## 1. 今日目标（回顾）
看清 All_Aline 的签名与宿主单帧调用（ProcessingOneFrame L400-410），把 μ 体当“强度方图”走 W04 的 DSC 管线量化出 uchar 圆图 PNG。

## 2. API 原型（真实，VGPU_Process.cuh L455-456）
```cpp
bool VGPU_All_Aline_Mu_Data_To_Image(
    float* all_aline_mu_data,    // μ 体（布局同 DSC 的方图卷）
    int iwidth,                  // 一线点数 = RawToFFTDataCols (1025) → “列/深度”
    int iheight,                 // 一帧线数 = RawToFFTDataRows (500) → “行/θ”
    int ipullback_frames,        // 帧数（1=单帧）
    unsigned char* output_circle_data, // 8bit 圆图
    int* icut_start,             // 每帧 cut（宿主传 GetGlobalCutHeightStart()）
    int icut_size,               // 裁剪大小（宿主 cut_size_）
    int output_circle_diameter,  // 圆图边长（宿主 g_circle_image_width_）
    bool isVivoData);            // 是否微光（影响量化噪声门限）
```
**观察**：签名与 DSC（W04）几乎同构——μ 方图被当作强度图做“裁剪→DSC→量化(uchar)”。

## 3. 宿主单帧路径（真实，ProcessingOneFrame L399-410）
```cpp
VGPU_All_Aline_Mu_Data_To_Image(single_frame_miu_gray_array, // 本帧 μ（rows*cols）
    GetGlobalRawToFFTDataCols(), GetGlobalRawToFFTDataRows(), 1,
    single_circle_image_buffer,      // uchar[g_circle_width_*g_circle_height_]
    GetGlobalCutHeightStart(),       // cut 数组（按帧取，此处单帧仍传数组）
    this->cut_size_, g_circle_image_width_, isVivoData);
memcpy(ipa_circle_images_data_array_ + frame_id*W*H, single_circle_image_buffer, W*H); // L409
```
要点：**单帧重建** = 从整卷 μ 指针里按帧取 → 单帧 μ 圆图 → 写回全卷圆图序列对应位置（增量更新，W09 的缓存思维复现）。

## 4. 开源实现（复用 oct::Dsc）
```cpp
// 1) 裁剪：只取 [icut_start, icut_start+icut_size) 深度段
cv::Mat polarMu(h, cut_size, CV_32FC1); // h=theta, 每行一段
// 2) DSC：极坐标→圆（用 W04 已实现的 oct::Dsc::polar2cart）
cv::Mat circleFloat = oct::dsc_polar2circle(polarMu, /*diameter=*/g_circle_w);
// 3) 量化到 uchar：μ 范围 [0, μmax] 线性映射（教学用，产品有真值标定——黑盒）
cv::Mat circleU8;
cv::normalize(circleFloat, circleU8, 0, 255, cv::NORM_MINMAX, CV_8UC1);
cv::imwrite("ipa_mu_frame_" + std::to_string(f) + ".png", circleU8);
```

## 5. 自测与验收
1. W11D2 的 cpu_volume_mu 出 μ 卷 → 逐帧出圆图 PNG；
2. 合成 μ 体：深度 300-600 处 μ=0.9（矩形带）→ 圆图应见**圆环带**（带半径随 cut 变化）——验证 DSC 方向正确；
3. cut 数组变化：icut_start 递增 10 → 圆环内半径随之移动（验证 icut 生效）；
4. 8bit 量化：μ=0 区应为黑，带区灰亮（无伪彩即可，W12 才有毯展 LUT）。

## 6. DoD 打卡
- [ ] 复用 oct::Dsc 出 μ 圆图 PNG（3 组 cut 验证）

## 明日预告
两路输出用途（line_ipa_miu / carpet）+ 输出缓冲字典 + W11 REVIEW。
