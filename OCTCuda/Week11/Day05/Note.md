# Week11 / Day05 — 学习记录（源码填充版）

> 主题：Calculate 两路输出（μ 体 / line μ）后续用途 + 输出缓冲字典 + W11 REVIEW。

## 1. 两路输出的宿主归宿（真实）
- `out_all_aline_mu`（μ 体 float）：单帧 → 直接 All_Aline_Mu_Data_To_Image 出圆图；全卷 → 宿主先存于 `miu_gray_array_`，之后整卷出图/保存。
- `out_carpet_att` / `line_ipa_miu`（每 A-line 一个代表 μ，float[alines]）：
  - IPAProcessing L289-290：全卷存 `pre_ipa_analysed_result.line_ipa_miu[frames*theta]`；
  - ProcessingOneFrame L435：单帧只覆写 `frame_id*theta` 段；
  - **消费方**：W12 的 `VGPU_UpdateValueIPA(InlineIPA=line_ipa_miu,…)`（cuh L478-480 注释明确 InlineIPA = 回拉序列线IPA值结果）。
  > cuh L432 名 `out_carpet_att`（μ值结果/毯展相关）；宿主保存名 `line_ipa_miu`——同一缓冲两个名字，笔记统一记“每线 μ”。

## 2. 输出缓冲字典（交付物）
| 名称 | 宿主字段/成员 | 尺寸 | 分配/写 | 消费 | 说明 |
| --- | --- | --- | --- | --- | --- |
| line μ | pre_ipa.line_ipa_miu（float*） | frames×theta | L289-290 全卷 / L435 单帧覆写 | W12 UpdateValueIPA InlineIPA | 每 A-line 代表衰减 |
| frame IPA | pre_ipa.frame_ipa_result（double*） | frames | L287 分配（“暂无使用”注释） | 预留帧级聚合 | — |
| μ 体 | IPAAlgorithmController::miu_gray_array_ | frames×theta×depth | L221 分配、L242 输出 | All_Aline_Mu_Data_To_Image | 仅全卷路径 |
| μ 圆图 | ipa_circle_images_data_array_（uchar*） | frames×gW×gH | L409-410 覆写帧 | UI/SetIpaCircleImagesDataArray(L438) | 8bit |
| 阈值 | pre_ipa.threshold（float） | 1 | L292 | UpdateValueIPA InThresholdT | 9.5/10.5/11 |
| 类型 | pre_ipa.is_vivolight_ipa（bool） | 1 | L293 | UpdateValueIPA isVivolightIPA | P60/P80 vs C7C8 |
| 帧距 | pre_ipa.lpixel_sapcing（double） | 1 | L294（GetPixelSpacing()[2]） | UpdateValueIPA pixelSapcing | mm/帧 |
> 更新路径：轮廓变化 → `UpdateWhileLumenContourChange/UpdateWhileICAContourChange`（L307-341）→ `ProcessingOneFrame(frame)`（L344）→ 逐帧覆写 line μ + μ 圆图 → UI 刷新。即“**只重算被改的帧**”。

## 3. 开源侧（照字典对齐）
```cpp
struct IpaBuffers {
    std::vector<float> mu_vol;      // frames*theta*depth  （μ 体）
    std::vector<float> line_mu;     // frames*theta         （每线代表，=carpet 名）
    std::vector<uchar> circle_u8;   // frames*gW*gH         （μ 圆图）
    // update_frame(k) 仅重算第 k 帧三块对应段
};
```

## 4. 本周 REVIEW（口述）
D1 单线拟合（对数最小二乘/噪声窗跳过）→ D2 卷 + 简化掩膜（lumen_b/labels/media=100 截断）→ D3 CUDA 一 A-line 一 block（shared 载线、块内归约、GPU≈CPU<1e-4）→ D4 μ 圆图复用 DSC（单帧/全卷 = 帧偏移 + 写回）→ D5 缓冲字典（line μ→UpdateValueIPA）。

## 5. 合规
μ 量化 LUT 为教学 normalize；产品 μ↔组织学映射为黑盒；SPEC 首行免责声明已列（W10D4）。

## 6. DoD 打卡
- [x] 输出缓冲字典完成（§2）
- [x] Week11/REVIEW.md 已生成

## 明日预告
Week12：`VGPU_UpdateValueIPA`（改阈值重算毯展与色图）与 BackgroundIPA/IPAZone 线程。
