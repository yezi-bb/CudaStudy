# W08 检测 Hooks 总览（私有学习笔记）

> 依据宿主源码行号均已核对（`E:\CUDA\source` 镜像）。
> 合规：方法公开、产品阈值黑盒（00_全局规划 §7）。

## 1. 三类检测 × 触发状态 × 宿主落点
| 检测 | API（VGPU_Process.cuh） | 宿主状态门 | 宿主函数:行 | 输入图 | 关键参数 | 置位结果 |
| --- | --- | --- | --- | --- | --- | --- |
| 造影剂（介质） | Contrast_MediumCheck5 L303 / Afd L305-306 | EVerifyPurgeState（普通）/ ESmokeTestCheckState（烟雾），均需 TriggerType=="Automatic" | HandleDataOfRecording L755-786 / L787-820 | Transpose_CheckImage 全 FFT 深度 L762/794 | `(0, cutH, 帧号, isSmoke, bright, gap1..3)` | m_is_verifypurge_success=true，帧号++ |
| 导管折断 | CheckCatheterBreakDetection L310 | EScanState + 功能开 + 未置位（上升沿） | HandleDataOfScanning L541-555 | GPU 内部 transpose；out_CheckImage 可选 | `(0, 0.3, 0.0019, 90, 图, save)` | SetGlobalCurrentCatheterBreakStatues(true) |
| Guiding | guidingDetectOneFrame L313 | EPullbackRecordState + AFD + need | HandleDataOfRecording L821-836 | GPU 内部 transpose | `(startRow=10, thr, window, m_avgPixels, totalFrame)` | success=true；need=false；容器 clear+swap |

## 2. 共性设计（抄作业清单）
1. 输入统一 = “Log 求和后、DSC 前”方图（检测窗口可全深度，成像用 cut 带）
2. 同步嵌入帧链；结构化异常仅 return 本帧，不崩线程
3. bool 返回 + 宿主全局状态置位；GPU 不外传大块数据
4. 回拷按需：is_device_to_host / m_is_save_check_scan_image / out_CheckImage 均默认 false
5. 阈值默认值宿主头文件可见（ImageProcessingController.h L131-135）：m_threshold=0.3, m_condition1=0.0019, m_condition2=90

## 3. 状态机衔接
```
EVerifyPurgeState ─ok→ ESmokeTestCheckState ─ok→ EPullbackRecordState ─guiding ok→ 正式记录
EScanState ─(break 命中, 只报一次)→ 全局折断位 → 停止/提示
```

## 4. 开源检测点（等价模块名，不含产品数值）
- cpu_medium_check(mat, H, W, cutH)  → {ok, bright_mean, gap_stat}
- cpu_break_check(mat, H, W, t_e, t_r, t_bad) → {ok, energy, wall_frac, bad_lines}
- cpu_guiding_detect(state, thr, total) → 序列到达判定
- pre_dsc_checks.run(kind, transpose_full, ctx) → CheckReport{kind, ok, why}
