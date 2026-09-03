# Week05 / Day05 — 学习记录（源码填充版）

> 主题：链 A 复盘、简历句草稿、W06 预习清单。

## 1. 今日目标（回顾）
把 e2e 成果固化为可演示 demo 与“一句简历”，并列出 Week06 回拉批处理 API 预习表。

## 2. Week05 REVIEW 底稿（抄进 `Week05/REVIEW.md`）

**API 范围**：`VGPU_Image_Enhancement`（4 种 GrayEnhanceType，宿主默认 Linear/Pow+L634-640）、`VGPU_Gray2Color`（LUT 256×3、BGR、host ColorsMapType）、`VGPU_Data_Power_aline(_Vivo)`（旁路统计）、链 A 全部主干。
**核心结论**：
1. 增强 = DSC 浮点圆图 → 显示窗 `[low,up]` + gamma 映射 → uchar 灰度；
2. 伪彩查表逐像素，实时唯一 `true` 的显示回拷点；
3. 链 A：`Resample(511)→FFT+Interp(521)→Transpose(534)→DSC(625)→Enhance(636)→Gray2Color(651)`，中间全 KeepDevice；
4. Power_aline 独立于显示链（保留底噪/不做有损压缩）。
**e2e**：`run_scan_frame` 已跑通；合计 `___ ms/帧`。

## 3. 简历句草稿（数字先占位，随后补真实）
> “从零实现血管内 OCT GPU 实时成像管线（重采样/加窗→cuFFT→对数谱→极坐标转直 DSC 圆图→增强→伪彩），逐级与 CPU 黄金版 diff（≤1e-3）；单帧 1000×2048 处理 __ms，相比 CPU 快 ~__ 倍，达到实时 60fps 预算。”

## 4. W06 预习清单（回拉批处理 API，均已在 VGPU_Process.cuh 见声明）
| API | 作用（按注释） |
| --- | --- |
| `VGPU_Check_pullback_Data_memory` | 为整段回拉检测分配显存 |
| `VGPU_Set_Original_pullback_Data_To_GPU` | 回拉结束后整段 raw（U16/U8vivo）传 GPU |
| `VGPU_Handle_All_Preview_data` | 对所有帧生成 FFT 数据（预览） |
| `VGPU_Get_All_FFT_data` | 取所有帧 FFT 后 U16 回 CPU |
| `VGPU_Handle_All_FFT_data` | 生成方图+圆图（含去噪开关/start,end/直径/窗） |
| `VGPU_Handle_All_Calibration_Image` | 校准后图像批量生成 |
| `VGPU_OneFrameRawData_To_Image` / `Hnad_One_Frame_Data` | 单帧 raw/单帧回显（重放用） |
| `VGPU_CalculatedContrastRange` | 自适应对比度窗 |
| `VGPU_PullbackRawData_To_FFT_Data` 等 3 个 | 竞品数据兼容（.oct/.dcm/raw） |

## 5. 自测 Q&A
1. 简历句为什么强调“diff ≤1e-3 + ms 数 + fps 预算”？→ 可验证的正确性 + 可量化的性能 = 面试官能立刻判断你“真的会写 kernel”。
2. W06 的核心难点预测？→ 批量显存规划（550 帧）与“边扫边算 vs 结束后整段”状态机。
3. 为什么竞品兼容 API 有 3 个？→ 输入介质不同（raw/已FFT/DCM），统一到同一方/圆图输出。

## 6. DoD 打卡
- [ ] demo 可演示 + `Week05/REVIEW.md` 完成（§2 底稿）
- [ ] 简历句已落笔（§3）
- [ ] W06 预习表已建（§4 作为笔记底稿）

## 明日预告
Week06：回拉数据上传与批处理。
