# Week07 / Day03 — 学习记录（源码填充版）

> 主题：公开简化版“导管壁检测”（CPU 实现）——每角度径向亮度峰 → 鲁棒中值 → cutHeight。
> 原则：**方法可公开，产品级阈值不外泄**（见 `00_全局规划.md` §7）。

## 1. 今日目标（回顾）
写一个不依赖 GPU/DLL 的 CPU 简化实现：输入一帧 transpose（深度×角度），自动定位导管壁所在深度行，输出可用于成像链的 cut 窗口；用合成圆环验证。

## 2. 坐标系与物理含义（先画清，再写码）
校准阶段宿主处理的是 **Transpose 后的方图**（极坐标未做 DSC）：

```
transpose 方图  data[dep][θ]：
  行 = 深度 r（从 0 到 cut_end-cut_start，约 700~1025）
  列 = 角度/线（0..g_scan_lines_number_，1000）
导管壁（绕导管一圈的高反射层）→ 在极坐标图里是“几乎水平的亮带”
  同心导管：每列在深度方向 profile 的峰 ≈ 同一行 R_wall
  偏心/倾斜导管：R_wall(θ) 随 θ 缓慢变化 → 需要“逐列寻峰 + 鲁棒汇总”
```
所以宿主口中“每角度径向亮度峰”= 对每列沿深度找最亮过渡带；而 `cutHeight` 是“导管直径/2 对应的像素行 + 余量”，本质是先验跳过近场导管区。

## 3. 宿主真实锚点（行号已核对）
- `ImageProcessingController.cpp L497`：`catheterCutHeight = round(导管直径/2/记录像素间距) + 15;`
- `L559-574`：`ECalibrationState` 内，`image_hight=cut_end-cut_start`（>7mm 视野按 7mm 折算，L562-565）；第 37 帧作参考；传 `image_hight, 1000` 给 `VGPU_Catheter_AutoCalibration`。
- `L586-594`：`EConnectCalibrationState` 用递增 `m_check_frame_index`，`is_twice_check` 随是否首次自检取反。
- 成功 → `ECalibrationState→EScanState`（L608）；失败 → 保持校准态继续存图（L603-615）。
- 校准真正的“产出”落在内部：精修后的深度窗口，实时链 L534 只 Transpose `[cut_start, cut_end)`。

## 4. 开源简化实现（cpu_catheter_peak，落点在 OCTCudaProject）

```cpp
// 输入：一帧 transpose，行=深度(H)，列=角度(W)，float，已 log
// 输出：导管壁行估计 R_wall + cut 窗口
struct CutResult { bool ok; double r_wall; int cut_start, cut_end; };

CutResult cpu_catheter_peak(const std::vector<float>& mat, int H, int W,
                            int catheter_cut_h_px /* = round(D/2/pix)+15 */,
                            int search_w /* 在 catheter_cut_h_px±search_w 内搜索 */)
{
    const int r0 = std::max(2, catheter_cut_h_px - search_w);   // 跳过导管近场
    const int r1 = std::min(H,   catheter_cut_h_px + search_w);
    std::vector<float> wall(H, 0.f);       // 按行聚合“该深度出现强反射的线占比”
    for (int c = 0; c < W; ++c) {
        // 1) 每列取径向 profile，做 3-tap 平滑去单点噪声
        // 2) 在 [r0,r1) 找“最大亮度”所在行（简化：argmax）
        float best = -1.f; int best_r = r0;
        for (int r = r0; r < r1; ++r) {
            float v = mat[(size_t)r * W + c];
            if (r > r0) v = (v + mat[(size_t)(r-1)*W+c]) * 0.5f; // 简单平滑
            if (v > best) { best = v; best_r = r; }
        }
        wall[best_r] += 1.f;               // 投票
    }
    // 3) 取“被最多线选为峰”的深度行 → 导管壁（同心时即水平亮带）
    int peak_r = (int)(std::max_element(wall.begin(), wall.end()) - wall.begin());
    double frac = wall[peak_r] / W;
    if (frac < 0.3) return {false, 0, 0, 0}; // 无一致导管壁 → 校准失败
    // 4) cut 窗口：跳过导管壁附近，进入管腔成像区
    int cut_start = peak_r + 3;             // 公开简化：导管外壁后 3px
    int cut_end   = std::min(H, peak_r + (H - peak_r) * 3 / 4);
    return {true, (double)peak_r, cut_start, cut_end};
}
```

> 说明：这是“方法公开、数值自定义”的教学版（用**逐列峰 + 直方图投票**代替产品内部的阈值流水线），符合合规边界。真正工程可改进：MAD 剔除偏心角度再拟合（见 Day04 失败模式）。

## 5. 合成圆环自测（可复制运行）
```cpp
// 造图：H×W 全 0.1 背景 + 半径 R 的高斯环 + 随机噪声
// 环：每列在 r≈R(1+e_θ) 处加亮带，e_θ 为 ±2% 的缓慢偏心扰动（模拟偏心）
for (int c = 0; c < W; ++c) {
    int rc = (int)(R * (1 + 0.02 * sin(6.28 * c / W)));
    for (int t = -4; t <= 4; ++t) mat[(size_t)(rc + t) * W + c] += 3.0f * expf(-t*t/8.f);
    // 再叠加高斯噪声 mat += 0.15*randn
}
auto cut = cpu_catheter_peak(mat, H, W, R - 40, 120);
assert(cut.ok && std::abs(cut.r_wall - R) < 3);   // 误差 < 3px
```
- 建议 `H=1024, W=720, R=180`：同一份代码应能“无真值表”自证正确。
- 练习进阶 1：让 `R` 随 θ 按椭圆变化（偏心导管），观察单半径失效 → 用中值/MAD 剔除离群角度。
- 练习进阶 2：把 `frac` 阈值提到 0.5，半圈遮挡（气泡）时应正确失败 → 对接 Day04 失败模式。

## 6. 自测 Q&A
1. 为什么在 transpose（方图）上做而不是圆图上？→ 校准在 DSC 之前（宿主 L534 Transpose → L572 校准 → L625 DSC），管线顺序如此，且方图上导管壁≈水平亮带，一维寻峰即可。
2. 逐列 argmax 与“鲁棒中值”什么关系？→ argmax 给每列候选，投票/中值在角度维度做鲁棒汇总，抵抗偏心与遮挡。
3. catheter_cut_h_px 里“+15”为何必要？→ 直径换算有误差、导管壁有厚度，+余量保证搜索带覆盖导管壁而非空腔内。
4. frac<0.3 返回 false 模拟了什么？→ 宿主里校准失败保持 ECalibrationState 并持续取下一帧重试（L603-615）。
5. 为什么说不追求数值一致？→ 产品用 GPU 内部阈值流水线（真值/调参属内部），开源只练“方法骨架+可测性”。

## 7. DoD 打卡
- [ ] cpu_catheter_peak 实现并入 OCTCudaProject
- [ ] 合成环自测通过（误差 <3px，遮挡时正确失败）

## 明日预告
校准失败模式 + e2e 的 auto_cut 开关。
