# 15 分钟 IPA 口述稿（私有学习用）

## 开场（1 分钟）
“我做的是血管内 OCT 回拉分析里的 IPA：每根 A-line 沿深度的光衰减系数 μ。脂质斑块散射吸收强，μ 高 → 我们按线/按帧聚合，输出毯展图和曲线给临床。”

## 1 物理（2 分钟）
I(z)=I0·e^(−μz)·G(z) → ln I=lnI0−μz+lnG。卷约 550 帧×500 线×1025 深 ≈2.8 亿样本 → GPU。
（图：一张 OCT 圆图 + 一条衰减曲线）

## 2 参数（2 分钟）
att_paras 两类字段：物理量(z0/zR/zw/SNR/noise)与派生量(step=ceil(比例×minwin))。三套配置本质是“机型×数据”查表：P60/P80(体内)与 C7C8(竞品, isVivo=false)。
（可谈：阈值默认在头文件、txt 可覆盖 → 调参工程习惯）

## 3 Calculate 重（3 分钟）
输入 FFT U16 卷 + reshaped_lumen[每线边界] + labels + media=100 → 内核逐 A-line 在 lumen 外深窗做对数斜率拟合得 μ(z)；输出 μ 体(≈1.1GB 550帧) + line μ。布局帧外层，单帧处理按 frame 偏移取段。
（自问：为什么在 FFT 方图上做？为什么 media 是标量？）

## 4 圆图（1 分钟）
μ 方图走与 DSC 同构的 API（All_Aline_Mu_Data_To_Image）→ 裁剪→极坐标转圆→uchar 量化。单帧改轮廓只重算那帧并写回卷序列对应段。

## 5 Update 轻（3 分钟）
用户只改一个阈值 InThresholdT，但 line μ 不用重算：VGPU_UpdateValueIPA 做 线超阈判定→着色、帧聚合出 IPA_L/RangeMean、线超出量 IPA_A、彩毯 IPA_T、A/L colorbar。这解释了为什么产品拆 Calculate/Update 两阶段：一次重算，多次毫秒级轻更新，拖阈值实时预览。

## 6 线程（2 分钟）
后台线程：SafeDicom 锁保护模型、is_stop_thread_ 随时可退、异常 __except 收口、完成 emit UpdateIpaValueSignal 通知渲染。显存上 IPA 与成像共用一张卡：重任务前后打 GPU 内存日志（IPAProcessing Init/Release），不足走健康 API 恢复；三层缓解=监控→健康恢复→可取消。

## 7 合规（1 分钟）
以上为教学复现，方法与公开头文件字段语义一致；产品数值/标定黑盒。
（自讲一遍，卡壳点回看 W10-12 笔记）
