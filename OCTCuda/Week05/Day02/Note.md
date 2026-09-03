# Week05 / Day02 — 学习记录（源码填充版）

> 主题：Gray2Color 伪彩映射 + goldenMapArray 合规边界。

## 1. 今日目标（回顾）
实现灰度→伪彩 kernel（自造 palette），输出可存 PNG；明确公司 LUT 只理解、不外带。

## 2. 真实声明与枚举

```cpp
// VGPU_Process.cuh L273-274
bool VGPU_Gray2Color(cv::Mat& CpuMat, int enhance_img_rows, int enhance_img_cols, bool is_device_to_host);
// L130-141 ColorsMapType: Color_Golden=1, Color_Gray, ...(金/灰/等)，宿主默认取 ColorsMapType::Color_Golden
```
宿主调用（ImageProcessingController.cpp L650-652）：
```cpp
VGPU_Gray2Color(clolor_circle_mat, g_circle_image_height_, g_circle_image_width_, true);
```
- 输出 `CpuMat` 为 `CV_8UC3`（L873 先 `cv::Mat::zeros(..., CV_8UC3)` 分配）→ 每次 `true` 回拷（显示/录像需要）；
- 公司表在 `source\Algorithm\vgpu\include\goldenMapArray.h`：`ColorsMapType` 对应多个 256×3 LUT（uchar，BGR 顺序），仅用于“理解灰度↔颜色分布”，**不得复制其数值到开源仓/简历作品**。

## 3. 开源实现（合规做法：自造 palette）
```cpp
// include/oct/luts.hpp —— 自定义“增强灰度调色板”（自造，勿抄公司数组）
static __constant__ unsigned char kLut[256][3];   // 或 __device__ 常量表，启动前 cudaMemcpyToSymbol
__global__ void gray2colorKernel(const unsigned char* __restrict__ gray,
                                 unsigned char* __restrict__ bgr, int n) {
  int i = blockIdx.x*blockDim.x + threadIdx.x;
  if (i >= n) return;
  unsigned char g = gray[i];
  bgr[3*i+0] = kLut[g][0];  // B
  bgr[3*i+1] = kLut[g][1];  // G
  bgr[3*i+2] = kLut[g][2];  // R
}
```
自造 palette 建议（可复现性）：热金属/喷气/自定义渐变均可；写清生成公式（如分段线性 RGB 斜坡）保证任何人可重建、无版权问题。

## 4. 合规自检（DoD 交付，逐条打勾）
- [ ] 未复制 `goldenMapArray.h` 数值；只提过“存在 256×3 LUT，BGR”。
- [ ] 仓库 palette 由公开公式生成，注释说明来源。
- [ ] 工程无公司注释/常量/文件名（`VGPU_Process.cuh` 不进入开源仓；如有需白名单的仅函数签名）。
- [ ] README 合规段再次核对（含“自造数据/公开数据集”声明）。

## 5. cv::Mat 接入注意（实操坑）
- `clolor_circle_mat` 由宿主预分配 `CV_8UC3`；DLL 直接写 Mat 数据指针 → 学习版用 `cudaMemcpy D2H` 到 `mat.data` 即可等价；
- PNG 保存：`cv::imwrite("out.png", mat)`；先转 `cv::cvtColor`(BGR2RGB) 再存可避免颜色颠倒（或按 BGR 期望顺序存）。

## 6. 自测 Q&A
1. ColorsMapType 为什么是“map 而不是单色”？→ 每档灰度映射一种颜色，形成类“黄金/灰阶”的临床习惯配色，辅助判读。
2. Gray 档还需要查表吗？→ 是，查表输出 R=G=B=灰度值即可（或 kernel 直通），但走同一 LUT 结构更统一。
3. LUT 放 constant 内存还是 global？→ 256×3 小表放 constant/只读缓存最优；每像素查表一次不成为瓶颈。
4. 为什么实时必须 D2H？→ 显示用 cv::Mat/OpenCV 在主机；且 Qt/录像管线在 CPU 侧。是否记得链上除它外全程 false？→ 是（只有拍照/显示/导出 true）。
5. 合规红线是什么？→ 公司 LUT 数值、注释、常量名都不能进公开仓；宁可自造不完美，不冒险外泄。

## 7. DoD 打卡
- [ ] 伪彩图可保存 PNG（§5）
- [ ] 合规自检全过（§4）

## 明日预告
链 A e2e 串联 demo。
