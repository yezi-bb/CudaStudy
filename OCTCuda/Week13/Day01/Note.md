# Week13 / Day01 — 学习记录（源码填充版）

> 主题：解剖宿主 GPU 线程模型（GpuHandlingDataThreadController）——单常驻线程 + 标志 + 临界区。

## 1. 今日目标（回顾）
用真源码行号画清“谁创建线程、循环做什么、怎么停、怎么护数据、异常去哪”，为 W13D2 的分层重构打底。

## 2. 线程生命周期（真实，GpuHandlingDataThreadController.cpp）
### 线程入口（L396-423）
```cpp
DWORD WINAPI GpuHandlingDataThread(LPVOID pParam) {
    __try {
        GpuHandlingDataThreadController* c = (GpuHandlingDataThreadController*)pParam;
        while (c->GetIsHandDataThreadActive()) {        // ① 常驻轮询标志
            __try { c->HandleAquiredimageData(); }      // ② 每轮处理一帧任务
            __except (EXCEPTION_EXECUTE_HANDLER) { /*日志*/ }  // ③ 任务级保护
        }
        return 0;
    }
    __except (GetGlobalPreExceptionController()->ExceptionFilter(GetExceptionInformation(), "CJ")) {
        GetGlobalPreExceptionController()->ProcessException();  // ④ 线程级异常收口
    }
}
```
### 启动/停止（L445-491）
```cpp
void StartGpuHandlingDataThread() {
    VGPU_Check_pullback_Data_memory();              // 先查显存（横切，02 §L123）
    if (m_hand_for_scan_thread == NULL) {
        m_is_hand_data_thread_active = true;        // 置位后再创建
        m_hand_for_scan_thread = CreateThread(NULL, 0, GpuHandlingDataThread, this, 0, NULL);
    }
}
void ReleaseGpuHandlingDataThread() {
    is_need_gpu_processing = false;                 // 先清任务标志
    if (m_hand_for_scan_thread != NULL) {
        m_is_hand_data_thread_active = false;       // 再退循环
        Sleep(10);                                  // 给线程优雅退出的时间窗
        CloseHandle(m_hand_for_scan_thread); m_hand_for_scan_thread = NULL;
    }
    /* 重置记录缓冲/清 L 图（数据面复位）*/
}
```
### 分发（HandleAquiredimageData 内，按状态机分支）
| 状态 | 行附近 | 动作 |
| --- | --- | --- |
| 收到采集新帧（标志 is_need_gpu_processing） | ~L150-155 | 取当前状态/数据 |
| EScanState（扫描预览） | ~L169-171 | `ImageProcessingController::HandleDataOfScanning(...)`（实时单帧链，W05/07） |
| 记录/回拉（ERecord…等） | ~L202-235 / L278 | `HandleDataOfRecording(...)`（回拉逐帧链，W06/08） |
| 结果共享 | ~L244-270 | 临界区 `m_gpu_thread_Lock` 保护写 `SetGlobal*` 结果（供显示线程读） |

## 3. 设计模式提炼（抄作业）
1. **常驻线程 + 轮询**：不每帧 CreateThread（Win32 线程创建贵、不可控）；用 `m_is_hand_data_thread_active` 控制生命周期。
2. **任务标志 → 工作**：采集线程只“置 is_need_gpu_processing + 拷数据”，GPU 线程被唤醒处理——解耦生产者/消费者节奏。
3. **两级 __except**：任务级（一帧坏不影响下一帧）+ 线程级（“CJ”过滤器集中处理+记录），任何异常不回传采集侧。
4. **优雅停止三序**：清任务 → 退循环 → 关闭句柄（置位→Sleep→Close 的顺序反了会杀线程导致丢数据）。
5. **临界区只护共享结果**：算法内的大缓冲由各 Controller 自持，跨线程共享点集中。

## 4. 对照“为什么 02 强调状态机”
线程按 `m_image_processing_state`（EScanState/ERecord…）分发，状态的合法迁移 = 状态机（02 L134-140，W13D4 实现）；线程只是“状态机的执行者”，状态本身在 Controller 层管理。

## 5. 自测
1. 手画：采集线程 / Gpu 线程 / 显示线程三方 + 标志与临界区 + “CJ”收口；
2. 问自己：为什么启动先 Check_pullback_Data_memory、停止先清 is_need_gpu_processing？（→ 显存横切 + 无新任务再退）

## 6. DoD 打卡
- [x] 宿主线程图（§3/§4）能对着讲 5 分钟
