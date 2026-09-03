# Week12 / Day04 — 学习记录（源码填充版）

> 主题：IPA 与实时成像的 GPU 显存争用——监控与缓解（面试故事）。

## 1. 今日目标（回顾）
结合宿主显存日志与 W01 健康 API，把“IPA 后台大缓冲 vs 实时成像”的争用讲成完整故事，并给出开源统一 Context 分配器草图。

## 2. 宿主监控手法（真实，行号已核对）
IPAAlgorithmController.cpp：
- L534-547 `GPU_GetCurrentGPUMemory(bool bInit, QString pos)`：封装 `VGPU_GetCurrentGPUMemory(total, free, used)` + RUNLOG 前后对比，返回 true。
- L203/L248：IPAProcessing 开始前 Init、结束后 Release 各打一次；
- L378/L420：ProcessingOneFrame 单帧路径同款（**证明连单帧更新都在监控**）；
BackgroundIPAUpdateThreadController.cpp L833-842/L941-952：StartComputingIPA / ProcessIPAAxialImageData 前后同款打印“Release GPU Memory”。

**监控语义**：日志用 `used_memory_end/free_memory_end` 前后差来定位“某段代码把显存吃掉了多少”——是**调参与回归检查工具**，不是运行时 OOM 防护。

## 3. 争用来源（数据量算清）
| 谁 | 什么时候 | 大约占显存 |
| --- | --- | --- |
| 实时成像（W02-06） | 采集/预览中 | FFT 卷 + 圆图 + 中间缓冲 |
| 回拉批上传（W06） | 回拉时 | 原始 U16 卷 |
| IPA Processing（W11） | 预处理分析 | FFT U16 + μ 体(550帧≈**1.13GB**) + 内部工作缓冲 |
| Update（W12） | 拖动阈值 | 很小（线 μ + 色图） |

两者**都住同一张 GPU**：回拉分析（重 μ）通常与采集错峰；但窗口/卷切换、PCI 拼接同时进行时，可能瞬时逼近上限 → 需要：
1. **监控**（上面 helper 日志，肉眼查回归）；
2. **健康 API**（W01）：`VGPU_GetCudaErrorStatus()` 拿错误码、`VGPU_GetCurrentGPUMemory()` 拿余量、`VGPU_ResetCudaMemory()`/`VGPU_Reallocate_memory()` 恢复；
3. **取消/降级**（W12D2 线程）：is_stop_thread_、退后台标记，让重任务随时可弃，把显存让给采集。

## 4. 面试故事（讲法）
“回放/分析场景里 IPA 后台线程要一次性放 μ 体 ≈1.1GB，而采集线程还在持续成像。宿主在两个重函数前后都封装 GPU 内存快照打日志（IPAAlgorithmController L203/248/378/420），出现显存不足时靠 W01 的健康 API 恢复；同时重任务整体可取消（退出门+后台标记），保证采集永远优先。所以我的开源侧要做一个**统一显存记账的 Context 分配器**，把‘申请前查余量、超限先释放缓存、失败转健康检查’做成一条通用路径。”

## 5. 开源 allocator 草图（落点 OCTCudaProject/oct/Context）
```cpp
namespace oct {
struct MemStat { double total, free, used; };

class Context {                       // 统一显存记账分配器（草图）
public:
    void* alloc(size_t bytes, const char* tag) {
        if (used_ + bytes > budget_) {          // ① 申请前预算检查
            release_cached(tag);                // ② 先释放可丢弃缓存（结果图/临时）
            try_health_recovery();              // ③ GetCudaErrorStatus → Reallocate
        }
        void* p = nullptr; cudaMalloc(&p, bytes);
        if (!p) { record_error(tag, bytes); return nullptr; }
        used_ += bytes; tags_[p] = tag;         // ④ 记账（可查询谁吃的显存）
        return p;
    }
    void free(void* p) { if (p) { used_ -= /*记账*/; cudaFree(p); } }
    MemStat snapshot();                          // ⑤ 同宿主日志：print Init/Release 差
private:
    double used_ = 0, budget_ = /*默认70%总显存*/0;
    std::unordered_map<void*, std::string> tags_;
};
}
```
对齐点：`snapshot()`≈宿主 `GPU_GetCurrentGPUMemory`；`budget_`≈产品在重任务前的“内存帧数安全判断”（IPAProcessing L206）；失败路径≈健康 API 三件套（W01）。

## 6. 自测
1. 用 Context 重写 W11 ipa_mu 的显存申请，跑日志对比宿主格式；
2. 模拟超预算：故意把 budget_ 调小 → 应触发 release_cached/health 且不崩；
3. 写出“争用缓解三层”：监控→健康恢复→可取消（每层对应 2 个宿主行号）。

## 7. DoD 打卡
- [x] 争用与缓解笔记（§3-4）
- [x] allocator 草图（§5）——面试能画出三层缓解

## 明日预告
写 15 分钟 IPA 口述稿（Week12/talk_ipa.md）+ W12 REVIEW。
