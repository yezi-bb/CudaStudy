# W10 — att_paras 三配置表（私有学习笔记）

> 全部数值来自宿主 IPAAlgorithmController.cpp IPAProcessing（L46-244），行号已核对。

## 表 1：P60 / P80 / C7C8
| 字段 | P60 | P80 | C7C8 |
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
- 公共预设：stepsucc=0.5，stepfail=0.2（L56-57）
- 判定：P60 = 回拉长度60 && 机型≠ZERO-1；P80 = 其它 vivo；C7C8 = EC7orC8OCTDataType

## 表 2：尺寸派生（L175-180）
| 字段 | 来源 | 值(示例) |
| --- | --- | --- |
| number_frames | GetGlobalTotalFrameNumber() | 卷总帧 |
| number_depths | GetGlobalRawToFFTDataCols() | 1025 |
| number_theta | GetGlobalRawToFFTDataRows() | 500 |
| number_alines | frames×theta | 550×500 |
| step_success | ceil(0.5×minwin) | — |
| step_fail | ceil(0.2×minwin) | — |

## 表 3：新旧 API
- 旧：GUP_SetIpaalgorithmConfig(att_paras, flag) + GPU_Calculate_Ipa_Result（float raw）
- 新：VGPU_Calculate_Ipa_Result（att_paras 随调用传入，U16 FFT 卷，01 §7）
