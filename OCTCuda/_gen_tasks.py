# -*- coding: utf-8 -*-
"""Generate Week/Day TASK.md files for OCTCuda curriculum."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def T(goal, reads, apis, how, hands, refs, dod, nxt):
    return dict(goal=goal, reads=reads, apis=apis, how=how, hands=hands, refs=refs, dod=dod, nxt=nxt)


weeks = {}

weeks[1] = {
    1: T(
        "建立 OCTCuda 学习上下文：弄清「无 .cu 源码」与「API+宿主」边界，搭好笔记与术语表。",
        [
            "OCTCuda/README.md",
            "OCTCuda/00_全局规划.md",
            "Algorithm/vgpu/include/VGPU_Process.cuh（浏览 #pragma region 与函数名列表）",
            "ProjectP60_1.5/IS05.vcxproj 中搜索 cudart / cufft / VGPU_Process",
        ],
        ["全文件 region 目录建立（本日不深入单 API）"],
        "列出每个 region 下函数名表到 notes/W01_api_index.md。"
        "标注类别：成像主干 / 校准检测 / 批处理 / IPA。"
        "建立认知：内核在闭源 DLL，本仓是 API + 宿主编排。",
        [
            "创建 OCTCuda/notes/ 目录",
            "一页纸：公司仓 vs 未来开源仓职责对比",
            "确认本机 CUDA Toolkit / GPU，写入笔记",
        ],
        ["01_API接口全解.md §0", "CUDA C++ Programming Guide 第 1 章"],
        [
            "能口述：为何简历不能只写「调用过 VGPU_Process」",
            "已有 region 函数名索引",
            "已记录本机 CUDA 环境",
        ],
        "精读 Allocate / Free / Memory / Status 等生命周期 API",
    ),
    2: T(
        "精读显存生命周期 API，理解管线「先分配再算」模型。",
        [
            "VGPU_Process.cuh → #pragma region 参数配置与显存分配",
            "ImageProcessingController.cpp 中 Allocate / Free / SetFunctionConfig / SetCalibrationData 调用处",
        ],
        [
            "VGPU_Allocate_Parameter_Manager",
            "VGPU_Free_Parament_Manager",
            "VGPU_SetFunctionConfig",
            "VGPU_SetCalibrationData",
        ],
        "Allocate：按 PIU 转速、scan/pullback 线数、每线点数、圆图尺寸、回拉帧数、标定表，预分配 device 缓冲与 FFT plan（推断）。\n"
        "SetFunctionConfig：去 DC/底噪开关。\n"
        "SetCalibrationData：标定表 H2D。\n"
        "Free：成对释放；注意 isfree_CalibrationConfig。\n"
        "开源实现：class PipelineContext { init(shape); shutdown(); }。",
        [
            "笔记画出 Allocate 参数 → 假想缓冲列表（raw/windowed/fft/rect/circle/color）",
            "记录宿主实际传入的尺寸相关全局变量名",
        ],
        ["01_API接口全解.md §1", "cudaMalloc / cudaFree / cudaMemcpy"],
        [
            "写出不少于 6 类 device buffer 的估算公式",
            "能解释回拉帧数为何进入 Allocate",
        ],
        "错误状态、显存查询、Reallocate / Reset",
    ),
    3: T(
        "掌握 CUDA 健康监控与「DL 后重建显存」语义。",
        [
            "VGPU_GetCudaErrorStatus / GetCurrentGPUMemory / ResetCudaMemory / Reallocate_memory 声明",
            "MainWindowView.cpp 搜索 VGPU_GetCuda / Memory / Reset",
            "IPAAlgorithmController.cpp 中显存日志包装调用",
        ],
        [
            "VGPU_GetCudaErrorStatus",
            "VGPU_GetCurrentGPUMemory",
            "VGPU_ResetCudaMemory",
            "VGPU_Reallocate_memory",
        ],
        "GetCudaErrorStatus ← 错误探测；GetCurrentGPUMemory ← cudaMemGetInfo；\n"
        "Reset ← 设备复位后必须重新 Allocate；Reallocate ← 分析/DL 占用后恢复成像缓冲。\n"
        "开源：check(err)、vram_snapshot()、safe_reinit()。",
        [
            "写决策树：何时 Reset vs 仅 Reallocate",
            "在开源草稿实现 cuda_utils.hpp（可先桩实现）",
        ],
        ["CUDA Error Handling 文档/最佳实践"],
        [
            "能讲清 MainWindow 保护与 IPA 前后打显存日志的原因",
            "notes 中有决策树",
        ],
        "搭建开源仓 CMake 骨架",
    ),
    4: T(
        "创建与 AIOCT 隔离的 oct-cuda-pipeline 骨架，对齐模块映射表。",
        ["01_API接口全解.md §8 开源模块映射", "00_全局规划.md §6 实现优先级"],
        ["oct::Context ↔ Allocate/Free/Memory（映射）"],
        "CMake 启用 CUDA 语言；目录 kernels/ host/ tests/ bench/；\n"
        "先实现 Context 空壳：init/shutdown/mem_info。",
        [
            "在 AIOCT 外或 OCTCuda/playground/oct-cuda-pipeline 创建工程",
            "README 含合规声明 + 模块列表",
            "空 main 编译通过",
        ],
        ["CMake CUDA 官方示例", "CUDA Compilation Guide"],
        ["工程可配置可编译", "README 含合规段", "模块名与 §8 对齐"],
        "吃透 DOCMotionType 与 is_device_to_host；写 W01 REVIEW",
    ),
    5: T(
        "吃透 DOCMotionType 与 is_device_to_host；完成 Week01 复盘。",
        [
            "VGPU_Process.cuh 枚举 DOCMotionType",
            "ImageProcessingController 中 status 与 true/false 传参（至少统计 10 处）",
            "02_数据流与调用链.md 链 A",
        ],
        ["DOCMotionType", "is_device_to_host"],
        "SCAN vs PULLBACK_* 切换不同 device 指针/尺寸。\n"
        "实时主路径中间阶段 is_device_to_host=false，最后显示再 D2H。\n"
        "开源：CopyPolicy + PipelinePhase。",
        [
            "撰写 Week01/REVIEW.md（API 列表、尺寸笔记、三个疑问）",
            "更新 03_进度追踪.md",
            "可选：5 分钟口述显存生命周期",
        ],
        ["02_数据流与调用链.md"],
        ["REVIEW.md 已写", "能默述链 A 前三步", "开源仓出现 CopyPolicy"],
        "进入 Week02：重采样与窗函数",
    ),
}

weeks[2] = {
    1: T(
        "理解原始光谱 → 重采样加窗的物理与工程动机。",
        [
            "VGPU_Data_Resampling_For_Scan / _Vivo / _For_Pullback 声明",
            "Algorithm/vgpu/include/windata.h（窗系数表用途）",
            "ImageProcessingController 中 Resampling 调用上下文",
        ],
        [
            "VGPU_Data_Resampling_For_Scan",
            "VGPU_Data_Resampling_For_Scan_Vivo",
            "VGPU_Data_Resampling_For_Pullback",
        ],
        "SD-OCT 需在均匀波数网格上 FFT；窗抑制旁瓣。\n"
        "Vivo：U8 + gain/offset 转浮点。Pullback：多帧入口。\n"
        "实现：标定表引导插值 + 乘窗（Hann 等）。",
        [
            "笔记：U16 vs U8 输入差异表",
            "CPU/Python 生成 Hann 并可视化",
        ],
        ["公开 SD-OCT k-linearization 综述摘要", "01_API接口全解.md §2 Resampling"],
        ["能解释 FFT 前为何重采样+加窗", "Hann 数组可复现"],
        "实现 CPU 黄金版 resample+window",
    ),
    2: T(
        "实现 CPU 版重采样 + Hann（合成数据）。",
        ["WinType 枚举", "SetCalibrationData 与 Resampling 关系"],
        ["VGPU_SetCalibrationData", "VGPU_Data_Resampling_For_Scan"],
        "简化假设线性映射；每 A-line 插值到 N 点后乘 Hann；输出 float。",
        ["oct-cuda-pipeline: cpu_resample_window + 固定种子合成 chirp 单测"],
        ["线性插值数值方法"],
        ["CPU 输出稳定可测", "测试锁定"],
        "CUDA naive window kernel",
    ),
    3: T(
        "CUDA：每线程一采样点乘窗；标定插值可先简化为 identity。",
        ["BLOCK_DIM = 256"],
        ["VGPU_Data_Resampling_For_Scan"],
        "__global__ apply_window；grid-stride；窗放 constant 或只读缓冲；与 CPU 比误差。",
        ["实现 kernel + H2D/D2H", "max abs error 报告"],
        ["CUDA Best Practices — coalescing"],
        ["误差达标（如 1e-5）"],
        "Vivo 与 Pullback 重采样分支",
    ),
    4: T(
        "对照 Vivo / Pullback 重采样 API，补全开源分支。",
        ["ImageProcessingController 中 _Vivo 与 Pullback 相关分支"],
        ["VGPU_Data_Resampling_For_Scan_Vivo", "VGPU_Data_Resampling_For_Pullback"],
        "Vivo 先 scale；Pullback 带 frame_sum。开源 InputKind { U16, U8Vivo }。",
        ["扩展 resample(InputKind,...)", "宿主选分支笔记"],
        ["02 链 A/B"],
        ["分支表写入 notes", "代码含 U8 路径"],
        "W02 profile + REVIEW",
    ),
    5: T(
        "Profile 窗核；写 REVIEW；预习 cuFFT。",
        ["vcxproj 中 cufft 链接", "01 §2 FFT 预览"],
        ["（预备）VGPU_Get_FFT_Power_Result"],
        "用 cudaEvent 或 nsys 测 window；记录粗性能。",
        ["Week02/REVIEW.md", "性能一行表", "预习 cuFFT PlanMany"],
        ["cuFFT 用户指南 — PlanMany"],
        ["REVIEW 完成", "理解 batch=线数 的含义"],
        "Week03 FFT / Log",
    ),
}

weeks[3] = {
    1: T(
        "精读 FFT 功率与插值两套 API，画出与 Resampling 的衔接。",
        [
            "VGPU_Get_FFT_Power_Result / Interpolation_Result",
            "ImageProcessingController 中紧接 Resampling 的调用",
        ],
        ["VGPU_Get_FFT_Power_Result", "VGPU_Get_FFT_Power_Interpolation_Result"],
        "加窗实数 → R2C FFT → 功率 → log/缩放；Interpolation 输出 U16；ground_noise 去底。\n"
        "plan 应在 Allocate 创建并复用。",
        ["笔记：windowed → complex → logpower 缓冲图", "记录 is_device_to_host 取值"],
        ["01 §2 FFT", "cuFFT R2C"],
        ["IO 图完成", "能解释两 API 差异"],
        "实现 cuFFT stage",
    ),
    2: T(
        "开源实现 FftLogStage：PlanMany + Exec + log_power kernel。",
        ["ComplexData 结构体"],
        ["VGPU_Get_FFT_Power_Result"],
        "cufftPlanMany(batch=n_alines)；log_power kernel；默认 KeepDevice。",
        ["代码实现", "与小 N CPU DFT/第三方 FFT 对照"],
        ["cuFFT 文档"],
        ["batch FFT 跑通", "小尺寸误差可接受"],
        "U16 压缩与 Current_Frame 取出",
    ),
    3: T(
        "精读存储与取出 API：当前帧 FFT、U16↔F32、After_Log。",
        [
            "Get_Current_Frame_FFT_data*",
            "Get_After_Log_Result",
            "U16fft↔F32fft 两个 Result API",
            "GpuHandlingDataThreadController 中相关调用",
        ],
        [
            "VGPU_Get_Current_Frame_FFT_data",
            "VGPU_Get_Current_Frame_FFT_After_Interpolation_data",
            "VGPU_Get_After_Log_Result",
            "VGPU_Get_U16fft_data_toF32fft_Result",
            "VGPU_Get_F32fft_data_toU16fft_Result",
        ],
        "计算用 F32，存盘用 U16；拍照 D2H 当前帧。开源：量化 scale 写入元数据。",
        ["实现 quantize_u16 / dequantize", "笔记：宿主何时必须 D2H"],
        ["02 链 C"],
        ["量化往返误差表", "理解存盘路径"],
        "旧数据兼容 API",
    ),
    4: T(
        "读懂旧记录 Log 逆变换与 cutfront25；写兼容层设计。",
        [
            "VGPU_Get_old_data_toLog_Result",
            "VGPU_Get_old_data_cutfront25_Result",
            "VGPU_Get_Denoising_data_toLog_Result",
            "GpuHandlingDataThreadController 导入分支",
        ],
        [
            "VGPU_Get_old_data_toLog_Result",
            "VGPU_Get_old_data_cutfront25_Result",
            "VGPU_Get_Denoising_data_toLog_Result",
        ],
        "历史格式兼容：已 Log / 未裁前 25 点 / denoising→Log。实现：逐元素核 + width 维 offset。",
        ["notes/W03_legacy_log.md 设计文档", "可选实现 cut_front(n)"],
        ["02 链 C"],
        ["说清旧数据与新 denoising 差异"],
        "对照 Pullback_ProcessData_ToImage；写 W03 REVIEW",
    ),
    5: T(
        "对照回拉单帧捷径 API；复盘 FFT 周。",
        ["VGPU_Pullback_ProcessData_ToImage", "ImageProcessingController 回拉循环"],
        ["VGPU_Pullback_ProcessData_ToImage"],
        "等价于多阶段融合入口；开源可先顺序调用已有 stage 模拟。",
        ["Week03/REVIEW.md", "e2e: window→fft→log", "cudaEvent 计时"],
        ["01 §2"],
        ["REVIEW + 计时表", "融合 API 语义清楚"],
        "Week04 Transpose / DSC",
    ),
}

weeks[4] = {
    1: T(
        "精读 Transpose 与深度裁剪；联系导管校准 cut。",
        ["VGPU_Transpose / Transpose_CheckImage", "ImageProcessingController 中 start/end 来源"],
        ["VGPU_Transpose", "VGPU_Transpose_CheckImage"],
        "转置为显示方图布局并裁掉导管内无效深度。[start,end) 常由校准给出。\n"
        "实现：shared-memory tile transpose + 行范围裁剪。",
        ["CPU transpose+crop", "CheckImage 用途笔记"],
        ["CUDA tile transpose 经典文章"],
        ["CPU 版正确", "cut 与校准关系写明"],
        "CUDA tile transpose",
    ),
    2: T(
        "实现 shared-memory tile transpose（含 bank conflict padding）。",
        ["BLOCK_DIM / WARPSIZE"],
        ["VGPU_Transpose"],
        "tile 16x16 或 32x32；__shared__ tile[TILE][TILE+1]；与 CPU 比对。",
        ["kernel + 测试", "bank conflict 笔记"],
        ["CUDA Best Practices — shared memory"],
        ["GPU 与 CPU 一致", "笔记含 padding 原因"],
        "DSC API 精读",
    ),
    3: T(
        "精读 DSC 全部参数；推导极→直公式。",
        ["VGPU_DSC 声明", "InterpolateType", "ImageProcessingController DSC 调用"],
        ["VGPU_DSC"],
        "圆图像素 (x,y)→(r,θ)→在极坐标 rect 上插值。inner_r/margin_r 控制有效环带。\n"
        "插值：最近邻 / 双线性 / 三次。",
        ["手推公式写入 notes", "CPU 最近邻 DSC 出图"],
        ["scan conversion 公开资料"],
        ["公式 + CPU 最近邻结果图"],
        "双线性 DSC CPU + CUDA",
    ),
    4: T(
        "实现双线性 DSC：CPU 黄金版 + CUDA naive（全局内存）。",
        ["VGPU_DSC"],
        ["VGPU_DSC"],
        "每像素一线程；atan2+sqrt；双线性；越界写 0。",
        ["dsc_bilinear.cu", "与 CPU 误差报告"],
        ["01 §2 DSC"],
        ["CUDA 出圆图", "误差报告"],
        "texture 优化尝试 + W04 REVIEW",
    ),
    5: T(
        "DSC texture 优化尝试；Week04 复盘。",
        ["cudaTextureObject 文档"],
        ["VGPU_DSC"],
        "rect 绑定 texture；对比 v1/v2 耗时与 Nsight 内存指标。",
        ["Week04/REVIEW.md", "性能对比表"],
        ["Nsight Compute 内存指标"],
        ["至少有 v1 计时；v2 有结论（成功或阻塞原因）"],
        "Week05 增强与伪彩、e2e",
    ),
}

weeks[5] = {
    1: T(
        "精读灰度增强四种模式与宿主边界/gamma 参数。",
        ["VGPU_Image_Enhancement", "GrayEnhanceType", "ImageProcessingController 增强分支"],
        ["VGPU_Image_Enhancement"],
        "DSC float→显示灰度：Linear/Pow/Log/Exp；low/up_bound、pow_index。\n"
        "注意头文件中 is_device_to_host 类型为 int。",
        ["CPU 实现四种增强", "与宿主默认类型对照表"],
        ["display windowing / gamma"],
        ["四种可切换", "参数命名对照表"],
        "Gray2Color 伪彩",
    ),
    2: T(
        "精读并实现 Gray2Color；对照 goldenMapArray（勿外泄公司 LUT）。",
        [
            "VGPU_Gray2Color",
            "ColorsMapType",
            "goldenMapArray.h（只理解用途）",
            "ImageProcessingController Gray2Color(true)",
        ],
        ["VGPU_Gray2Color"],
        "constant LUT[256][3]；开源仓使用自造 palette，禁止复制公司表到公开仓。",
        ["kernel 输出 BGR/PNG", "合规自检"],
        ["01 §2 Gray2Color"],
        ["伪彩图可保存", "合规通过"],
        "Scan e2e 串联",
    ),
    3: T(
        "开源仓串联链 A 主干：Resample→FFT→Transpose→DSC→Enhance→Color。",
        ["02 链 A", "ImageProcessingController 单帧顺序"],
        ["链 A 全部主干 API"],
        "Host：run_scan_frame；中间 KeepDevice；最终 ToHost。",
        ["e2e demo + 合成 PNG", "每 stage cudaEvent"],
        ["00_全局规划.md §1"],
        ["结果图 + stage 耗时表"],
        "Power_aline 旁路 API",
    ),
    4: T(
        "精读光灵敏度功率 API（测试用途）。",
        ["VGPU_Data_Power_aline", "VGPU_Vivo_Data_Power_aline", "宿主调用点"],
        ["VGPU_Data_Power_aline", "VGPU_Vivo_Data_Power_aline"],
        "对 A-line 功率做统计；与主显示链独立。实现：reduction。",
        ["简单 reduce 或 thrust::reduce", "与 DSC 链关系笔记"],
        ["warp reduce 教程"],
        ["能说明为何独立于显示链"],
        "W05 REVIEW + 简历一句草稿",
    ),
    5: T(
        "复盘 e2e；写出可放简历的一句（数字可先占位）。",
        ["00_全局规划.md §4.3"],
        ["（综合）链 A"],
        "整理计时；REVIEW；简历句：fps/加速比占位。",
        ["Week05/REVIEW.md", "更新进度表", "列出 W06 API 预习列表"],
        ["02 链 B"],
        ["e2e 可演示", "简历句已写"],
        "Week06 回拉批处理",
    ),
}

weeks[6] = {
    1: T(
        "精读回拉显存检查与整卷上传 API。",
        [
            "VGPU_Check_pullback_Data_memory",
            "VGPU_Set_Original_pullback_Data_To_GPU",
            "GpuHandlingDataThreadController 回拉相关",
        ],
        ["VGPU_Check_pullback_Data_memory", "VGPU_Set_Original_pullback_Data_To_GPU"],
        "上传前检查 VRAM；U16 与 Vivo U8 双通道；按 frame 偏移写入 bulk buffer。\n"
        "实现：大块 H2D 或分块异步。",
        ["字节估算 frames*alines*points*sizeof", "开源 PullbackVolume::upload"],
        ["01 §5", "02 链 B"],
        ["估算与宿主帧数变量对应"],
        "Handle_All_Preview / Get_All_FFT",
    ),
    2: T(
        "精读全帧 FFT 生成与下载。",
        ["VGPU_Handle_All_Preview_data", "VGPU_Get_All_FFT_data", "宿主搜索调用"],
        ["VGPU_Handle_All_Preview_data", "VGPU_Get_All_FFT_data"],
        "设备上批处理全卷；下载 U16 FFT 供分析/IPA。",
        ["开源 batch_fft_volume", "KeepDevice 直至 Get"],
        ["cuFFT 扩展到多帧"],
        ["能口述链 B 中段"],
        "Handle_All_FFT / Calibration_Image",
    ),
    3: T(
        "精读 FFT→方图/圆图与校准裁剪批处理、对比度、单帧取图。",
        [
            "VGPU_Handle_All_FFT_data",
            "VGPU_Handle_All_Calibration_Image",
            "VGPU_CalculatedContrastRange",
            "VGPU_Hnad_One_Frame_Data",
        ],
        [
            "VGPU_Handle_All_FFT_data",
            "VGPU_Handle_All_Calibration_Image",
            "VGPU_CalculatedContrastRange",
            "VGPU_Hnad_One_Frame_Data",
        ],
        "复用 DSC/Enhancement；icut_start/size；自适应对比度；按帧取图（注意 API 拼写 Hnad）。",
        ["开源 render_volume_to_circles", "Calibration vs All_FFT 差异笔记"],
        ["01 §5"],
        ["差异表完成"],
        "Set_all_FFT / OneFrameRaw",
    ),
    4: T(
        "分析侧灌回 FFT 与单帧 Raw→图。",
        [
            "VGPU_Set_all_U16_FFT_data_to_Gpu",
            "VGPU_Set_all_FFT_data_to_Gpu",
            "VGPU_OneFrameRawData_To_Image",
            "IntegrationChannel 相关搜索",
        ],
        [
            "VGPU_Set_all_U16_FFT_data_to_Gpu",
            "VGPU_Set_all_FFT_data_to_Gpu",
            "VGPU_OneFrameRawData_To_Image",
        ],
        "分析改参时 Host 已有 FFT，需再 H2D。OneFrame 用于单帧预览。",
        ["开源 upload_fft_volume", "调用序笔记"],
        ["02 链 C"],
        ["说清「成像上传 Raw」vs「分析上传 FFT」"],
        "实现批处理骨架；W06 REVIEW",
    ),
    5: T(
        "开源实现小规模批处理（如 8 帧）；复盘 bulk vs 逐帧拷贝。",
        ["02 链 B"],
        ["链 B 核心 API"],
        "合成 8 帧 bulk→FFT→每帧 DSC；对比逐帧上传耗时。",
        ["Week06/REVIEW.md", "性能对比记录"],
        ["CUDA Streams 预习（Week13）"],
        ["bulk 路径可跑", "REVIEW 含对比"],
        "Week07 导管校准",
    ),
}

weeks[7] = {
    1: T(
        "精读校准枚举与 Catheter_AutoCalibration 主 API。",
        [
            "GPUCalibrationType / GPULightSourceType",
            "VGPU_Catheter_AutoCalibration",
            "ImageProcessingController 校准分支",
        ],
        ["VGPU_Catheter_AutoCalibration"],
        "连接校准 vs 术中自动；光源类型；新旧导管；输出校准数据/影响 cut。\n"
        "公开实现方向：方图径向寻峰估导管壁。",
        ["参数释义表", "画：校准如何改 Transpose start"],
        ["01 §3"],
        ["释义表完成", "与 cut 联动写清"],
        "旧 AutoCalibration_* 与 *_cs",
    ),
    2: T(
        "对照旧校准 API 与 cs 测试接口、CheckImageInfo。",
        [
            "VGPU_AutoCalibration_new / _connect / *_cs",
            "VGPU_CheckImageInfo",
            "宿主中注释掉的旧调用",
        ],
        [
            "VGPU_AutoCalibration_new",
            "VGPU_AutoCalibration_connect",
            "VGPU_AutoCalibration_new_cs",
            "VGPU_AutoCalibration_connect_cs",
            "VGPU_CheckImageInfo",
        ],
        "cs 接口直接吃 Host transpose，便于离线单测；CheckImageInfo：0 阈值 / 1 硬件。",
        ["新旧对照表", "设计开源 calib_from_transpose"],
        ["01 §3"],
        ["对照表完成"],
        "CPU 简化寻峰校准",
    ),
    3: T(
        "实现公开简化版导管壁检测（CPU），不追求产品数值一致。",
        ["宏 POSITION_* / VALUE_THRESHOLD 等"],
        ["（语义等价）VGPU_Catheter_AutoCalibration"],
        "每角度径向亮度峰 → 鲁棒中值 → cutHeight。",
        ["cpu_catheter_peak + 合成圆环测试"],
        ["径向 profile 方法"],
        ["合成环能检出近似半径"],
        "嵌入 e2e 的 auto_cut",
    ),
    4: T(
        "分析校准失败模式；e2e 增加 auto_cut 开关。",
        ["ImageProcessingController 成功/失败分支"],
        ["VGPU_Catheter_AutoCalibration", "VGPU_CheckImageInfo"],
        "失败可能是阈值或硬件；开源用开关切换手动/自动 cut。",
        ["e2e 接 auto_cut", "失败模式笔记"],
        ["02 链 A"],
        ["e2e 可切换 cut 来源"],
        "W07 REVIEW（方法公开 vs 阈值私有）",
    ),
    5: T(
        "复盘校准周；划清合规边界。",
        ["00_全局规划.md §7"],
        ["校准 region 全部 API"],
        "REVIEW：方法可公开，内部阈值不外泄。列出 W08 检测 API。",
        ["Week07/REVIEW.md"],
        ["00 §7"],
        ["合规边界清晰"],
        "Week08 造影剂 / 折断 / guiding",
    ),
}

weeks[8] = {
    1: T(
        "精读造影剂检测 Check5 与 Afd。",
        [
            "VGPU_Contrast_MediumCheck5",
            "VGPU_Contrast_MediumCheck_Afd",
            "宏 LINE_AVERAGE_GAP / PULL_BACK_THRESHOLD",
            "宿主搜索 Contrast_Medium",
        ],
        ["VGPU_Contrast_MediumCheck5", "VGPU_Contrast_MediumCheck_Afd"],
        "判断介质冲洗是否充分以允许回拉。公开版：环带亮度比例与 gap 统计；Afd 多阈值 + isSmoke。",
        ["参数释义笔记", "与回拉许可的状态关系笔记"],
        ["01 §4"],
        ["能口述检测目的与插入时机"],
        "导管折断检测",
    ),
    2: T(
        "精读 CheckCatheterBreakDetection。",
        ["VGPU_CheckCatheterBreakDetection", "ImageProcessingController 调用与 out_CheckImage"],
        ["VGPU_CheckCatheterBreakDetection"],
        "异常模式识别并输出检查图。开源：简化能量/结构异常特征。",
        ["假想特征列表", "可选 CPU 原型"],
        ["01 §4"],
        ["特征列表 + 链上插入点"],
        "guidingDetectOneFrame",
    ),
    3: T(
        "精读 guiding 检测 API。",
        ["VGPU_guidingDetectOneFrame", "宿主搜索 guidingDetect"],
        ["VGPU_guidingDetectOneFrame"],
        "窗口内平均像素序列；threshold/window/startRow/totalFrame。实现：滑动均值。",
        ["CPU sliding mean", "totalFrame 用法笔记"],
        ["01 §4"],
        ["伪代码完成"],
        "检测 hooks 总图",
    ),
    4: T(
        "画检测 API 插入链 A/B 总图；开源仅留 hooks 桩。",
        ["02 链 A/B", "本周三个 API"],
        ["Contrast_MediumCheck*", "CheckCatheterBreakDetection", "guidingDetectOneFrame"],
        "开源 Pipeline 增加 pre_dsc_checks() 空实现 + 日志。",
        ["notes/W08_detect_hooks.md", "代码 hooks"],
        ["00 学习策略"],
        ["总图完成"],
        "W08 REVIEW",
    ),
    5: T(
        "复盘检测周（不要求产品级精度）。",
        ["01 §4"],
        ["检测 region"],
        "REVIEW：目的、插入点、公开实现边界。",
        ["Week08/REVIEW.md"],
        [],
        ["插入点能默画"],
        "Week09 连续校准与管腔拼接",
    ),
}

weeks[9] = {
    1: T(
        "精读管腔拼接两个 API。",
        [
            "VGPU_Get_Lumen_Stitching_FFT_Image",
            "VGPU_Get_Lumen_Stitching_Denoising_Data",
            "头文件长注释",
            "宿主搜索 Lumen_Stitching",
        ],
        [
            "VGPU_Get_Lumen_Stitching_FFT_Image",
            "VGPU_Get_Lumen_Stitching_Denoising_Data",
        ],
        "远/近端按帧范围拼接；近端旋转角。实现：帧拷贝 + 圆周移位（角度滚动）。",
        ["IO 图", "CPU 滚动拼接原型"],
        ["01 §6"],
        ["旋转=圆周移位写清"],
        "GetContinuousCalibration",
    ),
    2: T(
        "精读 GetContinuousCalibration 与 machine_model。",
        [
            "VGPU_GetContinuousCalibration",
            "注释：0 冠脉 / 1 颈动脉 / 2 颅内",
            "宿主搜索 ContinuousCalibration",
        ],
        ["VGPU_GetContinuousCalibration"],
        "输出每帧 catheterCutStartHeight；机型参数不同。公开版：逐帧寻峰 + 时序平滑。",
        ["三机型差异笔记（仅宿主可见信息）", "int cuts[frames] 设计"],
        ["01 §6"],
        ["与单帧校准差异表"],
        "Continuous_* 出图 API",
    ),
    3: T(
        "精读 Continuous 出图 / 单帧更新 / 竞品入口。",
        [
            "VGPU_Continuous_Clibration_To_Circle_Image",
            "VGPU_Get_All_Continuous_Calibration_Image",
            "VGPU_Update_Frame_Continuous_Calibration_Image",
            "VGPU_C7C8_Get_All_Continuous_Calibration_Image",
        ],
        [
            "VGPU_Continuous_Clibration_To_Circle_Image",
            "VGPU_Get_All_Continuous_Calibration_Image",
            "VGPU_Update_Frame_Continuous_Calibration_Image",
            "VGPU_C7C8_Get_All_Continuous_Calibration_Image",
        ],
        "icut_start 变为每帧数组；Update 只重算一帧；C7C8 为竞品数据入口。",
        ["开源 cuts[] 驱动 render", "竞品入口笔记"],
        ["02 数据流"],
        ["能解释为何需要 Update 单帧"],
        "开源多帧 cut + 拼接 demo",
    ),
    4: T(
        "开源：多帧不同 cut 渲染 + 两段拼接 demo。",
        ["本周 API"],
        ["Stitching + Continuous_*"],
        "3 帧不同 cut；2 段 rolling stitch。",
        ["demo 出图", "简短文档"],
        [],
        ["demo 可运行"],
        "W09 REVIEW；预习 att_paras",
    ),
    5: T(
        "复盘几何类 API；预习 IPA。",
        ["01 §7 IPA 预览", "att_paras 结构体", "IPAAlgorithmController.cpp 填参段（约 56–180 行）"],
        ["（预习）att_paras"],
        "REVIEW + IPA 阅读计划。",
        ["Week09/REVIEW.md"],
        ["IPAAlgorithmController.cpp"],
        ["知道 P60/P80/C7 参数分支存在"],
        "Week10 IPA 理论与参数",
    ),
}

weeks[10] = {
    1: T(
        "建立 IPA 公开层面的物理/临床直觉。",
        [
            "公开检索：OCT intraplaque attenuation / lipid plaque attenuation coefficient（读摘要）",
            "VGPU_Process.cuh IPA region 注释",
        ],
        ["（概念）IPA"],
        "μ 反映组织光衰减；与脂质斑块分析相关。本计划目标是工程数据流与可公开复现估计器，不复制产品阈值。",
        ["notes/W10_ipa_physics.md（公开表述）"],
        ["公开综述摘要"],
        ["能用自己的话解释 IPA 功能"],
        "att_paras 逐字段对照宿主",
    ),
    2: T(
        "对照宿主填写 att_paras：P60 / P80 / C7；对比旧 SetConfig API。",
        [
            "IPAAlgorithmController.cpp IPAProcessing 填参（约 56–180 行）",
            "att_paras 定义",
            "08Code/.../IpaAlgorithmKernel.cuh",
        ],
        ["att_paras 全字段", "GUP_SetIpaalgorithmConfig（旧）"],
        "做三张配置表；step_success=ceil(stepsucc*minwin)。\n"
        "旧：先 SetConfig；新：Calculate 直接传 h_paras。",
        ["notes/W10_att_paras.md 三配置表", "新旧 API 差异"],
        ["01 §7", "IpaAlgorithmKernel.cuh"],
        ["三配置表完成", "新旧差异写明"],
        "Calculate 实参来源精读",
    ),
    3: T(
        "精读 VGPU_Calculate_Ipa_Result 每一次实参的来源与尺寸。",
        [
            "IPAAlgorithmController.cpp 中 VGPU_Calculate_Ipa_Result 调用",
            "reshaped_lumen / labels 从 DicomModel 拷贝",
            "media 常数 100",
            "GetGlobalFFTData",
        ],
        ["VGPU_Calculate_Ipa_Result"],
        "输入 FFT U16 卷；输出 miu 体 + line_ipa_miu（carpet）；\n"
        "lipid 阈值→in_ipa_11_mat_cof；isVivoData 影响噪声等行为。\n"
        "尺寸：depths=cols，theta=rows，alines=frames*theta。",
        ["绘制链 D 详细版（每指针尺寸）"],
        ["02 链 D"],
        ["尺寸公式与 GetGlobal* 对应无误"],
        "开源 μ 估计 SPEC",
    ),
    4: T(
        "设计开源 μ 估计规格（教学用），不宣称等于产品。",
        ["minwin / step_* / SNR 字段"],
        ["VGPU_Calculate_Ipa_Result（实现假设）"],
        "每 A-line：在 lumen 外深度窗对 log(I) 线性拟合得斜率≈μ；\n"
        "窗口搜索受 minwin/step 约束；labels 掩膜跳过无效线。",
        ["开源仓 oct::Ipa/SPEC.md", "CPU 伪代码"],
        ["最小二乘拟合"],
        ["SPEC 可供他人实现"],
        "W10 REVIEW",
    ),
    5: T(
        "复盘参数与规格；准备实现周。",
        ["W10 全部笔记"],
        ["att_paras", "VGPU_Calculate_Ipa_Result"],
        "REVIEW：字段、调用、SPEC。",
        ["Week10/REVIEW.md"],
        [],
        ["SPEC + 参数表 + 链 D 图齐全"],
        "Week11 CPU/CUDA 实现 μ",
    ),
}

weeks[11] = {
    1: T(
        "CPU 实现单 A-line μ 拟合；合成指数衰减验证。",
        ["开源 SPEC", "IPAAlgorithmController::ProcessingOneFrame 路径"],
        ["VGPU_Calculate_Ipa_Result"],
        "合成 I(z)=A*exp(-2μz)+noise；估计 μ 应接近真值。",
        ["cpu_aline_mu_test", "误差报告"],
        ["log(eps+I) 数值稳定"],
        ["合成数据相对误差可接受"],
        "扩展到一帧多线",
    ),
    2: T(
        "CPU 整帧/小卷 μ；简化 lumen/labels 掩膜。",
        ["宿主 lumen/labels 用法"],
        ["VGPU_Calculate_Ipa_Result 掩膜输入"],
        "仅在 lumen 外拟合；labels 跳过；media 简化为固定偏移。",
        ["cpu_volume_mu", "掩膜单测"],
        ["02 链 D"],
        ["掩膜生效"],
        "CUDA：一线一 block",
    ),
    3: T(
        "CUDA 实现 μ kernel 骨架。",
        ["BLOCK_DIM"],
        ["VGPU_Calculate_Ipa_Result"],
        "shared memory 载入一条 depth；block 内归约/拟合；写 out_mu。",
        ["ipa_mu.cu", "与 CPU 对比"],
        ["CUDA reduction"],
        ["小卷 GPU≈CPU"],
        "Mu → 圆图",
    ),
    4: T(
        "精读并实现 All_Aline_Mu_Data_To_Image（复用 DSC）。",
        [
            "VGPU_All_Aline_Mu_Data_To_Image",
            "IPAAlgorithmController 单帧/全卷调用",
        ],
        ["VGPU_All_Aline_Mu_Data_To_Image"],
        "把 μ 方图当强度做 DSC+量化；支持 icut_start 数组与 isVivoData。",
        ["复用 oct::Dsc 出 μ 圆图 PNG"],
        ["01 §7"],
        ["μ 圆图可出"],
        "理解 carpet / line_ipa_miu；W11 REVIEW",
    ),
    5: T(
        "理清 out_carpet_att 与 line_ipa_miu 后续用途；复盘。",
        ["Calculate 两路输出在宿主的保存位置", "pre_ipa_analysed_result"],
        ["VGPU_Calculate_Ipa_Result 输出"],
        "line μ 供 UpdateValueIPA；carpet 服务毯展。开源可先 line_mu = reduce(depth)。",
        ["Week11/REVIEW.md", "输出缓冲区字典"],
        ["预习 BackgroundIPA / IPAZone"],
        ["字典完成"],
        "Week12 UpdateValueIPA 与线程",
    ),
}

weeks[12] = {
    1: T(
        "精读 VGPU_UpdateValueIPA 全部参数与输出缓冲。",
        [
            "VGPU_UpdateValueIPA 头文件长注释",
            "BackgroundIPAUpdateThreadController 中调用",
            "IPAZoneController 中调用",
        ],
        ["VGPU_UpdateValueIPA"],
        "输入 InlineIPA；输出 IPA_L / RangeMean / IPA_A / IPA_T / colorbars；\n"
        "受 InThresholdT、Mode_ID、pixelSapcing、isVivolightIPA 控制。",
        ["参数→输出→UI 字段对照表"],
        ["01 §7 Update"],
        ["对照表完成"],
        "阈值变更完整数据流",
    ),
    2: T(
        "追踪「改阈值 → Update → UI」线程与信号。",
        [
            "BackgroundIPAUpdateThreadController.cpp",
            "UpdateIpaValueSignal 等相关信号",
            "后台退出/取消标志",
        ],
        ["VGPU_UpdateValueIPA", "VGPU_Calculate_Ipa_Result（对比轻重）"],
        "Calculate 重、Update 可反复；后台可取消。开源拆两阶段 API。",
        ["序列图 notes/W12_ipa_threads.md"],
        ["02 链 D"],
        ["序列图完成"],
        "开源简化 Update 实现",
    ),
    3: T(
        "开源实现简化 Update：阈值着色 + 帧聚合。",
        ["宿主对 IPA_T 尺寸的注释（如 1250*lines*3）"],
        ["VGPU_UpdateValueIPA"],
        "line_mu>thr 着色；按帧聚合→IPA_L；生成示意 colorbar。",
        ["ipa_update 模块 + 可视化"],
        [],
        ["改阈值能看到色图变化"],
        "IPA 与成像显存争用",
    ),
    4: T(
        "精读 IPA 前后显存监控及与成像缓冲共生问题。",
        [
            "IPAAlgorithmController 显存日志",
            "VGPU_Reallocate_memory 场景",
            "MainWindow CUDA 保护",
        ],
        ["VGPU_GetCurrentGPUMemory", "VGPU_Reallocate_memory"],
        "IPA 与实时成像争用 GPU；需监控与重建。开源：统一 Context 分配器。",
        ["争用与缓解笔记", "allocator 草图"],
        ["Week01 健康 API"],
        ["面试可讲清争用故事"],
        "写 15 分钟 IPA 口述稿；W12 REVIEW",
    ),
    5: T(
        "产出 IPA 口述稿并复盘 Week10–12。",
        ["W10–W12 笔记"],
        ["IPA region 三 API + 旧两 API"],
        "讲稿结构：物理→参数→Calculate→圆图→Update→线程。",
        ["Week12/REVIEW.md", "talk_ipa.md"],
        [],
        ["按讲稿自讲一遍无明显卡壳"],
        "Week13 GPU 线程与 Streams",
    ),
}

weeks[13] = {
    1: T(
        "精读 GpuHandlingDataThreadController 启动、循环、标志位。",
        [
            "GpuHandlingDataThreadController.cpp/.h",
            "is_need_gpu_processing",
            "CreateThread 与临界区",
        ],
        ["（宿主实时架构）"],
        "独立线程跑 GPU；标志触发；临界区保护共享状态。开源：std::thread + 队列。",
        ["线程状态图", "对齐链 A"],
        ["02 链 A"],
        ["状态图完成"],
        "与 ImageProcessingController 职责切分",
    ),
    2: T(
        "划分线程调度 vs 算法调用边界。",
        ["ImageProcessingController 对外方法", "GPU 线程调用哪些方法"],
        ["链 A 主干 API（复习）"],
        "线程类不写算法细节；Controller 封装 VGPU_*。开源同样分层。",
        ["重构：PipelineEngine + GpuWorker"],
        ["00 实现层目标"],
        ["分层清晰可指给面试官"],
        "CUDA Streams 双缓冲",
    ),
    3: T(
        "开源实现双缓冲 + cudaMemcpyAsync + stream 上计算。",
        ["CUDA Streams 文档"],
        ["（对应）少拷贝管线 + 并行拷贝计算"],
        "H2D async → kernels → 可选 D2H；双缓冲。用 Nsight Systems 看重叠。",
        ["bench 对比默认流", "文档化结果"],
        ["Nsight Systems"],
        ["有重叠证据或写清未重叠原因"],
        "实现开源状态机",
    ),
    4: T(
        "实现 02 中的状态机并断言非法 API 顺序。",
        ["02_数据流与调用链.md 开源状态机"],
        ["Allocate/Free 等生命周期 API"],
        "Idle→Allocated→Streaming→…→Freed；错误顺序抛异常。",
        ["代码 + 单测"],
        [],
        ["非法序测试覆盖"],
        "W13 REVIEW：线程 vs stream 答题要点",
    ),
    5: T(
        "复盘架构周；准备广度周。",
        ["Week13 产出"],
        ["架构相关"],
        "REVIEW + 面试题：专用 GPU 线程与 CUDA stream 如何分工。",
        ["Week13/REVIEW.md", "答题要点半页+"],
        [],
        ["答题要点完成"],
        "Week14 竞品 / NVAPI / VTK",
    ),
}

weeks[14] = {
    1: T(
        "精读竞品与导入类 API，做入口格式对照表。",
        [
            "VGPU_PullbackRawData_To_FFT_Data",
            "VGPU_C7C8_PullbackFFT_Data_To_Image",
            "VGPU_PullbackDcm_Data_To_Image",
            "VGPU_PullbackRawData_To_Image",
            "ImportationExportationController 搜索 VGPU_",
        ],
        [
            "VGPU_PullbackRawData_To_FFT_Data",
            "VGPU_C7C8_PullbackFFT_Data_To_Image",
            "VGPU_PullbackDcm_Data_To_Image",
            "VGPU_PullbackRawData_To_Image",
        ],
        "入口格式不同，后方汇合到方图/圆图核。开源：ImportAdapter。",
        ["notes/W14_import_matrix.md"],
        ["01 §5", "02 链 C"],
        ["对照表完成"],
        "缩略图 / 导出路径抽样",
    ),
    2: T(
        "抽样 RecordingThumbnail 与导出中的 GPU 调用子集。",
        [
            "RecordingThumbnailView.cpp 搜索 VGPU_",
            "ImportationExportationController.cpp 搜索 VGPU_",
        ],
        ["OneFrame / Handle 系列（实际出现的子集）"],
        "缩略图与导出复用同一 DLL 能力。整理调用子集列表。",
        ["调用子集列表笔记"],
        [],
        ["列表完成"],
        "NVAPI 温度与显示",
    ),
    3: T(
        "阅读 NVAPI 温度与多屏配置（广度，非 compute 核心）。",
        ["GpuController.cpp/.h", "GPUDisplayConfigController.cpp/.h（摘要）"],
        ["（NVAPI，非 VGPU）"],
        "工位显示与温度监控；与成像 compute 分离。开源不必复现。",
        ["notes/W14_nvapi.md（约 10–20 行说明即可）"],
        ["NVAPI 文档目录"],
        ["能区分 compute vs display 控制"],
        "VTK GPU Volume",
    ),
    4: T(
        "阅读 ThreeDimensionsImageController 中 VTK GPU 体绘制。",
        ["ThreeDimensionsImageController 搜索 GPUVolume / vtk"],
        ["vtkGPUVolumeRayCastMapper（VTK）"],
        "3D 走 VTK/OpenGL，与 VGPU 重建分离。加分：了解 CUDA–GL interop 概念。",
        ["notes/W14_vtk.md"],
        ["VTK GPU volume 概述"],
        ["能说出与 VGPU 边界"],
        "W14 REVIEW + P0 缺口列表",
    ),
    5: T(
        "广度周复盘；列出作品集必须补齐的 P0 缺口。",
        ["00_全局规划.md §6 P0/P1/P2"],
        ["全部 region 回顾"],
        "REVIEW + gap list → Week15 消灭。",
        ["Week14/REVIEW.md", "gap list"],
        [],
        ["gap list 明确可执行"],
        "Week15 作品集打磨",
    ),
}

weeks[15] = {
    1: T(
        "消灭 P0 缺口；补测试与 README 架构图（脱敏）。",
        ["开源仓现状", "00 §8 验收清单"],
        ["P0 模块对应的 VGPU 能力"],
        "补齐缺失 stage；README 画链 A（不出现需保密的内部名亦可）。",
        ["本地提交整理", "架构图"],
        ["00 §8"],
        ["P0 无红项或仅剩书面延期说明"],
        "正式性能表",
    ),
    2: T(
        "跑完整计时/Nsight，形成可放简历的性能表。",
        ["bench 程序"],
        ["e2e 管线"],
        "表含：stage ms、fps、CPU 对比、DSC v1/v2。",
        ["docs/perf.md", "原始结果文件归档"],
        ["Nsight 用户指南"],
        ["perf.md 达到可引用质量"],
        "精度报告",
    ),
    3: T(
        "撰写 precision.md：各 stage 误差与合成数据局限。",
        ["tests 结果"],
        ["各实现模块"],
        "误差表 + 方法论诚实说明。",
        ["docs/precision.md"],
        [],
        ["误差表完整"],
        "IPA 子文档打磨",
    ),
    4: T(
        "打磨 IPA 子 README：跑法、参数、免责声明。",
        ["Week10–12 产出"],
        ["IPA 三 API 语义"],
        "强调教学用估计器，不等于医疗产品算法。",
        ["oct::Ipa 文档", "合规复查"],
        ["00 §7"],
        ["免责声明 + 可运行说明"],
        "作品集自检；W15 REVIEW",
    ),
    5: T(
        "作品集自检清单全过；准备简历数字。",
        ["00 §8"],
        ["综合能力"],
        "自检：编译/测试/perf/precision/合规/演示脚本。",
        ["Week15/REVIEW.md", "一键 demo 脚本"],
        [],
        ["自检通过或残留 issue 列表化"],
        "Week16 求职闭环",
    ),
}

weeks[16] = {
    1: T(
        "写简历 GPU 相关 bullet（4–6 条）与开源项目段。",
        ["00 §4.3", "docs/perf.md 数字"],
        ["链 A/B/D 对应能力表述"],
        "公司经历脱敏；项目段链到开源仓；每条含技术词+数字。",
        ["resume_gpu_draft.md"],
        ["对照 2 份真实 CUDA/成像 JD 关键词"],
        ["草稿完成"],
        "面试题库",
    ),
    2: T(
        "整理面试题库并自答：CUDA 基础 + 管线架构 + IPA。",
        ["W04 DSC 笔记", "W13 线程 vs stream", "W12 IPA 讲稿"],
        ["高频 API 口述清单"],
        "不少于 15 题，含要点答案。",
        ["notes/interview_qna.md"],
        ["00 §4.2"],
        ["题库完成"],
        "白板手写练习",
    ),
    3: T(
        "限时手写：tile transpose、reduction、DSC 伪代码。",
        ["W04 / W11 kernels"],
        ["Transpose / DSC / μ"],
        "每题 30–45 分钟，模拟白板。",
        ["notes/whiteboard/ 存文本或照片说明"],
        [],
        ["三题均能写完"],
        "投递名单",
    ),
    4: T(
        "制定投递名单并按 JD 匹配主打故事（成像 / IPA / 系统）。",
        ["简历草稿"],
        ["能力→岗位映射"],
        "医疗影像、工业检测、半导体 AOI、机器人视觉、NVIDIA 相关组等。",
        ["apply_list.md（≥15 家/方向）"],
        [],
        ["每家有主打故事标签"],
        "16 周总复盘",
    ),
    5: T(
        "总复盘：对 VGPU_Process.cuh 各 region 自评覆盖率；订复习计划。",
        ["01_API接口全解.md 全文", "03_进度追踪.md"],
        ["VGPU_Process.cuh 全部导出符号"],
        "每 region 自评 1–5 分；低于 4 安排复习日。",
        ["Week16/REVIEW.md", "maintenance_plan.md"],
        ["00 §8"],
        ["覆盖率表完成", "进入可持续复习 + 投递"],
        "计划完成后：按 maintenance 执行并开始投递",
    ),
}


def render(week, day, t):
    lines = []
    lines.append(f"# Week {week:02d} / Day {day:02d} — 任务说明")
    lines.append("")
    lines.append("## 今日目标")
    lines.append("")
    lines.append(t["goal"])
    lines.append("")
    lines.append("## 必读代码 / 文档")
    lines.append("")
    for x in t["reads"]:
        lines.append(f"- {x}")
    lines.append("")
    lines.append("## API 精读（功能 → 如何实现）")
    lines.append("")
    lines.append("**涉及接口 / 主题：**")
    lines.append("")
    for a in t["apis"]:
        lines.append(f"- `{a}`")
    lines.append("")
    lines.append("**功能与实现要点：**")
    lines.append("")
    lines.append(t["how"])
    lines.append("")
    lines.append("> 字段级说明见 `OCTCuda/01_API接口全解.md`；调用链见 `02_数据流与调用链.md`。")
    lines.append("")
    lines.append("## 动手任务")
    lines.append("")
    for h in t["hands"]:
        lines.append(f"- {h}")
    lines.append("")
    lines.append("## 任务参考")
    lines.append("")
    if t["refs"]:
        for r in t["refs"]:
            lines.append(f"- {r}")
    else:
        lines.append("- 见 `01_API接口全解.md` / `02_数据流与调用链.md`")
    lines.append("")
    lines.append("## 完成标准（DoD）")
    lines.append("")
    for d in t["dod"]:
        lines.append(f"- [ ] {d}")
    lines.append("")
    lines.append("## 明日预告")
    lines.append("")
    lines.append(t["nxt"])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*所属周主题见 `00_全局规划.md` §3。打卡：`03_进度追踪.md`。*")
    lines.append("")
    return "\n".join(lines)


def main():
    n = 0
    for w, days in weeks.items():
        for d, t in days.items():
            path = os.path.join(ROOT, f"Week{w:02d}", f"Day{d:02d}", "TASK.md")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(render(w, d, t))
            n += 1
    print(f"wrote {n} TASK.md files under {ROOT}")


if __name__ == "__main__":
    main()
