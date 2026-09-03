# Week04 / Day01 — 学习记录（源码填充版）

> 主题：Transpose 与深度裁剪；CheckImage 用途；cut 与校准的关系。

## 1. 今日目标（回顾）
精读 `VGPU_Transpose(_CheckImage)`，搞清 `[start,end)` 的来源与 CheckImage 为何不裁剪。

## 2. 真实声明（VGPU_Process.cuh L261-263）

```cpp
/*对Log求和数据进行转置裁剪*/
bool VGPU_Transpose(DOCMotionType status, int start, int end, cv::Mat& Transpose_Mat, bool is_device_to_host);
bool VGPU_Transpose_CheckImage(DOCMotionType status, int start, int end, cv::Mat& Transpose_Mat, bool is_device_to_host);
```
宿主调用（行号已核对）：
- ImageProcessingController.cpp L495-496：`temp_cut_start_point = m_cut_start_point; temp_cut_end_point = m_cut_end_point;`
- L534：`VGPU_Transpose(doc, temp_cut_start_point, temp_cut_end_point, transpose_mat, false)`（实时裁剪转置）
- L762 / L794（verify purge / AFD 造影检测）：`VGPU_Transpose_CheckImage(doc, 0, m_gpu_imagme_points_number_after_fft_length, transpose_mat, false)` —— **0 到全深度 1025，不裁剪**

## 3. 转置语义
- 输入（device 侧 FFT 插值谱）布局：`行=线数(Ls/Lp)，列=每线深度点数(AfterFFT 长度 1025)`；
- 显示/圆图需要 **深度在行方向** → 转置成 `深度行 × 线列`；
- `[start,end)` 沿**深度维度**取有效段：把导管内无效近场与过深噪声裁掉，输出 `Transpose_Mat` 行数 = `end-start`、列数 = 线数。
- 裁剪点 m_cut_start/end 从哪来 → 校准结果（自动校准检测出导管位置与有效深度带后回填），见 L572-574 `VGPU_Catheter_AutoCalibration(...image_hight...)`；校准态 image_hight = `temp_cut_end - temp_cut_start`，且 `>7mm` 视野时统一按 7mm 折算（L562-564）。

## 4. CPU transpose+crop（练习黄金版）

```cpp
// 输入 src[lines][depth], 输出 dst[end-start][lines]
for (int d = start; d < end; ++d)
  for (int l = 0; l < lines; ++l)
    dst[d-start][l] = src[l][d];
```
（数据量 1000×1025 → 输出行数约 600~900，取决 cut。）

## 5. CheckImage 用途笔记（Day01 交付）
`_CheckImage` 与 `_Transpose` 的唯一差别=**裁剪范围/用途**：
- 实时显示：只转置“校准有效深度带”，省带宽且避免无效像素；
- 造影/断裂检测（L762/794）：需要**全深度**矩形图给检测算法找导管边界/造影剂形态 → 0..AFT 全深度、且通常不回拷（device 内直给后续检测 API）。

## 6. 自测 Q&A
1. 为什么转置而不是直接读列？→ 深度维度是内存连续的方向（转置后每行=一条深度 A-scan），DSC 按角度扫描读取更连续；不做 tile 转置则全局读非合并。
2. start/end 由谁定？→ 校准状态写入 m_cut_*；常规档为 0/全深度（CheckImage）或校准带。
3. 3mm vs 7mm 视野为何截断校准高？→ 只对可视区成像，避免无效深度参与校准匹配。
4. Transpose_Mat 用 cv::Mat 传参的意义？→ DLL 可直接按 Mat 布局写（row-major float），宿主侧零拷贝接入显示。

## 7. DoD 打卡
- [ ] CPU transpose+crop 正确（§4）
- [ ] cut 与校准关系、CheckImage 用途写明（§3/§5）

## 明日预告
CUDA shared-memory tile transpose（bank conflict + padding）。
