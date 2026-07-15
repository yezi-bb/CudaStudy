# ExternPro — CUDA DLL 接口导出与模板实例化

学习重点：如何把 CUDA kernel **封装成可导出的接口**，以及模板在跨 DLL 时为什么必须做**显式实例化**。

---

## 1. 目标与分层

本工程把算法拆成两层：

| 层 | 放哪里 | 做什么 |
|----|--------|--------|
| **对外接口** | `CudaTool.h` 类成员（如 `LaunchBinaryKernel`） | 管显存分配、H2D/D2H、错误检查；给外部工程调用 |
| **内核启动实现** | `kernel.cu` 中的 `Launch*Impl` + `__global__` | 真正启动 GPU kernel；需导出到 DLL |

```text
外部调用 CudaTool::LaunchBinaryKernel(...)
        │  （模板实现在 .h 里，编译进调用方）
        ▼
   LaunchBinaryKernelImpl<T>(...)   ← 符号来自 CudaTool.dll
        │
        ▼
   BinaryKernel<<<grid, block>>>(...)
```

因此接口设计要同时解决两件事：

1. **普通函数 / 类**：用 `dllexport` / `dllimport` 宏正确导出  
2. **带模板的 GPU 启动函数**：模板代码本身不能“直接装进 DLL”，必须对具体类型做**显式实例化再导出**

---

## 2. 导出宏：接口可见性的总开关

`CudaTool.h` 顶部：

```cpp
#ifdef CUDA_EXTERN_DLL
#define DLL_EXPORT __declspec(dllexport)  // 编【库工程】时
#else
#define DLL_EXPORT __declspec(dllimport)  // 编【调用方】时
#endif
```

| 工程 | 预处理器 | 宏展开为 |
|------|----------|----------|
| `CudaExtern`（本库） | 定义 `CUDA_EXTERN_DLL` | `dllexport`：把符号写进 DLL |
| 外部业务工程 | **不**定义该宏 | `dllimport`：从 DLL 导入符号 |

库工程里要在两处都带上该宏（否则 `.cu` 可能仍按 import 编译）：

- **C/C++ → 预处理器**：`CUDA_EXTERN_DLL`
- **CUDA C/C++ → Host 预处理器定义**：`CUDA_EXTERN_DLL`

本库 `vcxproj` 已在 Debug/Release 同步配置。

---

## 3. 如何设置接口（三类导出）

### 3.1 类整体导出

```cpp
class DLL_EXPORT CudaTool
{
    // ...
    void CheckCudaStatus(cudaError_t status, const char* msg);  // 非模板：实现在 .cpp
    template<typename T>
    void LaunchBinaryKernel(...);  // 模板：实现必须在 .h
};
```

- `DLL_EXPORT` 标在 **class** 上：非模板成员（如 `CheckCudaStatus`）会进入导出表  
- 实现写在 `CudaTool.cpp`，随 DLL 一起编译  

### 3.2 模板成员：实现放头文件

模板成员在**用到的那份 .cpp** 里才会实例化。若实现只放在库的 `.cpp`，调用方一调用就会 **LNK2019**。

约定：

```cpp
// 声明在类里
template<typename T>
void LaunchBinaryKernel(T* src, T* dst, size_t width, size_t height, T threshold);

// 定义紧跟在 .h 里（inline）
template<typename T>
inline void CudaTool::LaunchBinaryKernel(...)
{
    // cudaMalloc / copy / 调用 LaunchBinaryKernelImpl / cudaFree
}
```

这类接口负责“业务编排”，**不**直接写 `<<<>>>`。

### 3.3 GPU 启动函数：声明在 .h，定义+实例化在 .cu

```cpp
// CudaTool.h —— 仅声明，并带 DLL_EXPORT
template <typename T>
DLL_EXPORT void LaunchBinaryKernelImpl(T* d_in, T* d_out,
    size_t width, size_t height, T threshold);
```

```cpp
// kernel.cu —— 定义模板 + 启动 kernel
template <typename T>
void LaunchBinaryKernelImpl(T* d_in, T* d_out, size_t width, size_t height, T threshold)
{
    dim3 block(16, 16);
    dim3 grid((width + block.x - 1) / block.x, (height + block.y - 1) / block.y);
    BinaryKernel<<<grid, block>>>(d_in, d_out, width, height, threshold);
}
```

`<<<>>>` 只能出现在 `.cu`（由 nvcc 编译）。  
**仅有上面的模板定义还不够导出可用符号**——见下一节。

---

## 4. 模板显式实例化（跨 DLL 的关键）

### 4.1 为什么必须显式实例化

| 步骤 | 没有显式实例化时会发生什么 |
|------|---------------------------|
| 库工程编译 `.cu` | 只有模板**定义**，编译器不会为某个 `T` 真正生成函数体（没有人在该 .cu 里“用到”它） |
| 调用方 `#include` 后调用 | 需要链接 `LaunchBinaryKernelImpl<unsigned char>` |
| 链接 | **LNK2019：无法解析的外部符号** |

显式实例化的作用：在库工程里**强制**为某个 `T` 生成函数，并 `dllexport` 出去。

### 4.2 写法（本工程现用）

在 `kernel.cu` 模板定义**之后**追加：

```cpp
// 二值化：导出 unsigned char 特化
template DLL_EXPORT void LaunchBinaryKernelImpl<unsigned char>(
    unsigned char* d_in, unsigned char* d_out,
    size_t width, size_t height, unsigned char threshold);

// 双峰阈值：同样只导出 8bit
template DLL_EXPORT void LaunchHistsholdKernelImpl<unsigned char>(
    unsigned char* d_in, unsigned char* d_outThresh,
    size_t width, size_t height);
```

要点：

1. 语法是：`template` + 返回值/修饰 + 函数名 + `<具体类型>` + 形参列表  
2. `DLL_EXPORT` 要带上，保证进 DLL 导出表  
3. `<unsigned char>` 与头文件声明的形参类型必须一致  
4. **每支持一种像素类型，就加一行实例化**（如再支持 `float`，再写一条 `<float>`）

### 4.3 与“头文件里的模板成员”如何配合

```text
调用方编译 LaunchBinaryKernel<unsigned char>
    └─ 内联代码调用 LaunchBinaryKernelImpl(...)
         └─ 链接器到 CudaTool.dll 中查找
              LaunchBinaryKernelImpl<unsigned char>   ← 来自显式实例化
```

- `.h` 里的模板成员：在调用方实例化（可对任意 `T` 编译通过内存与拷贝逻辑）  
- `.cu` 里显式实例化：决定 **GPU 路径实际支持哪些 T**  
- 若调用方用了未实例化的类型（如 `float`），会在链接阶段失败——这是预期行为  

本库直方图路径还用 `static_assert(sizeof(T) == 1, ...)` 限制为 8bit。

### 4.4 `__global__` 要不要导出？

一般**不需要**。

- `__global__ BinaryKernel`：仅被同编译单元的 `Launch*Impl` 启动  
- 导出的是主机侧的 `Launch*Impl`，而不是 kernel 符号本身  

---

## 5. 推荐的接口落地清单（做新算法时照抄）

按顺序做：

1. **在 `CudaTool.h` 声明导出启动函数**  
   `template<typename T> DLL_EXPORT void LaunchXxxImpl(...);`

2. **在 `CudaTool` 类里加对外接口**（可选模板成员）  
   `void LaunchXxx(...)` / `template<typename T> void LaunchXxx(...)`

3. **模板成员实现写在 `.h`**：分配显存、调 `LaunchXxxImpl`、同步、回读、释放  

4. **在 `kernel.cu`**：  
   - 写 `__global__` kernel  
   - 写 `template<typename T> void LaunchXxxImpl(...)`（内部 `<<<>>>`）  
   - **追加** `template DLL_EXPORT void LaunchXxxImpl<YourType>(...);`

5. **库工程确认**已定义 `CUDA_EXTERN_DLL`（C++ 与 CUDA Host 两侧）  

6. Rebuild 库；用 `dumpbin /EXPORTS CudaTool.dll`（可选）核对是否出现实例化后的导出名  

### 本库已提供的接口对应关系

| 对外接口（`.h` 成员） | 导出实现（`.cu`） | 已实例化类型 |
|----------------------|-------------------|--------------|
| `LaunchBinaryKernel` | `LaunchBinaryKernelImpl` | `unsigned char` |
| `LaunchHistsholdKernel` | `LaunchHistsholdKernelImpl` | `unsigned char` |
| `CheckCudaStatus` | `CudaTool.cpp`（非模板） | — |
| `copyHostToDevice` / `copyDeviceToHost` | 仅头文件模板 | 由调用方实例化 |

---

## 6. 设计上易错点

| 错误做法 | 结果 | 正确做法 |
|----------|------|----------|
| 模板 `Launch*Impl` 只定义、不显式实例化 | LNK2019 | `.cu` 末尾写 `template DLL_EXPORT void ...<T>(...)` |
| 实例化写在 `.cpp`（非 nvcc）且内含 `<<<>>>` | 无法编译 | 含 kernel 启动的定义必须放 `.cu` |
| 类导出了，但启动函数声明没有 `DLL_EXPORT` | 链接不到 Impl | 头文件声明也要 `DLL_EXPORT` |
| 只给 ClCompile 加了 `CUDA_EXTERN_DLL` | `.cu` 可能按 dllimport 编 | Host 预处理器同步定义 |
| 想支持 `float` 却只实例化了 `unsigned char` | 链接失败 | 增加一行 `<float>` 实例化 |
| 把 `__global__` 也标 `dllexport` | 无必要、易乱 | 只导出主机 `Launch*Impl` |

---

## 7. 最小记忆版

1. **接口**：类用 `DLL_EXPORT`；编排逻辑可做模板并放在 `.h`；真正启动 GPU 的函数声明为 `DLL_EXPORT` 模板，定义在 `.cu`。  
2. **实例化**：在 `.cu` 里对每个支持的 `T` 写一行  
   `template DLL_EXPORT void LaunchXxxImpl<T>(...);`  
3. **宏**：编库定义 `CUDA_EXTERN_DLL`，调用方不定义。  

源码对照：`CudaExtern/CudaTool.h`、`CudaExtern/kernel.cu`。
