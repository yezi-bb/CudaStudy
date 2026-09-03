# Week14 / Day05 — 学习记录（源码填充版）

> 主题：广度周复盘 + P0 缺口列表（交付 Week15 消灭）。

## 1. 本周回顾
D1 导入矩阵（4 入口/OneFrame 单帧主路径/ImportAdapter）→ D2 缩略与导出子集（= 同一成像链抽样编码；U16 交接）→ D3 NVAPI 温度/显示（compute vs display 分界）→ D4 VTK GPU 体绘制（VGPU 产“体”、VTK 负责“看”）。

## 2. P0 缺口盘点（对照 00_全局规划.md §6 L115-119）
状态标记：✅笔记级已覆盖（含 cpu_* 伪代码/规格）；⬜开源工程实物未落地（W15 做）。

| P0 项 | 状态 | 笔记出处 | Week15 动作 |
| --- | --- | --- | --- |
| Allocate 语义 | ✅ | W01D1-2 | 并入 oct::Context |
| Resampling+Window | ✅ | W02D1-3 | oct::ResampleWindow |
| FFT+Log | ✅ | W03D1-3 | oct::FftLog（W02 起已开 kernel） |
| Transpose | ✅ | W04D1-2 | oct::TransposeCrop |
| DSC | ✅ | W04D3-4 | oct::Dsc |
| Enhancement+Gray2Color | ✅ | W05D1-3 | oct::EnhanceColor |
| e2e Scan | ✅ | W05D4-5 | oct::E2E::frame |
| Pullback batch | ✅ | W06D1-5 | oct::PullbackBatch（02 状态机 PullbackBulk） |
| Calib 简化 | ✅ | W07D3-4 | oct::Calib |
| Detect 简化 | ✅ | W08D1-4 | oct::Detect |
| 连续校准/拼接简化 | ✅ | W09D1-4 | oct::StitchContCalib |
| IPA μ 骨架 | ✅ | W10-11 | oct::Ipa::calculate |
| UpdateIPA 数值管线 | ✅ | W12 | oct::Ipa::update |
| Streams | ✅ | W13D3 | oct::E2E::framepipe |
P1 缺口（强烈建议，W15 有余力做）：Texture DSC、U16 压缩路径、检测 hooks 完整集成、Import/Export 抽样器。
P2（加分项）：VTK 集成（已有 C++ 侧 LUT 认知）、CUDA-GL。

## 3. “缺口”本质一句话
**知识 100% 就位（16 周 Note），代码 40% 已落 OCTCudaProject（Context/FftLog…），剩余 60% 是“把笔记里的 cpu_* 片段/规格搬进 src + 用合成数据把每个 DoD 跑绿”。**

## 4. DoD 打卡
- [x] gap list 明确可执行（§2，Week15 按行消费）
- [x] Week14/REVIEW.md 生成

## 明日预告
Week15：作品集打磨——按 gap list 落地源码 + 合成验收 + README/演示。
