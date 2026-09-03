# Week07 / Day02 — 学习记录（源码填充版）

> 主题：旧校准算法族（new / connect / *_cs）与 CheckImageInfo。

## 1. 今日目标（回顾）
对照新主接口与旧算法；理解 `_cs` 测试接口为何直接吃 Host transpose；CheckImageInfo 区分“算法失败/硬件失败”。

## 2. 真实声明（VGPU_Process.cuh L279-297）

```cpp
// 旧·新参考臂自动校准（device 版，输入取 device 转置图）
bool VGPU_AutoCalibration_new(int TransPose_height, int Transpose_width,
    int pos_up_threshold, int pos_down_threshold, int threshold_data, int blocksize,
    double LineBrightness, double PackDifference, double hdelt, double hbrightness, double NextValue,
    int &h_delt_y);
bool VGPU_AutoCalibration_connect(GPUCalibrationType calibrate_type, float ground_noise, int indexFrams,
    int TransPose_height, int Transpose_width, int pos_up_threshold, int pos_down_threshold,
    int threshold_data, int blocksize, double LineBrightness, double PackDifference,
    double hdelt, double hbrightness, double NextValue);
// *_cs：直接吃 Host transpose（float*），便于离线/单测
bool VGPU_AutoCalibration_new_cs(float* inTranspose_data_for_scan, int TransPose_height, int Transpose_width,
    int pos_up_threshold, int pos_down_threshold, int threshold_data, int blocksize,
    double LineBrightness, double PackDifference, double hdelt, double hbrightness, double NextValue,
    int &h_delt_y);
bool VGPU_AutoCalibration_connect_cs(int indexFrams, float* inTranspose_data_for_scan, /*…同阈值组…*/);
// L297: 返回 0 = 算法阈值问题, 1 = 硬件问题
int VGPU_CheckImageInfo();
```
宿主（行号已核对）：
- ImageProcessingController.cpp L402-403：连接校准旧算法仍走 `VGPU_AutoCalibration_connect_cs(m_check_frame_index, input_data, 642, 1000, m_position_up_threshold_forconnext, m_position_down_threshold_forconnext, m_threshold_data_forconnext, m_band_size_forconnext, m_LineBrightness_forconnext, m_PackDifference_forconnext, m_delt_forconnext, m_brightness_forconnext, m_nextvalue_forconnext)`；`new_cs` 被注释（L399-400）——两代阈值参数组并存。
- OctRecordingView.cpp L3298-3315：`CalibratingReferenceArmWithoutAlgorithm()` 后 `if (VGPU_CheckImageInfo()==1)` → 判为**导管异常**（硬件），走异常/提示流程；否则按是否首次自检继续。

## 3. 新旧对照表（DoD 交付）

| | `AutoCalibration_new/_connect(+_cs)` | `Catheter_AutoCalibration`（新主接口） |
| --- | --- | --- |
| 形态 | 一大串搜索阈值参数（pos_up/down、threshold、blocksize、LineBrightness…） | 收敛为枚举+意图参数（type/光源/新旧导管/帧号/cutHeight/二次校验） |
| 输入 | device 版内部取转置图；`_cs` 版 host 直接给 float* | 内部取转置图（同 device 版思路） |
| 输出 | `h_delt_y`/隐式状态 | 成功 bool + 内部校准量 → cut |
| 用法 | 老流程/连接校准（L402 仍活） | 术中自动/连接校准（L572-594 默认） |
| 测试 | `_cs` 天生可离线单测 | 靠宿主调试存图 |

设计体会：**接口从“阈值参数洪水”收敛为“意图+可离线测试”**——`_cs` 测试接口是给算法组离线程的“后门”，能吃到 Host 转置图直接验证算法逻辑。

## 4. 开源 `calib_from_transpose`（设计，Day02 交付）

```cpp
struct CalibParams { bool is_new_catheter; double cut_height_px; int ref_frame; };
struct CalibResult { bool ok; int cut_start, cut_end; double catheter_r; };
CalibResult calib_from_transpose(const std::vector<float>& transpose, int h, int w, const CalibParams&);
// 输入 = 一帧 host transpose(深度×线)；方法 = 公开版“径向寻峰估导管壁”（Day03 详）
```
- `_cs` 风格的“吃 host transpose”让单测只需合成矩阵，不依赖 GPU/DLL → 这正是开源项目最友好的起点。

## 5. CheckImageInfo 语义（笔记）
- 返回 `0`：算法阈值问题（如亮度过低/峰不足）→ 通常“换阈值重试/调参”即可；
- 返回 `1`：硬件问题（如导管未接/参考臂异常）→ 宿主直接报“导管异常”而非重试（OctRecordingView L3301-3310）。
- 学习点：**把“算法失败”和“硬件失败”分开**能让宿主采取不同动作，是好 API 设计的范例。

## 6. 自测 Q&A
1. `_cs` 后缀为什么利于测试？→ 无 device 依赖，输入输出纯 host，CI/离线单测可跑（算法要“可测性”）。
2. 为什么 connect 需要 indexFrams 递增？→ 连接校准连续取多帧逼近导管状态，每帧结果喂给下一帧搜索。
3. 一堆阈值参数为什么被收敛？→ 新主接口把它们打包成“枚举+预设”，降低宿主出错面；阈值仍内部存在但不再暴露。
4. h_delt_y 是什么量？→ 导管壁/参考臂偏移估计（y=深度方向位移），旧算法用它继续搜索；新算法内部化。
5. 两次 Check 组合（Connect + CheckImageInfo）顺序？→ 先停算(CalibratingReferenceArmWithoutAlgorithm)→CheckImageInfo 判硬件→再 AutoCalibration_connect_cs（L3298-3304 顺序）。

## 7. DoD 打卡
- [ ] 新旧对照表完成（§3）
- [ ] calib_from_transpose 接口设计好（§4）

## 明日预告
CPU 简化寻峰校准（合成环）。
