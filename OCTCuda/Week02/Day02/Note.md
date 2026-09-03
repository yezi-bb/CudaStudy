# Week02 / Day02 — 学习记录（源码填充版）

> 主题：CPU 黄金版 Resample+Window，作为 kernel 的验收 oracle。

## 1. 今日目标（回顾）
读透标定表用法 → 写逐行线性插值重采样 → 乘窗 → 存 CPU golden，供 CUDA 版 diff。

## 2. 数据形状（冠脉参考，来自宿主分配）

| 量 | 值 |
| --- | --- |
| 每帧线数 `scan_lines`(Ls) | 1000（回拉 497，见 GlobalConstantValueBase.h `g_scan_lines_number_` / `g_pullback_lines_number_`） |
| 每线点数 `points_per_aline`(N) | 2048（颈动脉 4096） |
| 输入 | `U16` 原始 DMA 数据（帧大小 `Ls×N×2B`） |
| 标定表 | `calibration_data[点]`：每个输出样本在“原始像素”上的目标位置（float，来自 `Calibration.txt`，宿主 `SetCalibrationData` 传入） |
| 窗 | `float[N]` Hann |

## 3. CPU golden 算法（参考实现）

```
对 每帧:  输入 raw[Ls*N] U16
  for line l in [0, Ls):
    for k in [0, N):
      if 使用标定表:  f = calib[l*N + k]           # 目标点在原像素域的浮点位置
      else(identity/线性映射简化):  f = k          # 或 f = k*scale + shift
      lo = floor(f); hi = lo+1; t = f-lo
      x  = interp(raw[(l*N+lo) mod N], raw[(l*N+hi) mod N], t)   # 端点回绕按表设计
      输出 out[l*N+k] = x * w[k]                    # 乘窗
```

要点：
- **逐 aline 独立** → 天然并行（线之间无依赖）。
- 标定表“到底映射什么”由标定文件决定（本仓只有闭源 DLL 行为，无法看内核），因此黄金版先支持 **identity + 单表两模式**，留 `map_mode` 参数；
- 输出域建议 `float`（比产品端可能保留的 U16 更利于 diff）。

## 4. 测试数据（合成，保证可复现）

```cpp
// 正弦扫描模拟一个接近“反射峰”的信号：
// raw(l, k) = 30000 + 1000*sin(2*pi*k/97) + noise(固定种子)
// 期望：identity 模式下 out 应等于 raw*w；peak 位置保持；窗后频谱旁瓣下降
```
golden 输出格式：`cpu_resample_window.bin`（float，`Ls*N`）+ 摘要（min/max/均值）。

## 5. 练习/验收
- [x] `include/oct/resample_window.hpp` 支持 `mode{identity, table}`；单测两种模式全跑（identity 强断言 + table 半像素回绕断言）
- [ ] 对 `N=2048,Ls=1000` 一帧运行 <100ms（CPU 未优化量级），并记录数值范围 —— 测试已加 `big` 参数，实跑后回填数值
- [ ] 为 Day03 kernel 保留逐行 diff 接口 —— 计划：测试同种子跑 CUDA 版后，对同一 `out` 求 `diff_max_rel`（max|a-b|/max|b|），届时在 Day03 的测试里加；golden 摘要行已具备对照锚点

## 5.1 实现落点（OCTCudaCmake）
| 文件 | 内容 |
| --- | --- |
| `include/oct/resample_window.hpp` | `ResampleMode{Identity,Table}`、`make_hann`、`resample_window_frame` 接口 + 语义注释 |
| `src/host/resample_window.cpp` | CPU 黄金版：窗只算一次、逐线逐点插值、端点回绕 `hi=(lo+1)%N`、越界兜底 `f<0→0 / f≥N→N-1` |
| `tests/test_resample_window.cpp` | 固定种子合成 **chirp**（f0=0.05→f1=0.4）；identity 强断言、table `k+0.5` 半像素断言、摘要/计时；传 `big` 跑冠脉真实尺寸 |
| `CMakeLists.txt` | `oct_core` 静态库（host 源全进库）+ `oct_test_resample` 注册 CTest |

> 注意：修正了一个端点 bug —— `f > N-1` 不能一律夹到 `N-1`，否则 `calib[k]=k+0.5` 在 `k=N-1` 时 `f=N-0.5` 被夹平、回绕分支失效；正确语义是只挡 `f≥N`（真越界），`f∈[N-1,N)` 走回绕插值。

## 6. 自测 Q&A
1. 为什么用浮点索引做插值而不直接取整？→ 标定目标不在整数像素上，直接取整会让 k 网格有 0.5 像素级错位，损伤轴向分辨率。
2. 逐线独立意味着 kernel 怎么铺线程？→ 可按 `(line, k)` 二维展平成一维 `Ls*N`（每线程一个输出样本），或一个 block 处理多条线以复用窗系数。
3. 帧原始数据布局是行主序吗？→ 是：`raw[l*N + k]`，同一 aline 连续，利于按行访问/共享内存搬运。

## 7. DoD 打卡
- [x] CPU golden 通过（identity + table 两模式断言已写，待本机 ctest 跑绿）
- [x] 数值摘要打印已内置测试（table 模式 + `big` 计时），实跑后回填本笔记

## 8. 本机验证命令
```powershell
cd E:\CUDA\Learning\CudaStudy\OCTCuda\OCTCudaProject\OCTCudaCmake
cmake -S . -B build -A x64
cmake --build build --config Release --target oct_test_resample
ctest --test-dir build -C Release --output-on-failure      # 小尺寸快检
.\build\Release\oct_test_resample.exe big                   # 真实尺寸 Ls=1000,N=2048 + 计时
```
预期输出：`PASS resample_window (identity + table)`；`big` 模式多一行 `table big summary: ... min/max/mean` 与 `timing: ... ms`，把这两行数值回填到 §5。

## 明日预告
把 CPU golden 搬到 CUDA kernel（`src/kernels/resample_kernel.cu`，加进 `oct_core` 源列表，同种子 diff）。
