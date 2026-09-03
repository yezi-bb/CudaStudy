# W09 连续校准/拼接 Demo（私有学习笔记）

## 1. 结论速览
- 连续 cut（每帧 cut[]）圆图导管区高度方差显著小于统一 cut → 解决回拉中导管壁深度漂移导致的管腔切错位。
- update_frame 单帧更新与全卷重建结果在非目标帧像素级一致（缓存复用正确）。
- cpu_rolling_stitch 旋转 + 帧维拼接通过全部断言（旋转平移 / 帧序 / 长度）。

## 2. 数据流
```
长卷 volume ──cpu_continuous_calib──> cuts[k]（中值平滑）
cuts[] ──render_all──> 全卷圆图 circles[k]
第 k 帧调 cut ──update_frame(k, new_cut)──> 只重算 circles[k]
两段 FFT(远/近) ──cpu_rolling_stitch(旋转角)──> 拼接长卷 → 进同一渲染链
```

## 3. 复现命令/参数
- frames=300, lines=512, depth=640；真实 cut = 130+18·sin(2πk/180)+N(0,2)
- 旋转角 37°；update_frame 目标帧 100，new_cut=150
- 断言：方差 A≥3×B；增量仅第 100 帧不同；stitch 长度 = 帧范围之和

## 4. 对比图
（贴 A/B/C 三张圆图缩略 + stitch 前后截图）

## 5. 对应宿主 API
Get_All_Continuous_Calibration_Image（IntegrationChannel.cpp L4285/4360/6192/6284）、Update_Frame_Continuous_Calibration_Image（L6361）、Get_Lumen_Stitching_Denoising_Data（L5477-5478）。
