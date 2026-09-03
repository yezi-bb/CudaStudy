# Week14 / Day02 — 学习记录（源码填充版）

> 主题：缩略图与导出路径的 GPU 调用子集抽样（RecordingThumbnailView / ImportationExportationController）。

## 1. 今日目标（回顾）
在 RecordingThumbnailView 里抓“回拉→缩略图”实际用到的 VGPU_ 子集，理解“为何缩略走少量 API 而不用全链”。

## 2. 调用子集列表（真实，RecordingThumbnailView.cpp，行号已核对）
| 行 | API | 语义 |
| --- | --- | --- |
| L4786-4789 | `VGPU_GetCudaErrorStatus()` | 启动保护：出错则自动关机提示（“auto shut down”） |
| L4872 | `VGPU_PullbackRawData_To_FFT_Data(out_data_buffer, icols, irows, use_iframes, fft_data_buffer)` | 缩略数据源：.oct raw 直接整卷变 U16 FFT（与 W14D1 批量入口复用） |
| L4946 | `VGPU_Get_old_data_cutfront25_Result(...)` | 旧数据处理：裁掉前 25 类残留段（竞品偏移补偿） |
| L4955 | `VGPU_Get_F32fft_data_toU16fft_Result(...)` | F32→U16 FFT 压缩，供后续/导出 |
| L5065 | `VGPU_OneFrameRawData_To_Image(out_data_buffer, icols, irows, out_mat, start, end, low, up)` | **抽样帧** 出圆图 = 缩略帧 |

## 3. 为什么缩略图“走少量 API”
- 缩略只展示**少量抽样帧**（不必 550 帧全 DSC）→ 抽样帧走单帧 OneFrame（W14D1）即可；
- 数据源若为竞品 .oct：先一次 `PullbackRawData_To_FFT_Data` 得到整卷 FFT（只算 FFT 不做裁剪/成像，为抽样取帧做“就绪”），再对抽样帧出图；
- **F32→U16** 出现两次（L4955/…）说明导出/缩略链路用 U16 作为“交接格式”（省显存、快拷，W02/03 双精度互转的实践场景）；
- L4786 把“CUDA 错误”当**整机安全事件**（OCT 设备不能带病采集）→ 关机保护是产品纪律（W01 已见同款）。

## 4. 导出路径（ImportationExportationController）
- 出图复用同一批渲染 API（逐帧出 circle → CPU 侧/OpenCV 组 AVI/图像序列/单帧导出）；
- 数据准备走 U16 FFT 交接；**没有专用“导出核”**——导出 = “把回放/导入用的图再编码一次”，这正是架构上“一个成像链多处复用”的证据。

## 5. 开源对照（oct::Export，落点）
```cpp
namespace oct {
struct ExportPlan { bool video; bool images; int sampling; };
class Exporter {
public:
    // 复用 E2E 的 process_frame：抽样帧 → circle → cv::VideoWriter / imwrite
    void run(const VolumeU16& vol, const CutCalib& cut, ExportPlan p);
};
}
```
（核心观点：缩略/导出不是新算法，是**同一个 process_frame 的抽样与编码**。）

## 6. DoD 打卡
- [x] 调用子集列表完成（§2 表；notes/W14_thumbnail_subset.md 归档）

## 明日预告
NVAPI 温度与显示控制（广度）——GpuController / SystemDiagnosticsView / GPUDisplayConfigController。
