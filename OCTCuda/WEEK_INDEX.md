# 周任务速查索引

每日详情：`WeekXX/DayYY/TASK.md`（共 16×5 = **80** 天）。

| 周 | 主题 | Day1 | Day2 | Day3 | Day4 | Day5 |
|----|------|------|------|------|------|------|
| [W01](Week01/Day01/TASK.md) | 环境与内存 API | 边界与索引 | Allocate/Free | 健康/Reset | 开源骨架 | MotionType 复盘 |
| [W02](Week02/Day01/TASK.md) | 重采样与窗 | 物理动机 | CPU 黄金版 | CUDA window | Vivo/Pullback | Profile+REVIEW |
| [W03](Week03/Day01/TASK.md) | FFT / Log | 两套 FFT API | cuFFT stage | U16↔F32 | 旧 Log 兼容 | Pullback 捷径 |
| [W04](Week04/Day01/TASK.md) | Transpose / DSC | Transpose | tile 优化 | DSC 公式 | 双线性 CUDA | texture+REVIEW |
| [W05](Week05/Day01/TASK.md) | 增强与 e2e | Enhancement | Gray2Color | 链 A e2e | Power_aline | 简历句 |
| [W06](Week06/Day01/TASK.md) | 回拉批处理 | 上传/检查 | 全帧 FFT | 方圆图批处理 | 分析灌 FFT | bulk demo |
| [W07](Week07/Day01/TASK.md) | 导管校准 | Catheter 主 API | 旧/cs 接口 | CPU 寻峰 | e2e auto_cut | 合规复盘 |
| [W08](Week08/Day01/TASK.md) | 检测类 | 造影剂 | 折断 | guiding | hooks 总图 | REVIEW |
| [W09](Week09/Day01/TASK.md) | 连续校准/拼接 | Stitching | GetContinuous | Continuous 出图 | demo | 预习 IPA |
| [W10](Week10/Day01/TASK.md) | IPA 参数 | 物理直觉 | att_paras 表 | Calculate 实参 | μ SPEC | REVIEW |
| [W11](Week11/Day01/TASK.md) | IPA 主计算 | CPU 单线 | CPU 掩膜卷 | CUDA μ | μ→圆图 | 输出字典 |
| [W12](Week12/Day01/TASK.md) | IPA 更新 | UpdateValue | 线程信号 | 开源 Update | 显存争用 | 口述稿 |
| [W13](Week13/Day01/TASK.md) | 实时架构 | GPU 线程 | 职责分层 | Streams | 状态机 | 面试要点 |
| [W14](Week14/Day01/TASK.md) | 广度补齐 | 竞品导入 | 缩略图导出 | NVAPI | VTK | gap list |
| [W15](Week15/Day01/TASK.md) | 作品集 | 补 P0 | perf 表 | precision | IPA 文档 | 自检 |
| [W16](Week16/Day01/TASK.md) | 求职闭环 | 简历 | 题库 | 白板 | 投递名单 | 总复盘 |

## 建议阅读顺序（开始第 1 天前）

1. [README.md](README.md)  
2. [00_全局规划.md](00_全局规划.md)  
3. [01_API接口全解.md](01_API接口全解.md)（可先扫目录，精读跟每日任务走）  
4. [02_数据流与调用链.md](02_数据流与调用链.md)  
5. [Week01/Day01/TASK.md](Week01/Day01/TASK.md)

## 再生任务文件

若需改模板后批量重生成：

```bash
python OCTCuda/_gen_tasks.py
```
