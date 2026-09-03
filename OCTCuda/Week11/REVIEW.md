# Week11 REVIEW — IPA μ 主计算（CPU + CUDA 教学实现）

## 1. 一周产出
| 日 | 主题 | 交付 |
| --- | --- | --- |
| D1 | 单 A-line μ 拟合 | cpu_aline_mu + 合成指数衰减测试（μ=0.3/0.9/1.8 rel.err<15%） |
| D2 | 卷级 μ + 掩膜 | cpu_volume_mu（frames×theta×depth）、lumen_b/labels/media=100 |
| D3 | CUDA kernel | ipa_mu.cu：一 A-line 一 block、shared 载线、GPU≈CPU(<1e-4) |
| D4 | μ→圆图 | 复用 oct::Dsc 出 uchar 圆图 PNG（icut 生效验证） |
| D5 | 输出归宿 | line_ipa_miu/frame_ipa_result/μ体/μ圆图/阈值 字典 |

## 2. 宿主源码锚点
- IPAProcessing（全卷）：IPAAlgorithmController.cpp L46-298
- ProcessingOneFrame（单帧）：L344-456（轮廓变化 → 只重算目标帧）
- 掩膜拷贝/帧偏移：L182-193、L355-374、L393
- 圆图写回：L400-410；pre_ipa 保存：L268-295、L423-439
- VGPU_Calculate_Ipa_Result 原型：cuh L438-439；All_Aline_Mu_Data_To_Image：L455-456

## 3. 核心尺寸/布局
- 单帧 rows×cols=theta×depth（500×1025）；alines=frames×theta
- μ 体帧外层（frame i 偏移 i*rows*cols）；line μ = frames×theta
- 单帧更新 = fft/lumen/labels/输出全部按 frame 偏移取段

## 4. 教学验证矩阵
- 合成 μ 双带卷 → line_mu 分段跟随
- 掩膜单测：label=0 跳过 / lumen 内为 0 / media 截断无伪 μ
- GPU≈CPU 固定窗策略 <1e-4；CPU→GPU 加速比记录于 Day03
- 圆图：μ 带=圆环，cut 数组驱动内径移动

## 5. 下周（W12）
VGPU_UpdateValueIPA：InlineIPA=line μ + 帧距/类型/阈值 → IPA_L/RangeMean/IPA_A/IPA_T + colorbar；BackgroundIPAUpdateThreadController / IPAZoneController 线程模型。
