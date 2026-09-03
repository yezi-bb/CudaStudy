# Week03 / Day04 — 学习记录（源码填充版）

> 主题：历史记录兼容三 API（old_toLog / cutfront25 / Denoising_toLog）与导入分支设计。

## 1. 今日目标（回顾）
读透“已 Log 旧档 / 未裁前 25 点 / denoising 新版”三条还原路径，产出兼容层设计文档。

## 2. 真实声明与宿主分支（VGPU_Process.cuh L243-249；调用点已核对）

```cpp
// L243 旧记录数据Log逆变换: after_Log(f32,u16?) → before_Log(U16), 并带出记录时的 ground_noise
bool VGPU_Get_old_data_toLog_Result(float *h_after_Log_data, int width,int height,int frame_number,
                                    float &out_record_ground_noise, U16 *h_before_Log_data);
// L246 旧记录自动裁剪掉前25个点（现场）
bool VGPU_Get_old_data_cutfront25_Result(float *h_after_Log_data, int width,int height,int frame_number);
// L249 新记录(denoising) → Log
bool VGPU_Get_Denoising_data_toLog_Result(U16 *h_before_Log_data, int width,int height,int frame_number,
                                          float *h_after_Log_data);
```
- GpuHandlingDataThreadController.cpp L908-909：旧档还原（`fft_data_buffer` = 导入的 U16/Log 域全帧数据）→ `old_data_toLog_Result(... ground_noiseN, image_data_buffer)`：还原出 Log 前（或反量化 F32）的全帧。
- L947-952：按记录类型分支——`denoising_data_buffer`（新版记录，Log 前 U16）存在时：要 F32 全动态 → `U16fft→F32fft`（L948）；要 Log 显示/分析 → `Denoising_data_toLog`（L952）。
- RecordingThumbnailView.cpp L4945-4955 / GpuHandling L1178-1179：旧档若带“前 25 点”噪声（未裁），先 `cutfront25_Result` 再 F32→U16 重建缩略/分析 buffer。

## 3. 三条路径差异（一句话版）
| 数据代 | 存的是什么 | 载入要做的 |
| --- | --- | --- |
| 旧·已 Log | Log 后（U16/F32 皆见） | `old_toLog` = 撤销 log/量化，还原出 log 前 U16（或含 ground_noise 校正） |
| 旧·未裁前 25 | Log 后且头部有 25 点杂讯 | 先 `cutfront25` 把每线前 25 点裁掉再走旧路径 |
| 新·denoising | 去噪后 Log 前 U16 | 要 F32 → `U16fft→F32fft`；要显示/分析 → `Denoising_toLog` |

差异本质：**新版记录在 Log 之前落盘（信息更全，可再 Log 或全动态 F32）；旧版落盘已含 Log，只能逆变换还原，且兼容历史 bug（前 25 点）**。

## 4. 兼容层设计（参考，可作为 W03_legacy_log 文档内容）
```cpp
struct RawFileMeta { enum class Kind { OldLogged, OldLogged_Cut25, NewDenoising } kind; int w,h,frames; float ground_noise; };
// 载入 → “规范化 buffer”：Log 后 F32 (width×height×frames)
float* loadToPostLog(const RawFileMeta& m, const void* fileData) {
  switch (m.kind) {
    case OldLogged:        // 已是 log 后：可能先裁25 → F32
      if (cut) cut_front(m, data);            // cut_front(n) 实现: 每行后移 n 个点
      return u16ToF32(data, m);
    case NewDenoising:     // log前 U16 → 做 log
      return denoiseToLog(data, m);
  }
}
```
`cut_front(n)` 要点：行主序下对每行 `dst[0..w-n)=src[n..w)` 左移，只在 head 有效；注意 w 变为 `w-n` 后要更新后续 width 使用处。

## 5. 新旧差异总结（DoD 一句话）
新 = Log 前去噪存档（可逆到 F32、可重 Log）；旧 = Log 后存档（只能撤销，且带 ground_noise 与 cut25 历史包袱）。GpuHandlingDataThreadController 的 `flag` 判断即据此两路分发。

## 6. 自测 Q&A
1. 为什么“新版”比“旧版”好？→ Log 前的原始（去噪）信息保留了做更多后处理的自由度；Log 后丢失高动态细节。
2. cutfront25 是裁剪数据还是标头？→ 裁每线头部 25 个无效/噪声谱点，保证后续 width 语义一致。
3. `old_data_toLog` 输出 out_record_ground_noise 干什么？→ 旧档撤销时把记录当时的底噪带出，供后续链路复现当时增益。
4. 兼容层放 host 还是 device？→ 载入阶段 host 编排、大块变换交给批量 API（整段 width×height×frames 一次入 GPU）。
5. 新老路径最终汇合在哪？→ 汇合到“Log 后 F32 的全帧 buffer”，后续 Transpose/DSC/分析无感。

## 7. DoD 打卡
- [ ] 能说清旧数据（含 cut25）与新 denoising 的差异（§3/§5）
- [ ] 兼容层设计已落笔记（§4 可作为文档底稿）

## 明日预告
对照回拉融合 API `Pullback_ProcessData_ToImage`；写 W03 REVIEW。
