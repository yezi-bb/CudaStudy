# Week10 / Day02 — 学习记录（源码填充版）

> 主题：att_paras 逐字段对照宿主——P60 / P80 / C7C8 三张配置表；新旧 API 差异。

## 1. 今日目标（回顾）
把 IPAProcessing（IPAAlgorithmController.cpp L46-244）里三套配置抄成表；看清“尺寸字段从 GetGlobal* 取、步长字段由 minwin 派生”。

## 2. 三张配置表（真实数值，源 IPAAlgorithmController.cpp L56-103）
| 字段 | P60（60mm, 非ZERO-1, L63-75） | P80（其余 vivo, L77-87） | C7C8 竞品（L91-103） |
| --- | --- | --- | --- |
| 脂质阈值 | 9.5 | 10.5 | 11 |
| z0 | 0 | 0.5 | 0.91 |
| zR | 3 | 2 | 0.99 |
| zC | 0 | 0 | 0 |
| zw | 10 | 7 | 5 |
| SNRmax | 0.25 | 0.25 | 0.25 |
| noise_level | 7 | 7 | 4 |
| scandepth | 5 | 5 | 4.8 |
| minwin | 41 | 46 | 41 |
| isVivoData | true | true | false |
> P60 的判定：`GetGlobalPullbackLength()==60 && MachineModel != "ZERO-1"`（L63）——机型与回拉长度的联合分支。

## 3. 尺寸字段与派生（真实，L175-180）
```cpp
number_frames  = GetGlobalTotalFrameNumber();    // 总帧数
number_depths  = GetGlobalRawToFFTDataCols();    // 每线深度点数 1025
number_theta   = GetGlobalRawToFFTDataRows();    // 每帧线数(行) 500
number_alines  = number_frames * number_theta;   // 全卷 A-line 总数
step_success   = ceil(stepsucc * minwin);        // 0.5×minwin 取整
step_fail      = ceil(stepfail * minwin);        // 0.2×minwin 取整
```
关键 insight：**step 不是独立调参，而是 “minwin 的比例取整”**——缩小调参面，物理上保证“每次窗移动不小于最小窗的一定比例”。

## 4. 新旧 API 差异
| 维度 | 旧（IpaAlgorithmKernel.cuh，镜像未含/08Code） | 新（VGPU_Process.cuh） |
| --- | --- | --- |
| 配置 | `GUP_SetIpaalgorithmConfig(att_paras, h_isOption)` 先 SetConfig（含释放重配） | Calculate 直接传 `h_paras`（配置随调用走） |
| 计算 | `GPU_Calculate_Ipa_Result(...)` 多 out | 合并进 `VGPU_Calculate_Ipa_Result`（宿主一次调用完成 配置+算+输出，见 01 §7） |
| 数据入口 | float raw | **U16 FFT 卷**（宿主 GetGlobalFFTData()，L239/242） |
**进化规律复现**（W07/09 同款）：把“状态（配置）”从 API 分两步改成一个“完整描述对象”直接传入 → 宿主无全局状态、可重入（多线程/重复调安全）。

## 5. 一处“运行时可覆盖”的设计（真实，L106-173）
`#if READ_IPA_PARAMETER_TXT`：可从 `IPAParmenter.txt`（每行 `key=value`）覆盖上面所有字段——**发布态默认编译期内置，调试/标定时文件覆盖**。这是工程上“参数可调”的惯用手法。

## 6. DoD 打卡
- [x] 三配置表（§2）+ 尺寸/派生公式（§3）
- [x] 新旧差异写明（§4）；`notes/W10_att_paras.md` 已归档

## 明日预告
VGPU_Calculate_Ipa_Result 全部实参来源与尺寸精读（链 D 详细版）。
