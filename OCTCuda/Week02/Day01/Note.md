# Week02 / Day01 — 学习记录（源码填充版）

> 主题：为什么 FFT 前要「重采样到均匀波数 + 加窗」。真实声明与行号已核对。

## 1. 今日目标（回顾）
理解 SD-OCT 光谱→k 域重采样与窗抑制旁瓣的物理与工程动机，建立 U16/U8/Vivo 输入差异模型。

## 2. 真实声明（VGPU_Process.cuh L225-230）

```cpp
// L227
bool VGPU_Data_Resampling_For_Scan(DOCMotionType status, U16* Original_data_scan, float* Hannwin_data, bool is_device_to_host);
// L228 Vivo：多一个增益/偏置标定
bool VGPU_Data_Resampling_For_Scan_Vivo(DOCMotionType status, double gain_multiplier, int offset_data, U8* Original_data_scan, float* Hannwin_data, bool is_device_to_host);
// L230 回拉（帧级入口，DLL 内按 frame_sum 循环）
bool VGPU_Data_Resampling_For_Pullback(DOCMotionType status, unsigned short frame_sum, float* h_Hannwin_data, bool is_device_to_host);
```

宿主调用（ImageProcessingController.cpp）：
- L511 实时（常规采集卡）：`Resampling_For_Scan(doc_motion_type, original_scan_data_buffer_for_one_frame, m_hanning_window_for_scan_data, false)`
- L506 / L720 Vivo（自研采集卡，`GetGlobalIsSelfInnovateCard()`）：`Resampling_For_Scan_Vivo(doc, GetGlobalGainMultiplier(), GetGlobalOffsetData(), vivo_buffer, window, false)`
- 窗口指针可传 `NULL`（如 ExportOCTdataView.cpp L983 导出重处理）→ DLL 使用内置默认窗（windata.h 表）。

## 3. 物理动机（为什么重采样 + 加窗）

- **SD-OCT 光谱在相机像素上近似按波长 λ 均匀**；而 FFT 要求信号在**波数 k = 2π/λ 均匀**的网格上才给出“无 chirp 的点扩散函数”。λ-k 非线性（光栅/色散）会造成深度轴畸变 + 旁瓣增宽 → 用标定表做 k 域重采样（k-linearization）。
- **加窗**：直接对有限长光谱做 FFT = 加矩形窗，谱泄漏到旁瓣；乘 Hann/Tukey 类窗压低旁瓣（主瓣略展宽可接受）。
- 结论链：`raw(k像素不均匀) → 查标定表→线性插值到均匀k → 乘窗 → FFT`（下一周接 `VGPU_Get_FFT_Power_*`）。

## 4. 输入差异表（U16 / U8 Vivo / Pullback）

| 维度 | `_For_Scan` | `_For_Scan_Vivo` | `_For_Pullback` |
| --- | --- | --- | --- |
| 输入类型 | `U16*` 常规采集 | `U8*` 自研卡(Vivo) | 内部帧缓冲（`frame_sum` 指定帧数） |
| 额外参数 | — | `gain_multiplier, offset_data` | `frame_sum`（U16） |
| 换算 | 直接查表插值 | `(U8 - offset)*gain` 后进浮点（再做插值乘窗） | 等价 Scan，但批量多帧走一次接口 |
| 宿主触发 | 常规卡实时/回拉补采（L511/725） | 自研卡实时/回拉（L506/720） | 预留整段批入口（当前宿主较少直调，整段流程走 L705-735 逐帧或 `Pullback_ProcessData_ToImage`） |

记忆点：**同一条成像链、两套采集硬件 → 同一接口族分叉**；Open 端用 `InputKind { U16, U8Vivo }` 一个入口消化三种输入。

## 5. Hann 可复现（练习：Python 生成并画图）

```python
import numpy as np, matplotlib.pyplot as plt
N = 2048                      # 冠脉每线点数
w = 0.5 - 0.5*np.cos(2*np.pi*np.arange(N)/(N-1))
plt.plot(w); plt.title("Hann N=%d  peak=%.3f" % (N, w.max())); plt.show()
```
对读：DLL 的 `windata.h::h_win_data[]` 是 2049 点 `double` 表（约 0.044→1.0→0.044，中部 ~1024–1038 达 1.000，对称、三位小数量化）。它像“带边缘裁剪的余弦锥削窗/类 Hann 量化表”；闭源公式未知，复现时用 `Hann 边缘 0.5(1-cos)` 拟合其形状即可（误差量级 1e-3 内可验收）。U16 vs U8 差异是位深+光电换算，与窗无关。

## 6. 自测 Q&A
1. 为什么不能对原始光谱直接 FFT？→ 波长网格→FFT 隐含均匀采样假设，k 域非均匀会使轴向分辨率退化、产生伪峰。
2. Hannwin_data 传 NULL 意味着什么？→ DLL 侧启用内置默认窗表；宿主侧可用 `nullptr` 测“默认窗路径”。
3. Vivo 的 gain/offset 做什么？→ 把采集卡 U8 的像素线性搬移到“真实光强”刻度（`(x-offset)*gain`），否则后续对数谱会失真。
4. `frame_sum` 为何是 API 参数而非宿主循环？→ 把多帧重采样放一个 kernel/批量循环里做，省去每帧 launch 开销与多次 H2D。
5. 我们的开源重采样要保证什么验收点？→ 等距 k 网格上的同一目标峰位、窗后旁瓣比、与 CPU golden 逐点误差。

## 7. DoD 打卡
- [ ] 能解释 FFT 前为何重采样+加窗（§3 口述）
- [ ] Hann 数组可复现（§5 跑通）

## 明日预告
实现 CPU 黄金版 resample+window。
