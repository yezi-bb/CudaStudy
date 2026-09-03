# Week16 REVIEW — 16 周总复盘

> 复盘人/日期：见维护计划首行。本文档回答三件事：**学了什么 / 覆盖到什么程度 / 接下来怎么保持**。

## 0. 一句话结论
16 周目标达成：能**默画 4 条调用链**、讲清链 A/B/D 每个 stage 的宿主调用点与公开语义，并有教学 kernel 草稿与白板手写能力；剩余风险集中在 **region 4/5 的自评深度**与 **OCTCudaCmake 落点尚未成码**——已转交 `maintenance_plan.md` 持续消化。

## 1. 本周（W16 求职闭环）交付
| Day | 产物 | 状态 |
| --- | --- | --- |
| D1 | `Week16/resume_gpu_draft.md`（4-6 条带数字 bullet + 开源项目段） | ☑ |
| D2 | `notes/interview_qna.md`（25 题：CUDA/管线/IPA，每问要点答案+回链） | ☑ |
| D3 | `notes/whiteboard/`（transpose/reduction/DSC 三题限时 + 易错点 + 口述词） | ☑ |
| D4 | `Week16/apply_list.md`（18 家 / 6 方向 / 每家 A·B·I·S 故事标签） | ☑ |
| D5 | 本文件 + `Week16/maintenance_plan.md` | ☑ |

## 2. 十六周主题压缩地图（复习入口）
| 周 | 主题 | 核心交付 / 入口 |
| --- | --- | --- |
| W01 | 环境与内存 API | Allocate/Free/Realloc + 健康三 API；`oct::Context` 语义 |
| W02 | 重采样与窗 | Resample_Scan/Vivo/Pullback；标定表插值 + Hann |
| W03 | FFT/Log | cuFFT batch、log 域、U16↔F32、cutfront25 |
| W04 | Transpose/DSC | tile 转置 + 极→直公式；白板 01/03 由此出题 |
| W05 | 增强与 e2e | Enhancement/Gray2Color 收尾链 A |
| W06 | 回拉批处理 | PullbackBatch：批量 H2D→跨帧 grid→少次 D2H |
| W07 | 导管校准 | cut/catheterCut 语义 + CPU 黄金版峰值校准 |
| W08 | 检测类 | 造影/折断/guiding hooks 逐条（`notes/W08_detect_hooks.md`） |
| W09 | 拼接/连续校准 | rolling stitch + continuous calib demo（`notes/W09_*.md`） |
| W10 | IPA 参数与理论 | 物理 + P60/P80/C7C8 表（`notes/W10_ipa_physics.md`、`W10_att_paras.md`） |
| W11 | IPA 主计算 | `cpu_aline_mu`/`cpu_volume_mu` + `ipa_mu.cu` kernel 骨架 |
| W12 | IPA 更新与线程 | UpdateValueIPA 语义 + 显存竞争/allocator（`notes/W12_ipa_threads.md`） |
| W13 | 实时线程与 Streams | s0/s1 流水、`oct::PipelineState` 状态机、异常→恢复 |
| W14 | 竞品/健康/显示 | import/缩略图/NVAPI/VTK 四路（`notes/W14_*.md`） |
| W15 | 作品集 | P0 模块回填 + README mermaid 链 A；perf/precision 模板 |
| W16 | 求职闭环 | resume / qna / 白板 / apply_list / maintenance |

## 3. VGPU region 覆盖率自评（1–5；<4 安排复习日）
按 `01_API接口全解.md` 的 region 划分：

| Region | 评分 | 依据笔记 | 短板 → 行动 |
| --- | --- | --- | --- |
| 1 参数配置与显存分配 | 4.5 | W01/W12D4/W13 | 显存三 API 与 allocator 已是草图，需成码 |
| 2 扫描/回拉核心成像链 | 5.0 | W02–W06/W13/W15 | 全 stage 有教学实现与 e2e 图 |
| 3 导管校准 | 4.0 | W07 | 自动校准峰值细节仍黑盒 → CPU 黄金版可扩展 |
| 4 造影/折断/guiding 检测 | 3.5 | W08 hooks | 只有语义无独立复现 → **复习日：挑 guiding 或折断做简化特征原型** |
| 5 回拉后处理/分析预处理 | 3.5 | W06/W14 | 竞品 C7C8/DCM 等多为读面 → **复习日：列 API 清单逐条标映射/延期** |
| 6 管腔拼接与连续校准 | 4.0 | W09 demo | 数据流通；实现为教学简化 |
| 7 IPA | 4.5 | W10–W12/W15D4 | 物理↔参数↔kernel↔线程全链，最扎实 |

**复习日（维护期前 2 周内完成）：** Region 4 → `notes/W08_detect_hooks.md` 重读 + CPU 简化原型；Region 5 → 用 `01_API接口全解.md` L215-237 清单做映射表，并在 `01` §9 逐条补勾选。

## 4. 00 §8 总验收清单对照
| 00 §8 条目 | 状态 | 说明 |
| --- | --- | --- |
| 01 各接口旁补「我的实现笔记」链接/勾选 | 🟡 部分 | 每 API 已挂「精读周」；`01` §9 自学勾选需维护期补全 |
| 能默画 4 条调用链 | ☑ | 02 文档 + W13 可默画 |
| 开源仓 e2e 重建 + Nsight + 测试 | 🟡 部分 | OCTCudaCmake 已立 `oct::` 命名空间与 context/shape；12 个目标文件待实现（W15 清单） |
| IPA 参数/μ/圆图/UpdateValue 四步能讲 | ☑ | W10-12 四步齐；interview_qna 有题 |
| 简历 4-6 条含数字；模拟面试过管线+DSC 题 | ☑ | resume_gpu_draft + qna(25) + 白板三件套 |

## 5. 求职材料包（面试前入口）
- 简历语言：`Week16/resume_gpu_draft.md`（数字从 W05/W11/W13 耗时表填）
- 题库 25：`notes/interview_qna.md`（高频 5 题速答在 W16D2 Note）
- 白板三件套：`notes/whiteboard/`
- 投递名单：`Week16/apply_list.md`（18 家 + 投前 3 步）
- 可持续节奏：`Week16/maintenance_plan.md`

## 6. 合规复核（贯穿 16 周）
- 未逆向/反汇编 `VGPU_Process.dll`；公开材料只用宿主调用点行号+签名+公开语义推导；
- 未在公开仓写公司阈值/患者/标定真值；学习产物在 **OCTCuda 私有目录**，开源仓模块命名用等价功能名（`oct::ResampleWindow` 等）；
- 白板/题库/简历均为合成数据 + 通用术语。

## 7. 遗留与风险
1. **OCTCudaCmake 成码度**：`src/kernels/` 为空 → P0 12 文件待写（优先 transpose_tile / reduce_aline / dsc / resample / fft_log）；
2. **Region 4/5 自评 <4**：见上表复习日；
3. **`01` §9 勾选**未逐条完成；
4. 简历数字需在每轮 benchmark 后回填最新值。

## 8. 下一步
按 `Week16/maintenance_plan.md` 执行：前 4 周把 3 个风险清零，随后进入双周节奏 + 投递循环。

*合规：同 00 §7。打卡见 `03_进度追踪.md`（本周末 W01–W16 全量勾选）。*
