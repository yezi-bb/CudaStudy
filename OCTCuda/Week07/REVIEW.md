# Week07 REVIEW — 导管校准

> 依据：`00_全局规划.md` §3（周主题）/ §7（合规）；源码锚点均为本地镜像 `E:\CUDA\source` 已核对行号。

## 1. 本周关键词
- 校准类型：`GpuConnectCalibration`（连接/参考臂） vs `GpuAutoCalibration`（术中自动）——`VGPU_Process.cuh L126-128`
- 主接口：`VGPU_Catheter_AutoCalibration`（L286-287）——枚举+意图参数收敛
- 旧算法族：`AutoCalibration_new / _connect (+_cs)`（L279-283/290-294）
- 失败归属：`VGPU_CheckImageInfo`（L297）：0=算法阈值问题，1=硬件问题

## 2. 核心心智模型
```
导管/马达/光源 配置
   │ catheterCutHeight = round(D/2/像素间距)+15        (ImageProcessingController L497)
   ▼
校准态帧（自动=第37帧 / 连接=递增帧）→ 深度窗口(>7mm按7mm折算,L562-565)
   ▼ VGPU_Catheter_AutoCalibration  (L572/586/592)
成功 → ECalibrationState→EScanState(L608)，[cut_start,cut_end) 生效 → Transpose(L534)→DSC(L625)
失败 → 保持校准态、帧号+1、存失败现场图重试(L603-615)；View 层按 CheckImageInfo 判 调参/报硬件
```
产出不是一张“校准图”，而是**给成像链的深度窗口**。

## 3. 掌握清单（口述自检）
- [ ] 自动 vs 连接校准差异；为何固定 37 帧 vs 递增帧
- [ ] cutHeight/7mm 折算/二次校验各自解决什么问题
- [ ] `_cs` 接口为什么可测（host float*、无 device 依赖）
- [ ] CheckImageInfo 两层语义如何驱动宿主不同动作
- [ ] CPU 简化实现：逐列径向寻峰 + 投票/鲁棒汇总 + frac 阈值判定
- [ ] auto_cut 开关与失败回退（手动/默认窗口不阻塞实时链）

## 4. 开源练习交付
- `cpu_catheter_peak`：transpose 方图 → 导管壁深度行 + cut 窗口（Day03）
- 合成圆环自测：误差 <3px；半圈遮挡应正确失败（Day03 §5 / Day04 §5）
- `CutControl{auto_cut, manual_start/end}` + `process_frame` 回退逻辑（Day04 §4）

## 5. 合规边界（00 §7）
- 公开：方法骨架、坐标系语义、管线顺序；
- 私有：产品阈值（pos_up/down、threshold_data、blocksize、LineBrightness…）、真值表、患者/回拉数据、DLL 逆向；
- 路径规则：公司仓绝对路径仅限本 OCTCuda 私有仓；开源用等价功能名。

## 6. 下周预告（W08 检测类 API，VGPU_Process.cuh）
| API | 位置 | 一句话 |
| --- | --- | --- |
| `VGPU_Contrast_MediumCheck5` | L303 | 造影剂（介质冲洗）识别 v10 |
| `VGPU_Contrast_MediumCheck_Afd` | L305-306 | AFD 版（isSmoke + 亮度/间隙阈值组） |
| `VGPU_CheckCatheterBreakDetection` | L310 | 导管折断检测（宿主 L541-554 已见） |
| `VGPU_guidingDetectOneFrame` | L313 | 回拉 guiding 检测 |
