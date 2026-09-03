# Week15 REVIEW — 作品集

## 1. 周产出
| 日 | 主题 | 交付 |
| --- | --- | --- |
| D1 | P0 落位 + 架构图 | 12 模块落位清单 + 脱敏 mermaid 链 A |
| D2 | 性能表 | docs/perf.md 模板（stage ms/fps/CPU/DSC v1v2 + 归档） |
| D3 | 精度报告 | docs/precision.md（误差表 + 局限声明） |
| D4 | IPA README + 合规 | oct::Ipa/README 免责/跑法/参数 + 00 §7 复查 |
| D5 | 自检 + demo 脚本 | run_all.ps1 + 简历数字草表 |

## 2. 事实基准
- OCTCudaProject/OCTCudaCmake 现状：include/oct 仅 context/shape；src/host 有 context.cpp/cuda_utils/main；kernels 空；bench/tests/docs 占位。
- P0 14 项对应模块与验收断言分布在 Week01-14 笔记；W15 动作 = 落到 src/ 并跑绿 tests。

## 3. 面试资产清单
README（架构图）→ docs/perf.md（数字）→ docs/precision.md（可信度）→ oct::Ipa（深水区 demo）→ tests（工程规范）→ 简历数字草表（W16 精修）。
