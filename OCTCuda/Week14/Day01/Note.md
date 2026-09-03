# Week14 / Day01 — 学习记录（源码填充版）

> 主题：竞品与导入类 API——入口格式矩阵（raw/FFT/DCM/单帧）。

## 1. 今日目标（回顾）
四种导入入口各自“吃什么、出什么”；宿主导入主路径其实用哪几个；开源 ImportAdapter 如何解耦“解码”与“GPU 方图”。

## 2. API 声明（真实，VGPU_Process.cuh，行号已核对）
| API | L | 输入 | 输出 | 注释 |
| --- | --- | --- | --- | --- |
| `VGPU_PullbackRawData_To_FFT_Data` | 340 | U16 raw 全卷（width×height×frames） | U16 fft 全卷 all_rectangle（未裁剪） | .oct 竞品 raw → FFT |
| `VGPU_C7C8_PullbackFFT_Data_To_Image` | 343-344 | U16 fft 矩形全卷 | 矩形+圆（uchar，icut/直径参数化） | .oct 竞品 fft → 图 |
| `VGPU_PullbackDcm_Data_To_Image` | 347-348 | uchar DCM 矩形全卷 | 矩形+圆 | 竞品 dcm → 图 |
| `VGPU_PullbackRawData_To_Image` | 351 | U16 raw 全卷 | 矩形+圆 | 竞品 .oct raw → 图 |
| `VGPU_OneFrameRawData_To_Image` | 336 | U16 **单帧** raw + `start/end/low_boundary/up_boundary` | Mat 圆图 | 单帧（导入预览/缩略复用） |

**规律**：入口格式（解码层）不同，但都汇合到**同族“方图核 + 裁剪 + DSC”**——这就是“数据源适配器”（W09 C7C8 同款思维）的批量版。

## 3. 宿主真实调用（ImportationExportationController.cpp）
- L217/L593/L1251/L3871：主路径全是 **`VGPU_OneFrameRawData_To_Image(out_data_buffer(+i*rows*cols), icols, irows, out_mat, start, end, low_boundary, up_boundary)`**——宿主把竞品整卷按**帧切片**循环出圆图 push 到 `vec_mat_image`（L3874 另做 `transpose` 用于摆放）；即宿主很少用 340-351 批量四连，而是**解码后逐帧 OneFrame**。
- `start/end` 与 `low_boundary/up_boundary`：宿主把导入配置换算成“裁切窗 + 亮度上下界”（导入的显示窗）→ OneFrame 一条 API 覆盖 解码后一帧的完整成像（重采样→FFT→Log→DSC→增强 的“竞品入口版”）。

## 4. 开源 ImportAdapter（落点 oct::Import，对应 02 链 C）
```cpp
namespace oct {
// 解码层：不同文件 → 统一 U16 卷（与宿主“先解码再 OneFrame”对齐）
class ImportAdapter {
public:
    // kind: RawOct / FftOct / Dcm / DcmRaw…（当前统一按 U16/uchar 两种落点）
    bool load(const std::string& path, Kind kind, ImportSpec& spec); // 解码头+尺寸
    // 单帧取像：给定解码缓冲 → 调 oct::frame_pipeline 的单帧版
    bool to_frame_image(const U16* frame, int cols, int rows,
                        const WinSpec& win /*=start/end/low/up*/,
                        cv::Mat& outCircle);          // ← 等价 VGPU_OneFrameRawData_To_Image
    // 批量：decode_all → run 在统一卷上（复用 oct::E2E bulk）
};
}
```
**判断力**：真正需要“批量 340-351”只有“整卷导出前先预处理”场景；交互/缩略全走单帧（省显存、快）。接口设计应提供单帧+批量两条，宿主按需选。

## 5. 自测
1. 若竞品文件是 8bit DCM，导入矩阵该选哪个 API？→ 需要先转 U16/uchar 适配层（Dcm 输入是 uchar 矩形：选 PullbackDcm_Data_To_Image）。
2. 写导入流程图：解码→归一尺寸→（逐帧 or 批量）→方图核→圆图。

## 6. DoD 打卡
- [x] notes/W14_import_matrix.md 对照表完成

## 明日预告
缩略图与导出路径的 GPU 调用子集抽样（RecordingThumbnailView）。
