# Week09 / Day04 — 学习记录（源码填充版）

> 主题：W09 Demo 联调——把 Day01-03 的 stitch + 连续 cut + 三件套渲染串成可跑演示，并沉淀文档。

## 1. 今日目标（回顾）
用合成卷端到端验证：连续 cut 相比统一 cut 的图像稳定性收益；两段 stitch 旋转对齐正确性；写简短设计与结论到 `notes/W09_continuous_calib_demo.md`。

## 2. Demo 数据与步骤（落点 OCTCudaProject，纯 CPU 可跑）
```
① 生成模拟长卷 volume: frames=300, lines=512, depth=640
   真实 cut_k = 130 + 18*sin(2πk/180) + 高斯(0,2)   // 缓慢漂移 + 抖动
   每帧内容：导管壁亮带画在 cut_k 附近，管腔低信号，血管壁带高信号
② cpu_continuous_calib → cuts_est[k]（W09D2）
③ 渲染三组圆图：
   A. 统一 cut = round(mean(cuts_est))
   B. 连续 cut = cuts_est
   C. 连续 cut + 用户把第 100 帧改为 150 → update_frame 只重算第 100 帧
④ 评价：导管区高度方差 A≫B；C 除第 100 帧外与 B 一致（增量正确）
```
```cpp
double ring_height_var(const std::vector<cv::Mat>& circles) {
    // 近似：每帧圆图中心往外的亮环行位置差 → 方差（越小 = 越稳定）
}
```
另一路 stitch 自测：
- far=帧 0..149、near=帧 150..299，near 整体旋转 37°；cpu_rolling_stitch 拼回 300 帧；
- 校验旋转帧的标记列整体平移 37 线、帧序连续（对照 W09D1 断言）。

## 3. 验收标准（写进 DoD）
1. 方差：A 的环高方差 ≥ 3×B 的环高方差（连续 cut 收益可见）；
2. update_frame 后仅第 100 帧差异 > 0，其余像素级一致；
3. stitch 旋转断言全绿，拼接长度 = 帧范围之和；
4. 输出 4 张对比 PNG（统一/连续/更新前后）能直接放进文档。

## 4. 一段话总结（面试可讲）
“回拉时导管壁深度逐帧漂移，统一裁剪会把管腔切错位；连续校准给每帧独立 cut，再配‘全卷重建 + 单帧更新 + 按需探测’三个粒度的出图接口，平衡了全量计算成本与交互实时性。拼接则是把两段不同 cut 先验的 FFT 卷在帧维按各自帧范围接成连续长卷，让下游单卷管线无感复用。”

## 5. DoD 打卡
- [ ] Demo 四步跑通，方差/增量/stitch 断言通过
- [ ] notes/W09_continuous_calib_demo.md 已写（设计与结果图）

## 明日预告
W09 REVIEW + IPA 预习：att_paras 结构体（16 字段）与 P60/P80/C7 参数分支（为 W10-12 铺路）。
