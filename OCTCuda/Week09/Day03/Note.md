# Week09 / Day03 — 学习记录（源码填充版）

> 主题：连续校准出图三兄弟——预处理 / 全卷 / 单帧更新，以及竞品 C7C8 数据源入口。

## 1. 今日目标（回顾）
拆分三个 API 的定位（全量 vs 增量 vs 单帧探测），搞清它们如何消费 Day02 的 `cuts[]` 数组（宿主即 `GetGlobalCutHeightStart()`）；掌握“渲染原语 + 组合”的接口设计。

## 2. API 全景（01_API接口全解.md §6，cuh 对应 L390-400）
| API | 定位 | 关键输入 | 输出 |
| --- | --- | --- | --- |
| `VGPU_Continuous_Clibration_To_Circle_Image` | **预处理/探测**：给若干目标帧号，按 cut 直接出圆图（预览阶段用，量小） | frame_number 列表、各帧 cut | 圆图 |
| `VGPU_Get_All_Continuous_Calibration_Image` | **全卷重建**：整卷按 `cuts[]` 一次性出矩形+圆图 | output_rectangle_data、output_circle_data、`icut_start=GetGlobalCutHeightStart()`（逐帧数组） | 全卷矩形/圆图 |
| `VGPU_Update_Frame_Continuous_Calibration_Image` | **单帧增量**：某帧 cut 变化后只重算那一帧（交互刷新） | update_frame（帧号）、cut_height_value | 该帧圆图刷新 |
| `VGPU_C7C8_Get_All_Continuous_Calibration_Image` | 竞品 `.oct` 数据源的**同管线全卷**入口 | 竞品矩形数据（U16 全卷）+ iwidth/iheight/ipullback_frames | 矩形+圆图 |

## 3. 宿主真实落点（IntegrationChannel.cpp，行号已核对）
- `Get_All_Continuous_Calibration_Image`：L4285 / L4360 / L6192 / L6284——四路数据场景共用，入参均含 `output_rectangle_data/output_circle_data`，`icut_start` 传 `GetGlobalCutHeightStart()`（**数组**）；
- `C7C8_Get_All_Continuous_Calibration_Image`：L4291 / L4366 / L6198 / L6290——与上面并排的竞品分支；
- `Update_Frame_Continuous_Calibration_Image`：L6361-6363——传 `update_frame`（帧号）+ `cut_height_value`（该帧新 cut），做单帧局部重算。

## 4. 设计意图（抄作业重点）
“全卷重建”计算量大（550 帧 × 每帧 矩形+圆图），但**交互只需要改某一帧**（用户拖动 cut 微调第 k 帧时）。接口最小集：
```
render(k)           = 探测单帧            → Continuous_Clibration_To_Circle_Image
render(all|cuts[])  = 全量批重建          → Get_All_Continuous_Calibration_Image
render(k, new_cut)  = 局部更新（其余帧缓存复用）→ Update_Frame_Continuous_Calibration_Image
```
`C7C8` 说明“**数据源不同不影响算法主链**”：竞品卷先做格式/类型适配，再进同一全卷重建。

## 5. 开源学习实现（落点 OCTCudaProject）
```cpp
// 渲染原语：给定第 k 帧极坐标 + 该帧 cut → 矩形(裁剪) + 圆图(DSC，复用 W04)
void render_frame_polar_to_circle(const std::vector<float>& polar, int lines, int depth,
                                  int cut_start, int cut_size, cv::Mat& rect, cv::Mat& circle);

// 组合1：全卷重建（对照 Get_All_Continuous_Calibration_Image）
void render_all(const std::vector<float>& volume, int lines, int depth, int frames,
                const std::vector<int>& cuts, std::vector<cv::Mat>& circles)
{
    circles.resize(frames);
    for (int k = 0; k < frames; ++k) {
        std::vector<float> frame(volume.begin() + (size_t)k*lines*depth,
                                 volume.begin() + (size_t)(k+1)*lines*depth);
        int cut_size = std::min(depth - cuts[k], 512);   // 说明：尺寸按实际裁剪带
        render_frame_polar_to_circle(frame, lines, depth, cuts[k], cut_size,
                                     /*rect=*/tmp, circles[k]);
    }
}
// 组合2：单帧更新（对照 Update_Frame_Continuous_Calibration_Image）
//  —— 只需重算 k 帧，其余帧缓存 circle[!k] 不动
void update_frame(int k, int new_cut, std::vector<cv::Mat>& circles,
                  const std::vector<float>& volume, int lines, int depth)
{ /* 取 k 帧 + new_cut → 只覆写 circles[k] */ }
```

## 6. 自测
1. 用 W09D2 的 cuts[] 渲染整卷，圆图每帧导管高度应基本一致（连续 cut 生效）；
2. 对比“统一 cut”渲染：漂移大的帧导管区明显错位/被切；
3. 对第 100 帧调 new_cut=150 后 update_frame，验证只有 circles[100] 变化、其余帧引用同一对象（缓存复用）。

## 7. 自测 Q&A
1. 三个 API 何时各自被用？→ 预览探测用 To_Circle；全卷回放/导出用 Get_All；用户微调第 k 帧用 Update_Frame。
2. icut_start 为什么在宿主里成了“数组指针”？→ 连续校准按帧取 cut（W09D2 输出），因此重建按帧索引。
3. C7C8 全卷与自采全卷差别在哪一层？→ 只在数据源格式/尺寸适配层，算法主链共用（这正是“适配器”思维）。
4. 全卷重建 550 帧会不会卡 UI？→ 宿主放在后台线程/分帧处理；交互性靠 Update_Frame 单帧补偿。
5. “渲染原语 + 组合”和直接三个 API 有何差别？→ 差别在缓存策略暴露：增量接口让宿主决定哪些帧可复用，避免每帧全量重算。

## 8. DoD 打卡
- [ ] render_frame / render_all / update_frame 三件套实现，三类自测通过
- [ ] 画清“cuts[] → 三 API 组合 → 界面刷新”的数据流

## 明日预告
W09 Demo：连续 cut 渲染对比 + 两段 stitch 联调，并写简短文档（notes/W09_continuous_calib_demo.md）。
