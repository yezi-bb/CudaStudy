# Week 05 / Day 02 — 任务说明

## 今日目标

精读并实现 Gray2Color；对照 goldenMapArray（勿外泄公司 LUT）。

## 必读代码 / 文档

- VGPU_Gray2Color
- ColorsMapType
- goldenMapArray.h（只理解用途）
- ImageProcessingController Gray2Color(true)

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Gray2Color`

**功能与实现要点：**

constant LUT[256][3]；开源仓使用自造 palette，禁止复制公司表到公开仓。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- kernel 输出 BGR/PNG
- 合规自检

## 任务参考

- 01 §2 Gray2Color

## 完成标准（DoD）

- [ ] 伪彩图可保存
- [ ] 合规通过

## 明日预告

Scan e2e 串联

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
