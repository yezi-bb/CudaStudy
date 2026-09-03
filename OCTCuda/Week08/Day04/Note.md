# Week08 / Day04 — 学习记录（源码填充版）

> 主题：三个检测 hooks 总览 + 开源版 `pre_dsc_checks()` 设计；总图沉淀到 `notes/W08_detect_hooks.md`。

## 1. 今日目标（回顾）
把 W08D1（造影剂）、D2（折断）、D3（guiding）统一成一张“检测站”图：触发状态、输入图、输出去向、是否回拷；再在开源管线中加 `pre_dsc_checks()` 检测点桩。

## 2. 检测站总览（真实宿主行号）
| 检测 | 所在宿主函数 | 状态门 | 输入 | 关键实参 | 成功动作 |
| --- | --- | --- | --- | --- | --- |
| 造影剂 5/Afd | HandleDataOfRecording L755-786 / L787-820 | EVerifyPurgeState / ESmokeTestCheckState + Automatic | Transpose_CheckImage 全 FFT 深度（L762/794） | `(0, cutH, 帧号[, isSmoke, bright, gap1..3])` | `m_is_verifypurge_success=true` |
| 折断 Break | HandleDataOfScanning L541-555 | EScanState + 功能开 + 未置位 | GPU 内部取 transpose | `(0, 0.3, 0.0019, 90, 检查图, save?)` | `SetGlobalCurrentCatheterBreakStatues(true)` |
| Guiding | HandleDataOfRecording L821-836 | EPullbackRecordState + AFD + need | GPU 内部取 transpose | `(startRow=10, thr, window, m_avgPixels, totalFrame)` | `success=true; need=false; clear()` |

**共同点（抄作业要点）**：
1. 全部 **读“Log 求和后、DSC 前”的方图**（个别用全深度窗口）；
2. 全部 **同步嵌入帧链**，不另起线程、不阻塞出图（异常仅 return 本帧）；
3. 全部 **bool 返回 + 宿主全局状态置位**，GPU 只吐“结论/少量数据”；
4. 只在需要排查时 **D2H 回拷**（`m_is_save_check_scan_image` / `is_device_to_host=false`）。

## 3. 开源 `pre_dsc_checks()`（落点 OCTCudaProject）
在 W07 e2e 的 `process_frame` 基础上，把检测统一成 DSC 前的检测站：

```cpp
enum class CheckKind { None, PurgeMedium, SmokeMedium, CatheterBreak, Guiding };

struct CheckReport { CheckKind kind; bool ok; std::string why; };

class PreDscChecks {
public:
    // 检测点桩：每种检测只暴露 run(frame, ctx) → 报告
    // 由状态机驱动调用哪个 kind（对照宿主 m_image_processing_state）
    CheckReport run(CheckKind kind, const cv::Mat& transpose_full, const CheckCtx& ctx)
    {
        switch (kind) {
        case CheckKind::PurgeMedium:  return cpu_medium_check(...);   // W08D1
        case CheckKind::SmokeMedium:  return cpu_medium_check(...isSmoke...);
        case CheckKind::CatheterBreak:return cpu_break_check(...);    // W08D2
        case CheckKind::Guiding:      return cpu_guiding_detect(...); // W08D3
        default: return {kind, true, "skipped"};
        }
    }
};
```
改进点（相对宿主）：
- 检测点从“散落 if”提为**可插拔接口**：新增检测不污染主链；
- 报告带 `why`：失败原因字符串化，复现/调参友好；
- 按需回拷集中管理：默认 `device_side=true` 不拷，只有 save 开关打开才取检查图。

## 4. 状态机与检测关系（口述图）
```
[EVerifyPurgeState] ──Purge ok──> [ESmokeTestCheckState] ──Smoke ok──> [EPullbackRecordState]
        │ 造影剂5/Afd(false)              │ 造影剂5/Afd(true)                │ guiding(到达) → 正式记录
[EScanState] ──每帧 Break 门控(只报一次)──> 折断 → 全局置位 → 停止回拉/提示
```
全部发生在 **DSC 前**：同一张方图既服务检测又服务成像，GPU 资源复用最小化。

## 5. 自测
1. 用一周以来全部合成帧跑通 4 类 kind；
2. 对每个检测写出“一句话判定 + 会置哪个全局位”；
3. 设计一个场景：“Guiding 失败但导管已到位”应如何人工接管（UI 开关 bypass need flag，参照宿主 m_is_need_guidingDetect=false 的复位途径）。

## 6. DoD 打卡
- [ ] pre_dsc_checks 接口 + 4 kind 跑通
- [ ] `notes/W08_detect_hooks.md` 已归档（检测站总览，可复述）

## 明日预告
W08 REVIEW：三检测对比复盘 + 合规边界 + W09（连续校准/拼接）API 预告。
