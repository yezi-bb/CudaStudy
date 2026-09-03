# Week13 / Day02 — 学习记录（源码填充版）

> 主题：职责分层重构——宿主“线程调度 / 算法执行 / 状态决策”三件事分家；开源拆 `PipelineEngine`(host) + `GpuWorker`(gpu)。

## 1. 今日目标（回顾）
在宿主两个 Controller 的调用关系上提炼“三职责”，把 OCTCudaProject 的线程与算法解耦为两接口。

## 2. 宿主三职责（真实对照）
| 职责 | 宿主承担者 | 做的事 |
| --- | --- | --- |
| ① 调度（线程/标志/锁） | GpuHandlingDataThreadController | CreateThread、m_is_hand_data_thread_active、is_need_gpu_processing、临界区 |
| ② 算法执行 | ImageProcessingController（HandleDataOfScanning/Recording 内） | VGPU_Resampling/FFT/…、检测、校准（W01-09 全链） |
| ③ 状态决策 | m_image_processing_state + View 层 | 该处理哪一帧、要不要校准/检测/出图（状态机） |
> 主机边界：Gpu 线程把 Controller 当“每轮执行器”调；Controller 不反向感知线程，只按状态做事。

## 3. 开源重构（落点 OCTCudaProject，模块 oct::E2E）
```cpp
namespace oct {

// ②算法执行：无状态管线（输入一帧 → 输出帧产物），与线程/状态无关 → 可单测
class PipelineEngine {
public:
    struct FrameInput  { const void* raw; Shape fft_shape; const CutCalib* cut; };
    struct FrameOutput { cv::Mat rect, circle; const DetectReport* det; };
    bool process_frame(const FrameInput&, FrameOutput&);   // 链 = 02 链 A 的公开等价
    bool process_pullback_bulk(const PullbackBuf&, PullbackOut&); // 批(等价 W06)
};

// ①调度：一个常驻线程持有 engine，按任务队列/标志消费
class GpuWorker {                      // 对照 GpuHandlingDataThreadController
public:
    void start();                      // 置 active → 起线程（不每帧 new thread）
    void stop();                       // 清任务标志 → active=false → join（优雅停止三序）
    void enqueue_frame(const void* raw);
private:
    void run_loop();                   // while(active) { take(); engine_.process_frame(...); }
    std::atomic<bool> active_{false};
    PipelineEngine engine_;            // 组合而非继承
};

// ③状态决策（W13D4 状态机）驱动 GpuWorker 的输入来源
} // namespace oct
```
**重构判据**：PipelineEngine 可脱离 GpuWorker 用合成数据单测（跑通 W11 掩膜用例）；GpuWorker 只在“调度”上留测试（启停/队列空转不调算法）。→ 对齐宿主：算法 Controller 本就可被别的入口调（校准/离线回放也用同一批 VGPU_*）。

## 4. 与宿主行号对照表（自检）
| 开源 | 宿主 | 引用行 |
| --- | --- | --- |
| GpuWorker::start/stop | Start/ReleaseGpuHandlingDataThread | L445-491 |
| run_loop | GpuHandlingDataThread | L396-423 |
| PipelineEngine::process_frame | HandleDataOfScanning | ImageProcessingController ~L485 |
| PipelineEngine::process_pullback_bulk | HandleDataOfRecording | ~L674 |
| 状态机决定调用哪个 | HandleAquiredimageData 分发 | ~L150-280 |

## 5. 自测（动手）
1. 把现有 oct::Context 版单帧 demo（OCTCudaCmake/如何新建CMake工程.md 样例）包成 PipelineEngine::process_frame；
2. GpuWorker 单线程跑 1000 帧合成帧，验证“排队→消费→无泄漏”，停后 join 不卡死。

## 6. DoD 打卡
- [ ] PipelineEngine 单测通过（算法面无线程也能跑）
- [ ] GpuWorker 启停/队列测试通过

## 明日预告
CUDA Streams 与双缓冲：为什么“线程归线程、流归流”，开源多流并行 + 事件同步。
