# W14 — 缩略/导出 VGPU 子集（私有学习笔记）

## RecordingThumbnailView.cpp 实际子集
| 行 | API | 用途 |
| --- | --- | --- |
| 4786 | GetCudaErrorStatus | CUDA 错误 → 自动关机保护 |
| 4872 | PullbackRawData_To_FFT_Data | .oct raw → 整卷 U16 FFT |
| 4946 | Get_old_data_cutfront25_Result | 裁前 25 残留补偿 |
| 4955 | Get_F32fft_data_toU16fft_Result | F32→U16 交接格式 |
| 5065 | OneFrameRawData_To_Image | 抽样帧出缩略圆图 |

## 结论
- 缩略/导出 = 同一成像链的“抽样 + 编码”，无专用核。
- U16 FFT 是交接/导出格式。
- CUDA 错误按整机安全事件处理。
