# Week 01 / Day 01 — 任务说明

## 今日目标

建立 OCTCuda 学习上下文：弄清「无 .cu 源码」与「API+宿主」边界，搭好笔记与术语表。

## 必读代码 / 文档

- OCTCuda/README.md
- OCTCuda/00_全局规划.md
- Algorithm/vgpu/include/VGPU_Process.cuh（浏览 #pragma region 与函数名列表）
- ProjectP60_1.5/IS05.vcxproj 中搜索 cudart / cufft / VGPU_Process

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `全文件 region 目录建立（本日不深入单 API）`

**功能与实现要点：**

列出每个 region 下函数名表到 notes/W01_api_index.md。标注类别：成像主干 / 校准检测 / 批处理 / IPA。建立认知：内核在闭源 DLL，本仓是 API + 宿主编排。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 创建 OCTCuda/notes/ 目录
- 一页纸：公司仓 vs 未来开源仓职责对比
- 确认本机 CUDA Toolkit / GPU，写入笔记

## 任务参考

- 01_API接口全解.md §0
- CUDA C++ Programming Guide 第 1 章

## 完成标准（DoD）

- [ ] 能口述：为何简历不能只写「调用过 VGPU_Process」
- [ ] 已有 region 函数名索引
- [ ] 已记录本机 CUDA 环境

## 明日预告

精读 Allocate / Free / Memory / Status 等生命周期 API

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
