# Week03 / Day03 — 学习记录（源码填充版）

> 主题：存储/取出（U16↔F32）、Current_Frame 拍照回拷、After_Log。

## 1. 今日目标（回顾）
弄清“计算 F32、存盘 U16”的量化往返与拍照/导出回拷路径。

## 2. 真实声明（VGPU_Process.cuh）

```cpp
// L241 对压缩后的数据取Log
bool VGPU_Get_After_Log_Result(DOCMotionType status, float* h_Log_data, bool is_device_to_host);
// L252 取Log后的U16转F32        L255 F32转U16
bool VGPU_Get_U16fft_data_toF32fft_Result(U16*, int width,int height,int frame_number, float*);
bool VGPU_Get_F32fft_data_toU16fft_Result(float*, int width,int height,int frame_number, U16*);
// L258-259 传出当前帧FFT数据（拍照/保存原始数据，U16 输出、总是回拷）
bool VGPU_Get_Current_Frame_FFT_data(DOCMotionType status, U16* h_One_FFT_Power_data);
bool VGPU_Get_Current_Frame_FFT_After_Interpolation_data(DOCMotionType status, U16* h_One_FFT_Interpolation_data);
```

宿主关键调用（行号已核对）：
- ImageProcessingController.cpp L529-530 / L742-743：实时帧与回拉帧拍照前 `VGPU_Get_Current_Frame_FFT_data(doc, m_interpolation_pullback_data)`（取“插值谱”存原始）。
- RecordingThumbnailView.cpp L4945-4955：导入旧档生成缩略图时——若 `cutfront25` 标志则先裁（L4946），再 `F32fft→U16fft`（L4955）写入缩略图 buffer。
- 参数语义：`width = GetGlobalPointsNumberPerLineAfterFFTlength()`（1025）、`height = g_pullback_lines_number_(497)`、`frame_number=帧数`（回放整段 U16 数据的宽/高/帧三维）。

## 3. 为什么 F32 计算、U16 存盘？
- OCT log 谱动态范围有限，U16(65535 档) 足够存“可显示谱”，文件体积比 F32 减半；
- 分析/后续二次处理又要全动态范围 → 读回时反量化到 F32；
- 实时计算用 F32 避免反复量化的舍入累积。

## 4. 量化往返（练习：quantize_u16 / dequantize）

```cpp
struct QuantMeta { float scale; float offset; };   // v_f32 = (u16 / scale) + offset
uint16_t quantize_u16(float v, QuantMeta m){ float t = (v - m.offset)*m.scale; return (uint16_t)clamp(t,0.f,65535.f); }
float    dequantize (uint16_t q, QuantMeta m){ return (float)q / m.scale + m.offset; }
```
误差分析：单程舍入 ≤ 0.5 LSB → 相对误差 ~ 1/(2·65535) ≈ 7.6e-6（理想满档）；回读后 maxRel 应 ≪1e-3。Scale 必须写进文件元数据，否则不可逆。
（对产品端：其“固定 scale/offset”可在导入导出路径的注释/配置中找，属于导出元数据规范，不抄录。）

## 5. 宿主何时必须 D2H（笔记交付）
| 场景 | 为何必须回拷 |
| --- | --- |
| 拍照保存原始谱（L530/743 Current_Frame） | 文件系统在主存侧 |
| 导出重处理（ExportOCTdataView L898/991 true） | cv::Mat / 文件 |
| 缩略图/回放读 U16（RecordingThumbnail L4955） | 需要 u16 buffer 供 Qt/文件 |
| 实时圆图链（L521 后 DSC/Enhance/Gray2Color） | 不需要 → false |

## 6. 自测 Q&A
1. 存盘为什么要 U16 而非 F32？→ 体积减半、够显示档位；代价是二次分析需反量化（有元数据即可）。
2. Current_Frame 类 API 为何没有 is_device_to_host？→ 语义固定：拍照/保存必须回拷，无需开关。
3. cutfront25 什么时候介入？→ 旧记录曾把前 25 个点混入（多为无效/噪声段）；导入时按标志决定是否裁剪，保证后续 width 一致（见 Day04）。
4. width/height/frame_number 的宽度用哪个体量？→ AfterFFT 长度 1025（width）× 线数（height）× 帧数，三维来定位 U16fft 缓冲元素。
5. 量化往返误差能不能直接决定图像质量？→ 只是存储误差，远小于算法/log 域噪声，验收以“回读谱与原谱视觉/数值接近”为准。

## 7. DoD 打卡
- [ ] 量化往返误差表（写进代码/注释，§4）
- [ ] 理解存盘路径（§5 表）

## 明日预告
旧记录兼容 API（old_toLog / cutfront25 / denoising→Log）。
