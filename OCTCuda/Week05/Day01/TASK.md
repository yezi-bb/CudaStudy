# Week 05 / Day 01 — 任务说明

## 今日目标

精读灰度增强四种模式与宿主边界/gamma 参数。

## 必读代码 / 文档

- VGPU_Image_Enhancement
- GrayEnhanceType
- ImageProcessingController 增强分支

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Image_Enhancement`

**功能与实现要点：**

DSC float→显示灰度：Linear/Pow/Log/Exp；low/up_bound、pow_index。
注意头文件中 is_device_to_host 类型为 int。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- CPU 实现四种增强
- 与宿主默认类型对照表

## 任务参考

- display windowing / gamma

## 完成标准（DoD）

- [ ] 四种可切换
- [ ] 参数命名对照表

## 明日预告

Gray2Color 伪彩

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
