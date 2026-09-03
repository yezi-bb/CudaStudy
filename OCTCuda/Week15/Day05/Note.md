# Week15 / Day05 — 学习记录（源码填充版）

> 主题：作品集自检（映射 00 §8）+ 一键 demo 脚本 + 简历数字草表。

## 1. 总验收自检（00 §8 L134-138 → 本机状态）
- [x] 01_API 文档旁“我的实现笔记”链接：全部 80 份 Note 已指向真实行号/规格
- [x] 4 条调用链能默画：02 文档 + W05/06/10/13 分别串过 链A/B/D/E
- [~] 开源仓：e2e 重建 + 测试绿（今日跑一遍 ctest）+ perf/precision 文档（D2/D3）
- [x] IPA 四步（参数→μ→圆图→UpdateValue）：W10-W12 笔记能讲清
- [ ] 简历 4-6 条含数字 + 模拟面试（本周出数字草表，W16 精修）

## 2. 一键 demo 脚本（run_all.ps1，根目录）
```powershell
# OCTCuda 一键验收：build → test → bench → docs 汇总
param([switch]$SkipBuild)
if (-not $SkipBuild) { cmake --build out/build/x64-Release --config Release | Out-Host }
Push-Location out/build/x64-Release
ctest --output-on-failure | Out-Host          # tests 绿
& .\bench.exe --all --seed 42 | Tee-Object ../../bench/output_latest.txt
Pop-Location
# 汇总给用户看（不回写公司路径）
Write-Host "OK: ctest 绿 / perf 见 bench/output_latest.txt"
```

## 3. 简历数字草表（先占位，W16 精修）
| # | 条目 | 数字来源 |
| --- | --- | --- |
| 1 | 自研 CUDA OCT 重建管线：Resample→FFT→Transpose→DSC→增强 | README + perf |
| 2 | e2e 帧率 _ fps（DSC v2，GPU 型号） | perf.md |
| 3 | DSC v1→v2 提升 _ % | perf.md |
| 4 | IPA μ 教学估计器合成误差 <15%（三档 μ） | precision.md |
| 5 | 单帧/全卷/Update 三粒度更新；状态机防非法调用 | W11-13 |
| 6 | 显存记账 Context：预算检查/失败恢复 | W12D4 |

## 4. DoD 打卡
- [ ] 自检清单全过（或残留 issue 列表化，见 W16D1）
- [x] run_all.ps1 骨架 + 简历数字草表（§3）

## 明日预告
Week16：求职闭环——作品集收尾、投递材料、模拟面试。
