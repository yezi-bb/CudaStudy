# Week13 / Day04 — 学习记录（源码填充版）

> 主题：实现开源最小状态机（02 数据流 L134-140）——非法 API 顺序抛异常。

## 1. 今日目标（回顾）
把“Idle → Allocated → StreamingFrame → (可选)PullbackBulk → AnalysisLoaded → IpaComputed → Freed”做成带守卫的类，任何非法迁移抛异常（模仿宿主“状态机驱动、错误即保护”的纪律）。

## 2. 规格（源自 02 L134-140）
```text
Idle → Allocated → StreamingFrame → (optional) PullbackBulk → AnalysisLoaded → IpaComputed → Freed
每状态只允许上述文档列出的 API 子集；错误顺序抛异常。
```
**为什么要有状态机**（宿主观察）：
- 同一批 VGPU_* 在错误时机被调会因缓冲未配/尺寸不符而崩（如没 Allocate 就 Stream）；
- 线程循环每轮都要知道“现在能做什么”——状态就是“允许的 API 集合”的浓缩。

## 3. 实现（落点 OCTCudaProject/oct/E2E/PipelineState.h）
```cpp
namespace oct {
enum class St { Idle, Allocated, StreamingFrame, PullbackBulk,
                AnalysisLoaded, IpaComputed, Freed };

class PipelineState {
public:
    St state() const { return st_; }
    void ensure(St allowed, const char* api) {
        if (st_ != allowed)
            throw std::logic_error(std::string("illegal API ") + api +
                " in state " + to_string(st_));        // 非法顺序即抛
    }
    // —— 每步先 ensure，再迁移 ——
    void allocate()      { ensure(St::Idle, "allocate");         st_ = St::Allocated; }
    void reallocate()    { ensure(St::Allocated, "reallocate"); /*留在 Allocated*/ }
    void stream_frame()  { ensure(St::Allocated, "stream_frame"); st_ = St::StreamingFrame; }
    void end_streaming() { ensure(St::StreamingFrame, "end_streaming"); /*可回 Allocated 继续拉取*/ }
    void start_bulk()    { ensure(St::StreamingFrame, "start_bulk"); st_ = St::PullbackBulk; }
    void end_bulk()      { ensure(St::PullbackBulk, "end_bulk");    /*可继续 AnalysisLoaded*/ }
    void load_analysis() {
        if (st_ != St::StreamingFrame && st_ != St::PullbackBulk)
            throw std::logic_error("load_analysis needs data first");
        st_ = St::AnalysisLoaded;
    }
    void compute_ipa()   { ensure(St::AnalysisLoaded, "compute_ipa"); st_ = St::IpaComputed; }
    void update_ipa()    { ensure(St::IpaComputed, "update_ipa");     /*留在 IpaComputed*/ }
    void free()          { if (st_ == St::Idle) throw std::logic_error("double free");
                           st_ = st_ == St::IpaComputed ? St::Freed : St::Idle; }
private:
    St st_ = St::Idle;
};
} // namespace oct
```
> 语义对齐宿主：Allocated≈VGPU_Allocate_Parameter_Manager 完成；StreamingFrame≈实时链每帧（W05）；PullbackBulk≈回拉批（W06）；AnalysisLoaded≈轮廓分析后 IPA 输入就绪（W10）；IpaComputed≈VGPU_Calculate_Ipa_Result 完成可 Update（W12）。

## 4. 与 GpuWorker/PipelineEngine 整合（W13D2）
```cpp
// 每轮 run_loop：
//   状态决定调哪个 engine 方法；engine 方法内部先 state_.ensure 再动手
void GpuWorker::run_loop() {
    while (active_) {
        auto job = take();
        switch (state_.state()) {
        case oct::St::Allocated:  state_.stream_frame(); engine_.process_frame(job); break;
        case oct::St::StreamingFrame: engine_.process_frame(job); break;  // 继续拉
        case oct::St::AnalysisLoaded: state_.compute_ipa(); engine_.compute_ipa(job); break;
        default: /* idle/freed: 空转 */ break;
        }
    }
}
```

## 5. 自测（GTest）
1. 合法序列全绿：allocate→stream×N→load_analysis→compute_ipa→update_ipa×M→free；
2. 非法序列抛异常：double allocate / compute_ipa 不加载直接算 / free 后 stream_frame / allocate 前 free；
3. 每步 ensure 错误信息含 API 名与当前状态（可读性）。

## 6. DoD 打卡
- [ ] PipelineState + 单测（合法/非法两组）通过
- [ ] 与 GpuWorker 整合跑 1000 帧状态全正确

## 明日预告
W13 REVIEW + “线程 / Stream / 状态机 / 显存横切”面试要点。
