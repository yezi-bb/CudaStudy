# -*- coding: utf-8 -*-
"""Generate WeekXX/DayYY/Note.md from TASK.md for OCTCuda curriculum.

Company source root: E:\\OCT10\\AIOCT
"""
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AIOCT = Path(r"E:\OCT10\AIOCT")
LEARN = Path(r"E:\CUDA\Learning\CudaStudy\OCTCuda")
CMAKE = LEARN / "OCTCudaProject" / "OCTCudaCmake"
CUDATOOL = Path(r"E:\CUDA\Learning\CudaStudy\CudaTool")

# Short name → absolute path under AIOCT
PATH_MAP = {
    "Algorithm/vgpu/include/VGPU_Process.cuh": AIOCT / "Algorithm/vgpu/include/VGPU_Process.cuh",
    "Algorithm/vgpu/include/windata.h": AIOCT / "Algorithm/vgpu/include/windata.h",
    "ProjectP60_1.5/IS05.vcxproj": AIOCT / "ProjectP60_1.5/IS05.vcxproj",
    "ImageProcessingController.cpp": AIOCT
    / "Source/Controllers/AlgorithmControllers/ImageProcessingController.cpp",
    "ImageProcessingController": AIOCT
    / "Source/Controllers/AlgorithmControllers/ImageProcessingController.cpp",
    "GpuHandlingDataThreadController.cpp": AIOCT
    / "Source/Controllers/ThreadManagementControllers/GpuHandlingDataThreadController.cpp",
    "GpuHandlingDataThreadController": AIOCT
    / "Source/Controllers/ThreadManagementControllers/GpuHandlingDataThreadController.cpp",
    "MainWindowView.cpp": AIOCT / "Source/View/ViewSource/MainWindow/MainWindowView.cpp",
    "MainWindow": AIOCT / "Source/View/ViewSource/MainWindow/MainWindowView.cpp",
    "IPAAlgorithmController.cpp": AIOCT
    / "Source/View/ViewSource/Analysis/IPAAlgorithmController.cpp",
    "IPAAlgorithmController": AIOCT
    / "Source/View/ViewSource/Analysis/IPAAlgorithmController.cpp",
    "BackgroundIPAUpdateThreadController.cpp": AIOCT
    / "Source/View/ViewSource/Analysis/BackgroundIPAUpdateThreadController.cpp",
    "BackgroundIPAUpdateThreadController": AIOCT
    / "Source/View/ViewSource/Analysis/BackgroundIPAUpdateThreadController.cpp",
    "IPAZoneController.cpp": AIOCT / "Source/View/ViewSource/Analysis/IPAZoneController.cpp",
    "IPAZoneController": AIOCT / "Source/View/ViewSource/Analysis/IPAZoneController.cpp",
    "IntegrationChannel.cpp": AIOCT / "Source/View/ViewSource/Analysis/IntegrationChannel.cpp",
    "IntegrationChannel": AIOCT / "Source/View/ViewSource/Analysis/IntegrationChannel.cpp",
    "08Code/Algorithm/Analysis/include/IpaAlgorithmKernel.cuh": AIOCT
    / "08Code/Algorithm/Analysis/include/IpaAlgorithmKernel.cuh",
    "IpaAlgorithmKernel.cuh": AIOCT
    / "08Code/Algorithm/Analysis/include/IpaAlgorithmKernel.cuh",
    "GlobalConstantValue.h": AIOCT / "Source/Managers/GlobalConstantValue.h",
    "GlobalConstantValueBase.h": AIOCT / "Source/Managers/GlobalConstantValueBase.h",
    "VGPU_Process.cuh": AIOCT / "Algorithm/vgpu/include/VGPU_Process.cuh",
    "windata.h": AIOCT / "Algorithm/vgpu/include/windata.h",
}


def resolve_read(item: str) -> str:
    s = item.strip()
    # Prefer longer key matches (e.g. ImageProcessingController.cpp before shorter stems)
    for key, path in sorted(PATH_MAP.items(), key=lambda kv: -len(kv[0])):
        if key in s:
            return f"`{path}` — {s}"
    # Relative AIOCT / OCTCuda paths appearing in the bullet
    m = re.search(
        r"(Algorithm/[\w./]+|Source/[\w./]+|ProjectP60_1\.5/[\w./]+|08Code/[\w./]+|OCTCuda/[\w./]+|0[0-3]_[\w./]+)",
        s,
    )
    if m:
        rel = m.group(1)
        if rel.startswith("OCTCuda/"):
            return f"`{LEARN / rel[len('OCTCuda/'):]}` — {s}"
        if re.match(r"0[0-3]_", rel):
            return f"`{LEARN / rel}` — {s}"
        return f"`{AIOCT / rel.replace('/', os.sep)}` — {s}"
    return s


def parse_task(text: str) -> dict:
    def section(name: str) -> str:
        m = re.search(
            rf"## {re.escape(name)}\s*\n(.*?)(?=\n## |\n---|\Z)",
            text,
            re.S,
        )
        return (m.group(1).strip() if m else "")

    goal = section("今日目标")
    reads_raw = section("必读代码 / 文档")
    api_block = section("API 精读（功能 → 如何实现）")
    hands_raw = section("动手任务")
    refs_raw = section("任务参考")
    dod_raw = section("完成标准（DoD）")
    nxt = section("明日预告")

    # Only APIs listed under 「涉及接口 / 主题」
    theme_m = re.search(
        r"\*\*涉及接口 / 主题：\*\*\s*\n(.*?)(?=\n\*\*功能|\n>|\Z)",
        api_block,
        re.S,
    )
    theme_block = theme_m.group(1) if theme_m else api_block
    apis = re.findall(r"`([^`]+)`", theme_block)
    seen = set()
    apis_u = []
    for a in apis:
        if a not in seen and not a.startswith("全文件") and "接口全解" not in a and "调用链" not in a:
            seen.add(a)
            apis_u.append(a)

    how_m = re.search(r"\*\*功能与实现要点：\*\*\s*\n(.*?)(?=\n>|\Z)", api_block, re.S)
    how = how_m.group(1).strip() if how_m else ""

    def bullets(block: str) -> list[str]:
        out = []
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("- "):
                out.append(line[2:].strip())
            elif line.startswith("- [ ]") or line.startswith("- [x]"):
                out.append(re.sub(r"^- \[[ x]\]\s*", "", line))
        return out

    return {
        "goal": goal,
        "reads": bullets(reads_raw),
        "apis": apis_u,
        "how": how,
        "hands": bullets(hands_raw),
        "refs": bullets(refs_raw),
        "dod": bullets(dod_raw),
        "nxt": nxt,
    }


def week_theme(week: int) -> str:
    themes = {
        1: "环境与内存 API",
        2: "重采样与窗",
        3: "FFT / Log",
        4: "Transpose / DSC",
        5: "增强与 e2e",
        6: "回拉批处理",
        7: "导管校准",
        8: "检测类 API",
        9: "连续校准 / 拼接",
        10: "IPA 参数与理论",
        11: "IPA 主计算",
        12: "IPA 更新与线程",
        13: "实时架构 / Streams",
        14: "广度补齐",
        15: "作品集",
        16: "求职闭环",
    }
    return themes.get(week, "")


def render_note(week: int, day: int, t: dict) -> str:
    title = f"# Week {week:02d} / Day {day:02d} — 学习记录"
    reads_lines = "\n".join(f"- {resolve_read(r)}" for r in t["reads"]) or "- （见 TASK）"
    api_lines = "\n".join(f"- `{a}`" for a in t["apis"]) or "- （见 TASK）"
    hands_lines = "\n".join(f"- [ ] {h}" for h in t["hands"]) or "- [ ] （见 TASK）"
    dod_lines = "\n".join(f"- [ ] {d}" for d in t["dod"]) or "- [ ] （见 TASK）"
    refs_lines = "\n".join(f"- {r}" for r in t["refs"]) or "- （见 TASK）"
    how = t["how"] or "（见 TASK「功能与实现要点」与 `01_API接口全解.md`）"

    # path cheat for imaging weeks
    host_hint = f"""
## 公司源码路径（AIOCT）

- 根目录：`{AIOCT}`
- GPU API：`{AIOCT / 'Algorithm/vgpu/include/VGPU_Process.cuh'}`
- 成像编排：`{AIOCT / 'Source/Controllers/AlgorithmControllers/ImageProcessingController.cpp'}`
- GPU 线程：`{AIOCT / 'Source/Controllers/ThreadManagementControllers/GpuHandlingDataThreadController.cpp'}`
- 尺寸常量：`{AIOCT / 'Source/Managers/GlobalConstantValueBase.h'}`（Ls=1000, Lp=497, H=W=704, F55=550）
- 开源仓：`{CMAKE}`
- 学习文档：`{LEARN}`
""".strip()

    return f"""{title}

> 周主题：{week_theme(week)}  
> 依据：同目录 `TASK.md`；公司仓只读对照 **`{AIOCT}`**。  
> 字段级说明：`{LEARN / '01_API接口全解.md'}`；调用链：`{LEARN / '02_数据流与调用链.md'}`。

## 1. 今日目标

{t['goal']}

## 2. 必读（已映射绝对路径）

{reads_lines}

{host_hint}

## 3. API / 主题

{api_lines}

### 功能与实现要点

{how}

## 4. 动手任务清单

{hands_lines}

## 5. 参考

{refs_lines}

## 6. 完成标准（DoD）

{dod_lines}

## 7. 学习笔记区（自行补充）

- 关键结论：
- 宿主调用行号 / 参数：
- 开源实现落点（`{CMAKE}`）：
- 疑问：

## 8. 明日预告

{t['nxt'] or '（见 TASK）'}

---

*打卡：`{LEARN / '03_进度追踪.md'}`。合规：不逆向 DLL、不开源患者/标定真值。*
"""


# ---------- Week01 richer overrides (verified against E:\\OCT10\\AIOCT) ----------

W01 = {}

W01[1] = f"""# Week 01 / Day 01 — 学习记录

> 对照练习库：`{CUDATOOL}`  
> 开源骨架：`{CMAKE}`  
> 公司仓根目录（只读）：`{AIOCT}`

## 0. 源码路径对照

| 主题 | 绝对路径 |
|------|----------|
| GPU API | `{AIOCT / 'Algorithm/vgpu/include/VGPU_Process.cuh'}` |
| 工程链接 | `{AIOCT / 'ProjectP60_1.5/IS05.vcxproj'}`（搜 cudart / cufft / VGPU_Process） |
| 单帧成像 | `{AIOCT / 'Source/Controllers/AlgorithmControllers/ImageProcessingController.cpp'}` |
| GPU 线程 | `{AIOCT / 'Source/Controllers/ThreadManagementControllers/GpuHandlingDataThreadController.cpp'}` |
| IPA | `{AIOCT / 'Source/View/ViewSource/Analysis/IPAAlgorithmController.cpp'}` |
| 尺寸常量 | `{AIOCT / 'Source/Managers/GlobalConstantValueBase.h'}` |
| 学习头镜像 | `{LEARN / 'vgpu/include/VGPU_Process.cuh'}` |

AIOCT 头文件与学习仓一致：已是 `VGPU_Allocate_Parameter_Manager` / `Free` / `GetCudaErrorStatus` 等拆分 API（非旧版单一 `Parameter_Manager`）。

## 1. 核心结论

OCT 主程序**不编译业务 `.cu`**。算法在 `VGPU_Process.dll`；宿主只 `#include` + 链 `.lib` + 运行加载 `.dll`。`CudaTool` / `OCTCudaCmake` 是同一模式的缩小版。

h/lib/dll 两层：NVIDIA（cudart/cufft）+ 公司业务库（VGPU_Process）。

简历不能只写「调用过 VGPU_Process」——要讲清边界、显存生命周期、`is_device_to_host`、管线。

## 2. 理论上 CUDA 在干什么

Host：`cudaMalloc` → H2D → `kernel<<<>>>` →（可选）D2H → `cudaFree`。  
OCT Scan：Allocate 一次 → 中间 `is_device_to_host=false` → 最后 Gray2Color true 上屏。

## 3. 依赖怎么建

`IS05.vcxproj`：`cudart.lib` + `cufft.lib` + `VGPU_Process.lib`。  
开源：`{CMAKE}` 用 CMake + `CUDA::cudart`。

## 4. Region 索引

见 `VGPU_Process.cuh` 的 `#pragma region`：参数与显存 / 扫描回拉 / 导管校准 / 造影剂 / 回拉后处理 / IPA。本日只建目录。

## 5. 动手 DoD

- [x] 能口述为何不能只写「调用过 VGPU_Process」
- [x] Region 函数名索引（见上 / Day01 精读）
- [ ] 本机 CUDA Toolkit / GPU 型号记入笔记

## 6. 明日

Allocate / Free / SetFunctionConfig / SetCalibrationData
"""

W01[2] = f"""# Week 01 / Day 02 — 学习记录

> 公司仓：`{AIOCT}`  
> 宿主：`...\\ImageProcessingController.cpp` → `CpuAndGpuMemoryAllocation` / `CpuAndGpuMemoryRelease`  
> API：`VGPU_Allocate_Parameter_Manager` / `Free` / `SetFunctionConfig` / `SetCalibrationData`  
> 常量：`GlobalConstantValueBase.h`

## 1. 先分配再算

```text
CpuAndGpuMemoryAllocation
  → VGPU_Allocate_Parameter_Manager(...)
  → VGPU_SetFunctionConfig(GetGlobalIsNeedRemoverDc())
每帧：只 H2D / kernel / 可选 D2H
CpuAndGpuMemoryRelease → VGPU_Free_Parament_Manager(true)
标定更新：VGPU_SetCalibrationData(m_calibration_data, GetGlobalPointsNumberPerLine())
```

Allocate 实测（约 229 行）：

```cpp
VGPU_Allocate_Parameter_Manager(
  GetGlobalCurrentPiuSpeed(), 0, 0,
  g_original_data_buf_lines_number_, g_scan_lines_number_, g_pullback_lines_number_,
  m_gpu_imagme_points_number_per_line,
  g_circle_image_height_, g_circle_image_width_,
  g_pullback55_total_frams_number_, m_calibration_data);
```

## 2. 尺寸实测

| 符号 | 常量 / Getter | 值 |
|------|---------------|-----|
| Lo | `g_original_data_buf_lines_number_` | 2000 |
| Ls | `g_scan_lines_number_` | 1000 |
| Lp | `g_pullback_lines_number_` | 497 |
| H,W | `g_circle_image_height/width_` | 704 |
| F | `g_pullback55_total_frams_number_` | 550 |
| N | `m_gpu_imagme_points_number_per_line` / Getter | 常 2048 |

## 3. ≥6 类 Device 缓冲公式

raw / raw_bulk(F) / windowed / fft+power / fft_vol / rect / circle / color。  
F 进 Allocate：bulk ≈ O(F×Lp×N)，550 档 GB 级，必须预留。

## 4. 开源

`oct::Context::init/shutdown` ↔ Allocate/Free。路径：`{CMAKE}`。

## 5. DoD

- [x] ≥6 类 buffer 公式
- [x] 能解释 F 为何进 Allocate
"""

W01[3] = f"""# Week 01 / Day 03 — 学习记录

> 公司仓：`{AIOCT}`  
> Status：`MainWindowView.cpp`、`RecordingThumbnailView.cpp`、`AnalysisViewManager.cpp` 调 `VGPU_GetCudaErrorStatus`，失败可自动关机保护  
> Memory/Reallocate：分析 / IPA / Python-DL 路径打点后重建  
> 开源桩：`{CMAKE / 'src/host/cuda_utils.hpp'}`

## 1. 结论

| API | AIOCT 落点 |
|-----|------------|
| `GetCudaErrorStatus` | MainWindow 等；false → 关机保护文案 |
| `GetCurrentGPUMemory` | IPA / Integration / Background 前后打点 |
| `Reallocate_memory` | DL/分析占用后重建成像缓冲 |
| `ResetCudaMemory` | 头文件有；严重故障后需再 Allocate |

口诀：缓冲没了卡还活 → Reallocate；上下文死 → Reset 再 Allocate。

## 2. 决策树

见同周规划：先 Status/Memory → sticky 则 Reset；仅池被拆则 Reallocate；空间不够勿 Reset。

## 3. DoD

- [x] 能讲 MainWindow Status 保护与 IPA Memory 日志原因
- [x] 决策树（上）
"""

W01[4] = f"""# Week 01 / Day 04 — 学习记录

> 开源工程：`{CMAKE}`  
> 公司仓只读：`{AIOCT}`  
> 步骤：`{CMAKE / '如何新建CMake工程.md'}`

## 1. 骨架

`include/oct`（shape/context）+ `src/host`（main/context/cuda_utils）+ `src/kernels`（Week02）+ tests/bench/docs。  
`oct::Context` ↔ Allocate/Free/Realloc/Memory/Status。

## 2. §8 模块名

Context / ResampleWindow / FftLog / TransposeCrop / Dsc / EnhanceColor / PullbackBatch / Calib / Detect / StitchContCalib / Ipa。

## 3. DoD

- [ ] 工程可配置编译（`oct_demo`）
- [ ] README 合规段
- [ ] 模块名对齐 §8
"""

W01[5] = f"""# Week 01 / Day 05 — 学习记录

> 公司仓：`{AIOCT}`  
> `HandleDataOfScanning`：`ImageProcessingController.cpp`  
> GPU 线程：`GpuHandlingDataThreadController.cpp`

## 1. DOCMotionType / is_device_to_host

status 选缓冲；bool 控制 D2H。主路径中间 false，最后 `Gray2Color(..., true)`。  
开源：`CopyPolicy` + `PipelinePhase` → `{CMAKE / 'include/oct/pipeline_types.hpp'}`（自行添加）。

## 2. 链 A 前三步

1. 采集写入 GPU 线程 one-frame buffer  
2. `is_need_gpu_processing`  
3. `HandleDataOfScanning(...)`

## 3. REVIEW

自建 `Week01/REVIEW.md`；勾选 `{LEARN / '03_进度追踪.md'}`。

## 4. DoD

- [ ] REVIEW.md  
- [ ] 默述链 A 前三步  
- [ ] 开源仓出现 CopyPolicy  
"""


def main() -> None:
    count = 0
    for week in range(1, 17):
        for day in range(1, 6):
            day_dir = ROOT / f"Week{week:02d}" / f"Day{day:02d}"
            task_path = day_dir / "TASK.md"
            note_path = day_dir / "Note.md"
            if not task_path.exists():
                print("missing", task_path)
                continue
            if week == 1 and day in W01:
                content = W01[day]
            else:
                parsed = parse_task(task_path.read_text(encoding="utf-8"))
                content = render_note(week, day, parsed)
            note_path.write_text(content, encoding="utf-8")
            count += 1
            print("wrote", note_path.relative_to(ROOT))
    print(f"done: {count} Note.md")


if __name__ == "__main__":
    main()
