# Week05 / Day01 — 学习记录（源码填充版）

> 主题：灰度增强四模式与宿主默认参数对照（display windowing / gamma）。

## 1. 今日目标（回顾）
精读 `VGPU_Image_Enhancement` 与 `GrayEnhanceType`，做参数命名对照表并 CPU 复现四种增强。

## 2. 真实声明与枚举（VGPU_Process.cuh）

```cpp
// L270-271
extern "C" __declspec(dllexport) bool VGPU_Image_Enhancement(int dsc_rows, int dsc_cols, int frame_no,
    unsigned char* h_Enhance_data, float low_bound, float up_bound, float pow_index,
    GrayEnhanceType enhance_type, int is_device_to_host);   // 注意：is_device_to_host 是 int！
// L84-91
typedef enum { LinearEnhanceType = 1, PowEnhanceType, LogEnhanceType, ExpEnhanceType } GrayEnhanceType;
```

宿主实时分支（ImageProcessingController.cpp，行号已核对）：
```cpp
if (GetGlobalImageEnhancementType() == 0) {            // L634 默认线性
    VGPU_Image_Enhancement(g_circle_image_height_, g_circle_image_width_, 0,
        this->m_enhance_data, this->m_low_boundary, this->m_up_boundary,
        GetGlobalDefaultGammaValue(), LinearEnhanceType, false);
} else {                                               // L640 幂增强
    ... PowEnhanceType ...(同参)...
}
// L651/L874/L951 增强后立即 Gray2Color(true) 回拷显示
```

## 3. 输入/输出与窗
- 输入：DSC 后的 `float` 圆图（设备侧，`frame_no=0` 为当前实时帧）；
- 输出：`unsigned char* h_Enhance_data`（704×704 灰度，内存按行主序）；
- `low_bound/up_bound` = 显示窗（对应 m_low_boundary / m_up_boundary，回拉重放时由 `VGPU_CalculatedContrastRange` 自适应计算）；
- `pow_index` = gamma（实时用 `GetGlobalDefaultGammaValue()`，录制重放用 `GetGlobalCurrentRecordGammaValue()`）。

## 4. 四种增强公式（CPU 复现参考）
设 `t = clamp((v - low)/(up - low), 0, 1)`：
| 模式 | 公式（到 0-255） | 说明 |
| --- | --- | --- |
| Linear | `g = 255·t` | 线性窗（默认 L634） |
| Pow | `g = 255·pow(t, 1/pow_index)` | gamma 校正（默认幂分支 L640 用 pow_index=gamma） |
| Log | `g = 255·log(1+ k·t)/log(1+k)` | 提升暗部 |
| Exp | `g = 255·(exp(k·t)-1)/(exp(k)-1)` | 压缩暗部提亮亮部 |

## 5. 参数命名对照表（DoD 交付）
| 宿主/全局命名 | 函数参数 | 作用 |
| --- | --- | --- |
| `m_low_boundary` | `low_bound` | 窗下限 |
| `m_up_boundary` | `up_bound` | 窗上限 |
| `GetGlobalDefaultGammaValue()` | `pow_index` | 实时 gamma |
| `GetGlobalCurrentRecordGammaValue()` | `pow_index` | 重放 gamma |
| `GetGlobalImageEnhancementType()==0/else` | `enhance_type` | 线性/幂 |
| `g_circle_image_height_/width_` | `dsc_rows/cols` | 704 |
| 回放帧序号 | `frame_no` | 0=当前 |

## 6. 自测 Q&A
1. is_device_to_host 为什么是 int？→ 接口历史遗留（0/1 同 bool 语义），注意不要写 `!=false` 等脆弱判断，按 `!=0` 处理。
2. low/up 从哪来？→ 实时为宿主窗参数（m_low_boundary/m_up_boundary），回拉后处理为 `CalculatedContrastRange` 自动算出的对比度窗。
3. Linear vs Pow 什么时候切换？→ `GetGlobalImageEnhancementType()`：0 线性、非 0 幂；手术中可切，即“增强曲线”开关。
4. 为什么先增强（灰度）再伪彩？→ 增强决定亮度层次，伪彩只负责“灰度→RGB 调色板”，解耦便于替换不同 map。
5. frame_no=0 语义？→ 单帧实时（每帧调用前不传具体序号）；帧序号用于回放/批处理取对帧。

## 7. DoD 打卡
- [ ] CPU 四种增强可切换输出（§4）
- [ ] 参数对照表完成（§5）

## 明日预告
Gray2Color 伪彩与合规。
