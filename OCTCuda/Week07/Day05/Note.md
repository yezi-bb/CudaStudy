# Week07 / Day05 — 学习记录（源码填充版）

> 主题：W07 REVIEW——校准 API 全景盘点、知识要点、合规边界；预告 W08 检测类 API。
> 周复盘文件已生成：`Week07/REVIEW.md`。

## 1. 本周目标回顾
Day01 主接口（GpuAutoCalibration/GpuConnectCalibration + 帧号 + cutHeight + 二次校验）→ Day02 旧算法族与 `_cs` 可测接口 + CheckImageInfo 分层 → Day03 CPU 简化“径向寻峰→鲁棒汇总→cut”实现 → Day04 失败模式 + auto_cut 回退。

## 2. 校准区 API 全景（真实声明，行号已核对，VGPU_Process.cuh）
| API | 位置 | 一句话职责 | 宿主落点 |
| --- | --- | --- | --- |
| `GPUCalibrationType` | L126-128 | GpuConnectCalibration=0 / GpuAutoCalibration | 主接口第一参数 |
| `VGPU_Catheter_AutoCalibration` | L286-287 | 新主接口：枚举+意图参数收敛 | ImageProcessingController L572/586/592 |
| `VGPU_AutoCalibration_new` | L279-280 | 旧·术中自动（device） | 已注释（L399-400） |
| `VGPU_AutoCalibration_connect(_cs)` | L281-283 | 旧·连接校准；`_cs` 吃 host transpose | L402-403 仍活跃 |
| `VGPU_AutoCalibration_new_cs` | L290-294 | 旧·自动校准 host 版 | 单测/离线 |
| `VGPU_CheckImageInfo` | L297 | 0=算法阈值问题 / 1=硬件问题 | OctRecordingView L3298-3315 |

## 3. 知识要点回顾（每天一条，能口述）
1. **校准的产出 = 给成像链的深度窗口**：Transpose 只取 `[cut_start,cut_end)`（L534），DSC 行数随之变化（L625）。
2. **cutHeight 是先验**：`round(导管直径/2/像素间距)+15`（L497）；校准围绕它精修，而非从零搜索。
3. **视野 >7mm 统一折算**（L562-565）：保证校准深度窗口跨视野可重复。
4. **参考帧**：自动校准固定取第 37 帧（L573）；连接校准逐帧递增（`m_check_frame_index`）。
5. **回拷仅在调试**：`is_device_to_host = m_is_save_flag`（L574）——又一次“只在需要处 D2H”。
6. **失败分层**：bool（本次成败）→ 保持状态重试；CheckImageInfo（0/1）→ 算法调参 vs 报硬件。
7. **接口演进规律**：阈值参数洪水 → “枚举 + 意图参数”，阈值内聚、宿主出错面变小。
8. **可测性设计**：`_cs` 后缀 = host float* 直入，无 GPU 依赖即 CI 可跑 → 开源练习抄这个姿势。

## 4. 合规边界清单（源自 00_全局规划 §7，L123-128）
- ✅ 可公开：方法骨架（逐列寻峰/鲁棒汇总/梯度过渡）、坐标系语义、管线顺序。
- ❌ 不外泄：产品级阈值（pos_up/down、threshold_data、blocksize、LineBrightness…）、内部 `IPAParmenter` 真值表、医院/回拉原始数据、DLL 逆向。
- 📁 公司仓绝对路径只写在本 OCTCuda 私有笔记；开源 README 用“等价功能模块名”。

## 5. W08 预告：检测类 API（真实声明，VGPU_Process.cuh）
| API | 位置 | 职责 |
| --- | --- | --- |
| `VGPU_Contrast_MediumCheck5` | L303 | 10 版造影剂（介质冲洗）识别 |
| `VGPU_Contrast_MediumCheck_Afd` | L305-306 | AFD 版 + isSmoke/bright/gap 阈值组 |
| `VGPU_CheckCatheterBreakDetection` | L310 | 导管折断检测（ground_noise/threshold/condition1/2） |
| `VGPU_guidingDetectOneFrame` | L313 | 回拉 guiding 检测（startRow/threshold/window/avgPixels） |
| `VGPU_CheckImageInfo` | L297 | 复用：区分算法/硬件问题 |
已见宿主端一处：ImageProcessingController L541-554——Scan 态每帧 `CheckCatheterBreakDetection(0, m_threshold, m_condition1, m_condition2, out_CheckImage, m_is_save_check_scan_image)`，失败置 `SetGlobalCurrentCatheterBreakStatues(true)`。

## 6. 自测 Q&A
1. 一帧校准失败，宿主下一帧会怎样？→ 仍在 ECalibrationState/EConnectCalibrationState，帧号递增再试并持续存失败现场图（L579-615）。
2. `_cs` 接口对“开源练习”最大启发？→ 输入输出全 host、无 DLL 依赖，可用合成数据做单元测试（Day02 §4 / Day03 §5）。
3. “方法公开、阈值私有”的边界一句话？→ 教“怎么找导管壁”，不教“产品参数是多少”。
4. 校准与 DSC 谁先谁后？→ 校准在 transpose 方图上（L572），DSC 在之后（L625）——因为 cut 决定 DSC 的行采样带。
5. 为什么 W08 检测都带 ground_noise / catheterCutHeight？→ 检测要排除导管区、以底噪为基线，和校准共享同一组物理先验。

## 7. DoD 打卡
- [x] 校准周知识/合规/API 复盘（本 Note + `Week07/REVIEW.md`）
- [x] 列出 W08 检测 API（§5）

## 明日预告
Week08：造影剂识别（Contrast_MediumCheck5/Afd）、导管折断（CheckCatheterBreakDetection）、guiding 检测（guidingDetectOneFrame）。
