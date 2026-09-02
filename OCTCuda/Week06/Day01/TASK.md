# Week 06 / Day 01 — 任务说明

## 今日目标

精读回拉显存检查与整卷上传 API。

## 必读代码 / 文档

- VGPU_Check_pullback_Data_memory
- VGPU_Set_Original_pullback_Data_To_GPU
- GpuHandlingDataThreadController 回拉相关

## API 精读（功能 → 如何实现）

**涉及接口 / 主题：**

- `VGPU_Check_pullback_Data_memory`
- `VGPU_Set_Original_pullback_Data_To_GPU`

**功能与实现要点：**

上传前检查 VRAM；U16 与 Vivo U8 双通道；按 frame 偏移写入 bulk buffer。
实现：大块 H2D 或分块异步。

> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。

## 动手任务

- 字节估算 frames*alines*points*sizeof
- 开源 PullbackVolume::upload

## 任务参考

- 01 §5
- 02 链 B

## 完成标准（DoD）

- [ ] 估算与宿主帧数变量对应

## 明日预告

Handle_All_Preview / Get_All_FFT

---

*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*
