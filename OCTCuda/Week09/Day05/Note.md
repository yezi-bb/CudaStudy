# Week09 / Day05 — 学习记录（源码填充版）

> 主题：W09 REVIEW + IPA 预习——为 W10-12 的衰减系数(μ)计算铺路。
> 周复盘文件：`Week09/REVIEW.md`；Demo 文档：`notes/W09_continuous_calib_demo.md`。

## 1. 本周回顾
D1 远/近端 Stitching（帧范围 + 旋转对齐，各自 cut[0]，宿主 L5477-5478）→ D2 连续校准 GetContinuousCalibration（机型/新导管 → 每帧 cut[]，宿主 L6066/6094 等）→ D3 出图三兄弟（探测/全卷/单帧更新，宿主 L4285-6363）→ D4 端到端 Demo（连续 cut 稳定性收益量化）。

## 2. 连续校准/拼接 API 全景（cuh + 01 文档 §6）
| API | cuh 附近 | 一句话 |
| --- | --- | --- |
| `Get_Lumen_Stitching_FFT_Image` / `_Denoising_Data` | L387-388 | 两段卷按帧范围+旋转拼接 |
| `Continuous_Clibration_To_Circle_Image` | L392 | 单帧/小批探测出圆图 |
| `Get_All_Continuous_Calibration_Image` | L395 | 全卷按 cuts[] 重建矩形+圆图 |
| `Update_Frame_Continuous_Calibration_Image` | L398 | 单帧 cut 变化局部重算 |
| `C7C8_Get_All_Continuous_Calibration_Image` | ~L399 | 竞品数据源同管线入口 |
| `GetContinuousCalibration` | L418 | 机型/新导管 → 每帧 catheterCutStartHeight[] |

## 3. 周“抄作业”金句
1. **把单值参数升级成 per-frame 数组**是“参数随物理过程变化”的正解（cut→cuts[]）。
2. **渲染三粒度**（探测/全卷/增量）本质是“原语 + 缓存复用策略”的接口拆分。
3. **数据源适配器**（C7C8）让算法主链与采集/格式解耦。
4. **两段拼接**把“多源数据”封装成“单一数据源”，下游链零改动。
5. 每个“逐帧估计”都要配“时序约束”（中值平滑/相邻一致）抑制抖动。

## 4. IPA 预习（为 W10-12，真实源码）
### att_paras 结构体（VGPU_Process.cuh L161-178，16 字段）
```cpp
struct att_paras {
    float z0, zR, zC, zw;      // 成像/束腰几何：起点、瑞利长度、中心、束宽
    float SNRmax, noise_level; // 信噪比上限与噪声底
    int   minwin;              // 最小拟合窗（深度点数）
    float stepsucc, stepfail;  // 窗搜索成功/失败步长
    float scandepth;           // 扫描深度
    int   number_frames, number_depths, number_theta, number_alines; // 卷尺寸
    float step_success, step_fail; // 与上同义的更新量（保留两套命名）
};
```
### P60/P80/C7 参数分支（真实，IPAAlgorithmController.cpp L56-180）
| 分支 | 脂质阈值 | z0 | 含义（公开推理） |
| --- | --- | --- | --- |
| P60 | 9.5 | 0 | 60k A-lines/s 机型（扫频源） |
| P80 | 10.5 | 0.5 | 80k A-lines/s 机型，z0 偏移成像起点 |
| C7C8 竞品 | ~11 | — | 竞品数据换算后的阈值（01 §7 提 11/14） |
阈值被用于脂质斑块判定（输入 in_ipa_11_mat_cof）。宿主按机型填 att_paras 后调 GPU。
### 主线 API（W10-12 精读）
- `VGPU_Calculate_Ipa_Result`：每 A-line 在 lumen→media 窗内拟合衰减系数 μ（输出 μ 卷 + carpet_att）；
- `VGPU_All_Aline_Mu_Data_To_Image`：μ 方图体 → 每帧圆图；
- `VGPU_UpdateValueIPA`：改阈值后由线 μ 重算 IPA_L/RangeMean/IPA_A/IPA_T 毯展与 colorbar。

## 5. 合规边界（00 §7）复述
- 公开：att_paras **字段语义**（z0/zR/zC/zw、minwin、步长等是物理参数名，公开解释无损）；
- 私有：各机型的**具体标定真值**、内核对数拟合细节、脂肪阈值与样本标定关系（黑盒）。

## 6. DoD 打卡
- [x] W09 复盘 + IPA 预习完成（本 Note + REVIEW.md）
- [x] 能默写 att_paras 分组与 P60/P80 z0 差异

## 明日预告
Week10：IPA 参数准备（att_paras 逐字段、lumen/media 掩码输入、机型分支 P60/P80 填参全流程）。
