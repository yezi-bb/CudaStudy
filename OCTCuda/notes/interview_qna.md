# 面试题库（自答，回链各周笔记）

## A. CUDA 基础
1. kernel 启动参数如何映射数据？→ grid/block/thread 三层；一维拉平 `idx=blockIdx.x*blockDim.x+threadIdx.x`（W11 ipa_mu 例子）。
2. shared memory bank conflict？→ 同 bank 串行化；padding 1 列/对角 tile（W04 transpose）。
3. 合并访问？→ 相邻线程访相邻地址；行优先按行展开；DSC 的写合并是重点（W04）。
4. reduction 高效写法？→ 块内两两归约 + shared + 避免 divergence；W11 sh_sum 树形归约参考。
5. transpose 优化三招？→ tile 载 shared、对角化防 bank、整行写回（W04D2）。
6. stream 与 event？→ stream=GPU 内队列；event=流间依赖；`cudaStreamWaitEvent` 而非全局同步（W13D3）。
7. pinned/async 拷贝？→ cudaMemcpyAsync 需 pinned；与计算重叠（W13）。
8. F32↔U16 何时用？→ 交接/省带宽用 U16，计算用 F32；有量化误差需测（W03/W15D3）。
9. 原子/锁？→ 归约先 shared 后原子避免锁竞争；宿主临界区只护共享结果（W13D1）。

## B. 管线架构
10. 链 A 各 stage？→ Resample+Win→FFT/Log→Transpose+cut→DSC→Enhance（W05）。
11. 单帧 vs 全卷差异？→ 帧偏移取段 + 逐帧写回；全卷有 1.1GB μ 体（W11D5）。
12. 为什么 DSC 前用方图？→ 校准/检测在极坐标更简单；DSC 只做显示/标注坐标（W04/W07）。
13. cut/catheterCut 语义？→ 跳过导管近场先验；连续校准给 per-frame cut[]（W07/W09）。
14. 线程模型？→ 常驻线程+标志轮询+两级异常；优雅停止三序（W13D1）。
15. 状态机为何？→ “允许的 API 子集”显式化；非法抛异常（W13D4）。
16. 显存健康 API？→ GetCudaErrorStatus/GetCurrentGPUMemory/Reset/Reallocate（W01/W12D4）。
17. 按需回拷？→ is_device_to_host=false 默认；现场图/检查图才 D2H（W02/W08）。

## C. IPA
18. IPA 在测什么？→ 每 A-line 深度 log 强度衰减斜率→μ；脂质高 μ（W10）。
19. att_paras 哪些是派生？→ step=ceil(比例×minwin)；参数只调小集合（W10D2）。
20. Calculate vs Update？→ 重算 μ vs 轻聚合上色；一次重算多次轻更新（W12）。
21. 6 输出是谁？→ IPA_L/RangeMean/A/T + A/L colorbar（W12D1）。
22. 输入依赖？→ lumen/labels 先由预处理产生，IPA 才可算（W10D3）。
23. 合规怎么答？→ 教学复现、参数黑盒、非诊断用途（W15D4）。

## D. 场景题
24. “帧率不够怎么办？”→ 先测各 stage ms（Nsight）→ 热点 DSC/重采样 → v2 插值/双流流水（W15D2）。
25. “图像有旋转错位？”→ W09 旋转= A-line 圆周移位；检查旋转角换算与 near/far 参照。
