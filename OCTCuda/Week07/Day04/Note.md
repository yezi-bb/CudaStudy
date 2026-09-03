# Week07 / Day04 — 学习记录（源码填充版）

> 主题：校准失败模式分析；e2e 增加 `auto_cut` 开关（手动/自动 cut 可切换）。

## 1. 今日目标（回顾）
把“校准可能失败”当一等公民建模：整理失败原因分类；在开源 e2e 管线里加 `auto_cut` 开关，自动 cut 失败时回退手动/默认深度窗口。

## 2. 宿主真实验收点（行号已核对）
- `ImageProcessingController.cpp L541-555`：Scan 态中若导管折断检测失败 → `SetGlobalCurrentCatheterBreakStatues(true)`（W08 正式展开）。
- `L559-616` 校准态块（`__try` 包住，异常走 `ExceptionFilter`）：
  - `image_hight = cut_end - cut_start`；视野 >7mm 统一按 `floor(7/2/pix)` 折算（L562-565）；
  - `VGPU_Catheter_AutoCalibration` 返回 bool；成功置状态 `EScanState`（L608），失败**保持校准态**并持续 `AddSaveCalibrationImageToQueue` 存图等待下一帧（L603-615）；
  - `m_check_frame_index++` 每帧递增（L579/600）。
- 失败归属判定在宿主 View 层：`OctRecordingView.cpp L3298-3315` 先 `CalibratingReferenceArmWithoutAlgorithm()`，再 `if (VGPU_CheckImageInfo()==1)` 判**导管异常（硬件）** 并走异常提示，否则进入算法校准——**宿主决策 = CheckImageInfo(0 算法/1 硬件) + bool(算法成败) 两层**。

## 3. 失败模式分类表（笔记交付）
| 类别 | 现象 | 判定线索 | 处置（参照宿主） |
| --- | --- | --- | --- |
| 硬件/导管异常 | 无参考臂信号、亮度过低 | CheckImageInfo==1 | 报“导管异常”，不重试（View 层） |
| 算法/阈值问题 | 有图但峰找不准 | CheckImageInfo==0 / bool==false | 换阈值参数、调 `ground_noise`、重试下一帧 |
| cutHeight 先验偏差 | 导管直径/像素间距错 → 搜索带不含导管壁 | frac<0.3 | 扩大 `search_w` 或重做导管参数 |
| 视野过大 | >7mm 直接按 7mm 折算，深度窗口变短 | 配置层 | 统一 7mm 校准（L562-565），不逐视野调 |
| 偏心/倾斜导管 | 单半径失效，各角度峰分散 | MAD 大 | 逐列峰 + 鲁棒中值/MAD 剔除后再拟合 |
| 遮挡伪影 | 半圈被气泡/残造影剂盖住 | frac 偏低 | 失败回退上一帧 cut / 手动 cut |

**学习点**：成功的 cut 是“可验证、可回退的决策”；宿主从不因一帧失败就崩，而是分层处置。

## 4. e2e `auto_cut` 开关设计（落点 OCTCudaProject）

```cpp
struct CutControl {
    bool auto_cut = true;   // 自动校准得到的 cut；false = 手动/默认
    int manual_start = 0, manual_end = 1024; // 手动或全深度兜底
};

struct FrameResult { bool calib_ok; int cut_start, cut_end; Mat circle; };

FrameResult process_frame(const Mat& fft_frame /* 深度×线 */,
                          const CutControl& ctrl, const CutResult& calib)
{
    int cs, ce;
    if (ctrl.auto_cut && calib.ok) {          // 自动 cut 生效
        cs = calib.cut_start; ce = calib.cut_end;
    } else {                                   // 失败 → 手动/默认（等价宿主停在默认窗口继续成像）
        cs = ctrl.manual_start; ce = ctrl.manual_end;
    }
    // …同 Day01 流程图：只对 [cs,ce) 做 Transpose→DSC→增强
    return {calib.ok && ctrl.auto_cut, cs, ce, /*circle*/Mat()};
}
```
宿主对应关系：
- `auto_cut=false` ≈ 宿主校准失败时 `m_image_processing_state` 保持并“用默认 cut 继续出预览图”，不阻塞实时链；
- `auto_cut=true` 且成功 ≈ L608 `ECalibrationState→EScanState` 后应用精修 `[cut_start,cut_end)`；
- 手动值来自 UI（`m_cut_start_point/m_cut_end_point` 用户可调），兜底保“可看”。

## 5. 失败模式实验（练习）
1. 用 Day03 合成图加“半圈遮挡”（θ∈[0,π/2]∪[π,3π/2] 无环）→ 应返回 `ok=false`；
2. 将 `auto_cut` 置 false → e2e 仍应产出可预览圆图（走 manual 全深度）；
3. 模拟 CheckImageInfo：写 `enum { kAlgo=0, kHardware=1 }`，宿主按返回值走两套提示——对照 OctRecordingView 的两分支。

## 6. 自测 Q&A
1. 为什么需要两套判定（CheckImageInfo + bool）？→ bool 说“本次没算出来”，CheckImageInfo 说“为什么”，前者驱动重试、后者驱动报修/换阈值。
2. 失败时为何宿主还继续存校准图？→ 需要采集失败现场给算法组调参（SaveCalibrationImage 队列，L613）。
3. auto_cut=false 是不是等于“产品不用自动校准”？→ 不是，开源是“开关可切”以演示两条路径；产品里用户也可手动调 cut。
4. 偏心导管怎么知道该用椭圆而非圆？→ 先 MAD 判断离群；若仍大，说明偏心，可用各角度峰拟合椭圆中心与长短轴（进阶）。
5. 异常 `__except` 捕获校准段干什么？→ GPU 调用+OpenCV 分配都可能抛结构化异常，保证不拖垮采集线程（`"CJ"` 异常过滤器 L618）。

## 7. DoD 打卡
- [ ] e2e 接入 auto_cut，可切自动/手动源
- [ ] 失败模式笔记（§3 表）归档

## 明日预告
W07 REVIEW：本周校准知识盘点 + 合规边界 + W08 检测 API 预告。
