# W14 — 导入/竞品入口矩阵（私有学习笔记）

## 入口矩阵（cuh 行号已核对）
| 数据源 | API | 输入 | 输出 |
| --- | --- | --- | --- |
| .oct raw 整卷 | PullbackRawData_To_FFT_Data (L340) | U16 raw | U16 FFT 矩形（未裁剪） |
| .oct raw 整卷 | PullbackRawData_To_Image (L351) | U16 raw | 矩形+圆 uchar |
| .oct FFT 整卷 | C7C8_PullbackFFT_Data_To_Image (L343-344) | U16 fft | 矩形+圆 |
| DCM 整卷 | PullbackDcm_Data_To_Image (L347-348) | uchar | 矩形+圆 |
| 单帧 raw | OneFrameRawData_To_Image (L336) | U16 一帧 + start/end/low/up | 圆图 Mat |

## 宿主实际主路径
ImportationExportationController.cpp L217/L593/L1251/L3871：解码后**逐帧** OneFrameRawData_To_Image → vec_mat_image（L3874 transpose 摆放）。
批量 340-351 仅在“导出/预处理”场景。

## 开源对齐
oct::Import::ImportAdapter{load(kind), to_frame_image(frame), to_bulk(vol)}；与 oct::E2E bulk 复用。
