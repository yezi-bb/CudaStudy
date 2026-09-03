# Week16 / Day02 — 学习记录（源码填充版）

> 主题：面试题库与要点答案（notes/interview_qna.md）。

## 1. 今日目标（回顾）
≥15 题、分三块（CUDA 基础 / 管线架构 / IPA），每问给“要点答案 + 回链笔记行号”，可自问自答两轮。

## 2. 题库结构（详细内容见 notes/interview_qna.md）
- CUDA 基础：kernel 启动/Grid 映射、shared memory bank、合并访问、reduction、transpose、stream/event、pinned/统一内存、原子/归约、性能工具
- 管线架构：链 A/B/D、单帧 vs 全卷、状态机、线程模型、显存三 API、按需回拷、U16/F32 双格式、cut 语义、DSC 两版
- IPA：物理、att_paras、Calculate/Update 两阶段、6 输出、掩膜依赖、合规边界

## 3. 高频 5 题速答（口试前再过）
1. “线程 vs Stream？”→ W13：CPU 谁去调 vs GPU 怎么排；事件做流间依赖。
2. “如何优化 transpose？”→ W04：tile + shared，避免 bank conflict 用 padded/对角交换。
3. “显存不够怎么办？”→ W12D4：预算→释放缓存→健康三 API；重任务可取消。
4. “DSC 怎么做？”→ W04：极坐标每目标像素逆映射 (r,θ)→方图双线性采样；v2 行缓存。
5. “为什么拆 Calculate/Update？”→ W10-12：μ 一次算、阈值多次轻更新（聚合+上色）。

## 4. DoD 打卡
- [x] 题库 ≥15 题（notes/interview_qna.md），要点答案齐

## 明日预告
限时手写：tile transpose / reduction / DSC（白板模拟）。
