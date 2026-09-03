# 白板 03 — DSC：极坐标 → 圆图（45 min）

## 题目（面试口吻）
> 「DSC 把一张『深度×角度』的极坐标矩形图（行=从导管中心向外的深度采样，列=0…359° 的 A 线）转成 704×704 的血管圆图。每个输出像素即一条光线。请推坐标公式并写出 CUDA 映射 kernel。双线性插值加分。讲清哪些像素不合法、该填什么。」

- 输入 `rect[raw_rows][raw_cols]`（float，行主序）；raw_rows=裁剪后深度，raw_cols=线数；
- 输出 `circle[H][W]`（H=W=704，0-based 像素）；
- `inner_r`：环带内半径（导管盲区，可=0）；`margin_r`：外缘留白（可=0）；`dr`：每像素对应多少深度行（学习版可调常量，产品用标定 mm/像素换算）。

## 参考答案

坐标公式（先画：输出像素 → 相对圆心的极坐标 (r, θ) → 矩形上的非整数 (row, col)）：
```
cx = W/2;  cy = H/2;
dx = x - cx;   dy = y - cy;
r   = sqrtf(dx*dx + dy*dy);
th  = atan2f(dy, dx);                          // [-π, π]
col = (int)((th + PI) / (2*PI) * raw_cols) % raw_cols;   // 角度 → 线号
row = r / dr;                                   // 半径 → 深度行号（- inner_r 视口径定义）
if (row < 0 || row >= raw_rows - margin_r)  → 不合法像素，写 0
```

```cuda
__global__ void dsc_kernel(const float* __restrict__ rect,
                           float* __restrict__ circle,
                           int raw_rows, int raw_cols,
                           int H, int W, int inner_r, int margin_r, float dr) {
    const int x = blockIdx.x * blockDim.x + threadIdx.x;
    const int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= W || y >= H) return;

    const float cx = W * 0.5f, cy = H * 0.5f;
    float dx = x - cx, dy = y - cy;
    float r  = sqrtf(dx * dx + dy * dy);
    float th = atan2f(dy, dx);
    float colf = (th + PI_F) / (2.f * PI_F) * raw_cols;  // 浮点保持精度
    int   col  = ((int)colf) % raw_cols;
    float rowf = r / dr;                       // 学习版；产品 = (r_mm - inner_r_mm)/采样间隔
    if (rowf < inner_r || rowf >= raw_rows - margin_r) { circle[y * W + x] = 0.f; return; }
    int row = (int)rowf;

    // 最近邻（先跑通）
    float v = rect[row * raw_cols + col];
    // 双线性（进阶）：取 row,row+1 × col,col+1 四个值按小数权重混合，
    // col 换列时注意 % raw_cols 回绕（360°=0° 连续）
    circle[y * W + x] = v;
}
// 启动：<<<dim3(ceil(W/32), ceil(H/32)), dim3(32,32)>>>，每输出像素一个线程。
```

## 易错点 / 检查单
- [ ] **每像素一线程、无数据竞争**：输出 704×704 每像素独立 → 天然并行，重点只在公式与边界；
- [ ] `atan2f(dy,dx)` 值域 [-π,π]：平移 `+π` 再除以 2π 才落在 [0,1)，否则负角度错位半圈；
- [ ] `rowf` 用浮点算、最后才转 int：先转 int 再比较会把小数位丢进边界判断；
- [ ] col 取模实现 360° 回绕；θ=±π 同一条线；
- [ ] 越界像素必须写 0（导管盲区 + 方图四角）+ 口述 `inner_r/margin_r` 与「row<0 兜底」的关系；
- [ ] 双线性采到 col+1 要取模（跨 0/359 边界）。

## 口述词（出声练）
「这是典型的 gather 型逆映射：圆图上每个像素发射一条光线，算出到导管圆心的半径和角度，反查矩形图的位置并采样——而不是把矩形 push 到圆上，那样会有空洞和重叠。704² 约 50 万像素、每像素独立，GPU 一个线程一个像素刚刚好。角度分辨率：最外圈周长约 2π·352≈2212 像素，而 1000 条线 + 双线性插值足够覆盖，704 只是显示分辨率。」

## 落点
OCTCudaProject/OCTCudaCmake/src/kernels/dsc_polar2cart.cu（naive 最近邻 → 双线性两版，CPU 黄金版对照）。
回链笔记：`Week04/Day03`（公式手推）与 `Week04/Day04`（双线性、CUDA naive→优化）。
