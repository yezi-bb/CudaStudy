# OCTCuda — 从 AIOCT GPU 代码到可就业 CUDA 能力

本目录是一份**可按天执行**的自学与复现计划，目标：

1. **完全理解**本仓库中与 CUDA 相关的主机编排与 `VGPU_Process.cuh` / IPA 接口语义；
2. 在**独立开源仓**中按接口功能复现同类算法（不复制闭源 DLL / 不泄密）；
3. 积累可写进简历的 kernel、Nsight 数据与口述材料，冲击较好的 GPU/CUDA 岗位。

---

## 文档索引

| 文件 | 用途 |
|------|------|
| [00_全局规划.md](00_全局规划.md) | 总目标、阶段、合规、验收标准、岗位对齐（详细版） |
| [01_API接口全解.md](01_API接口全解.md) | `VGPU_Process.cuh` 全接口：功能 / IO / 如何实现 / 精读周 |
| [02_数据流与调用链.md](02_数据流与调用链.md) | Scan / Pullback / Analysis / IPA 四条调用链 |
| [03_进度追踪.md](03_进度追踪.md) | 打卡表（自行勾选） |
| [WEEK_INDEX.md](WEEK_INDEX.md) | 16 周 × 5 天速查 |
| `WeekXX/DayYY/TASK.md` | **每日任务**（80 份）：目标 / 必读 / API 实现要点 / 动手 / 参考 / DoD |
| `notes/` | 个人笔记占位 |
| `_gen_tasks.py` | 任务文件生成脚本（改内容后可重跑） |

---

## 关键事实（开始前必读）

- **内核源码不在本仓库**：算法在闭源 `VGPU_Process.dll`；本仓库有完整 **API 头文件** + **Qt/C++ 主机编排**。
- **学习方式**：读 API → 读宿主调用 → 画数据流 → 在开源仓用 CUDA **等价实现** → Nsight 验证。
- **合规**：禁止把公司 DLL、标定表、患者数据、内部阈值表开源；公开仓只用合成数据 / 公开文献算法。

---

## 建议执行节奏

- **每周 5 个工作日**（`Day01`–`Day05`），周末复盘 `WeekXX/REVIEW.md`（第 5 天任务里会要求写）。
- 每日建议投入：**3–5 小时**（读代码 40% + 写复现 40% + 笔记/测试 20%）。
- 顺序：**不要跳 Week01–05**（管线主干）；IPA 在 Week10–12；求职作品集在 Week14–16。

---

## 与本仓库源码的对照入口

| 主题 | 路径 |
|------|------|
| GPU API | `Algorithm/vgpu/include/VGPU_Process.cuh` |
| 单帧成像编排 | `Source/Controllers/AlgorithmControllers/ImageProcessingController.cpp` |
| GPU 处理线程 | `Source/Controllers/ThreadManagementControllers/GpuHandlingDataThreadController.cpp` |
| IPA 计算 | `Source/View/ViewSource/Analysis/IPAAlgorithmController.cpp` |
| IPA 阈值更新 | `BackgroundIPAUpdateThreadController.cpp` / `IPAZoneController.cpp` |
| 旧 IPA API（对照） | `08Code/Algorithm/Analysis/include/IpaAlgorithmKernel.cuh` |

---

## 开源复现仓建议布局（Week01 Day05 起创建）

```text
oct-cuda-pipeline/          # 与 AIOCT 物理隔离的独立仓库
  CMakeLists.txt
  include/
  src/kernels/
  src/host/
  tests/
  bench/
  docs/
```

按日任务中的「实现参考」即在此仓落地；AIOCT 仅作**只读对照**。
