# Week04 / Day03 — 学习记录（源码填充版）

> 主题：DSC 全部参数与极→直坐标公式；CPU 最近邻出图。

## 1. 今日目标（回顾）
吃透 DSC 语义（回拉时是极坐标 rect → 血管圆图），手推坐标映射公式并用 CPU 最近邻实现第一版圆图。

## 2. 真实声明与枚举（VGPU_Process.cuh L265-267 / L93-99）

```cpp
bool VGPU_DSC(DOCMotionType status, int raw_rows, int raw_cols, float* h_DSC_data,
    int polar_rows, int polar_cols, int inner_r, int margin_r,
    InterpolateType interpolate_method, bool is_device_to_host);
// L93-99
typedef enum { INTER_AJACENT = 1 /*最邻近*/, INTER_BILINEAR /*双线性*/, INTER_BITRIPLE /*三次双卷积*/ } InterpolateType;
```
宿主实时调用（ImageProcessingController.cpp L625）：
```cpp
VGPU_DSC(doc_motion_type,
    temp_cut_end_point - temp_cut_start_point,   // raw_rows=裁剪后的深度行
    g_scan_lines_number_,                        // raw_cols=每帧线数(360° A线数)
    m_dsc_data,                                  // 输出浮点圆图缓冲
    g_circle_image_height_, g_circle_image_width_, // polar=704×704
    0, 0, INTER_BILINEAR, false);
```

## 3. 语义：输入极坐标 rect，输出笛卡尔圆图
- 输入 rect（转置+裁剪后）：`raw_rows × raw_cols`，行=深度采样（从导管中心向外），列=0..359° 的 A 线。
- 输出 polar：704×704 方阵；导管中心在图像中心 (352,352)。
- `inner_r`：成像环带内半径（跳过导管遮挡/近场），`margin_r`：外缘留边裁剪；两者都=0 时全图外圆画。
- 插值：像素映射到 rect 上的非整数位置 → 最近邻/双线性/三次取样。

## 4. 坐标公式（手推，写入笔记）
对输出像素 (x,y)（0-based）：
```
cx = polar_cols/2; cy = polar_rows/2;
dx = x - cx; dy = y - cy;
r   = sqrt(dx*dx + dy*dy);
th  = atan2(dy, dx);                    // [-π, π]
col = ((th + π)/(2π) * raw_cols) mod raw_cols;   // 角度 → 线号
row = (r - inner_r) / dr + 0;           // 半径 → 深度行号（dr=采样/显示比例，见下）
if (row < 0 || row >= raw_rows - margin_r) → 置 0（越界/导管内/边缘外）
```
`dr` 推断（据 3/7mm 视野与校准）：
```
有效直径 D_mm（视野）；图像内半径范围 r∈(inner_r, H/2-margin_r)
rect 有效深度区间长 = end-start（A-scan 采样段）
dr ≈ (有效像素半径)/(end-start)
```
> 真实产品用“标定出的 mm/像素 + 采样间隔”换算；学习版用可调 `dr` 常量并留接口，视觉对齐即可。

## 5. CPU 最近邻 DSC（黄金版骨架）

```cpp
for (int y=0;y<H;y++) for(int x=0;x<W;x++){
  float dx=x-cx, dy=y-cy; float r=sqrtf(dx*dx+dy*dy);
  float th=atan2f(dy,dx);
  int col = (int)roundf((th+PI)/(2*PI)*raw_cols) % raw_cols;
  int row = (int)roundf(r/dr);
  float v = (row>=0 && row<raw_rows) ? src[row*raw_cols+col] : 0.f;
  out[y*W+x] = v;
}
```
出图检查：合成 rect（如模拟 3 个亮斑/字母 C）→ 圆图应呈现“环形正确对应到角度”；导管中心区域为 0。

## 6. 自测 Q&A
1. raw_rows/raw_cols 分别是转置图的什么？→ 行=深度(裁剪后)，列=角度/A线。
2. polar 704 与 raw_cols=1000 什么关系？→ 圆图只采 360°，外圈像素< 2π·352≈2212 个采样需求，用 1000 线+插值足够；704 是显示方图分辨率。
3. inner_r/margin_r=0 时为何还画得对？→ 中心为导管盲区但无掩膜时靠“row<0/越界写 0”兜底；实际产品用它们裁导管鞘。
4. 最近邻 vs 双线性各在什么阶段用？→ 实时(显示质量)双线性（L625 INTER_BILINEAR）；检测/检查图常最近邻省时间。
5. atan2 值域与 col 映射为什么 +π？→ atan2∈[-π,π]，平移成正 [0,2π) 再乘线数取整取模。

## 7. DoD 打卡
- [ ] 公式手推完成（§4）
- [ ] CPU 最近邻 DSC 出图正确（§5 自检）

## 明日预告
双线性 DSC：CPU 黄金版 + CUDA naive。
