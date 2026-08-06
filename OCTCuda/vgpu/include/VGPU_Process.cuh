// ------------------------------------------------------------
// Copyright (c) 2024, VIVO-LIGHT MEDICAL CORP. All rights reserved.
// Name         : VGPU_Process_cu.h
// Description  : GPU Process DLL definition
// History      : Caojie 2024.04.26
// ------------------------------------------------------------

#ifndef VGPU_PROCESS_CUH
#define VGPU_PROCESS_CUH

#include <opencv2/opencv.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/core/core.hpp>
#include <opencv2/core/mat.hpp>
#include "vector_types.h"
#include <vector>
#include <process.h>  

using namespace cv;


#define CAL_ERROR                0
#define CAL_SUCCESS              1
#define PI                       (3.141592653589793)
#define EPS                      (2.2204e-16)
#define BLOCK_DIM                256
#define WARPSIZE                 32
#define ALINE_NUM                (2*ALINES_PER_FRAME)
#define VALID_R				     900
#define FRAME_NUM                5
#define RESIZE_HW                128
#define COLOR_LEVEL              256
#define COLOR_CHANNEL            3

#define LOW_SIGMAS               2.0
#define LOW_SIGMAR               2*LOW_SIGMAS
#define HIGH_SIGMAS              3.0
#define HIGH_SIGMAR              2*HIGH_SIGMAS 
#define ALINE_BAND_SIZE          300  
#define ALINE_BAND_START         50
#define POSITION_UP_THRESHOLD    85
#define POSITION_DOWN_THRESHOLD  50
#define VALUE_THRESHOLD          100

#define LINE_AVERAGE_GAP	     20   //光源越亮，值可适当调大
#define PULL_BACK_THRESHOLD	     200  //100 域值 alines/3 三分之一被冲开

#define MYINDEX(i, j, cols)     (((i)*(cols))+(j))//行为主


//定义需要的数据结构（与调用中的数据结构相对应）
typedef unsigned short U16;
typedef unsigned char U8;

//自定义complex类型的struct
typedef struct
{
	float x;                  //FFT实部
	float y;                  //FFT虚部
}ComplexData;

/*窗函数类型*/
typedef enum
{
	Bartlett = 0,             //巴特利特窗
	BartLettHann,             //巴特利特汉宁窗
	BlackMan,                 //布莱克曼窗
	BlackManHarris,           //布莱克曼哈里斯窗
	Bohman,                   //博曼窗
	Chebyshev,                //切比雪夫窗
	FlatTop,                  //平顶窗
	Gaussian,                 //高斯窗
	Hamming,                  //海明窗
	Hann,                     //汉宁窗
	Kaiser,                   //凯撒窗
	Nuttal,                   //纳托尔窗
	Parzen,                   //帕曾窗
	Rectangular,              //矩形窗
	Taylor,					  //泰勒窗
	Triangular,               //三角窗
	Tukey                     //杜克窗
}WinType;

/*DSC后灰度图像增强类型*/
typedef enum
{
	LinearEnhanceType = 1,    //线性增强
	PowEnhanceType,           //乘方增强
	LogEnhanceType,           //对数增强
	ExpEnhanceType            //指数增强
}GrayEnhanceType;

/*灰度图像DSC插值类型*/
typedef enum
{
	INTER_AJACENT = 1,        //最邻近插值
	INTER_BILINEAR,           //双线性插值
	INTER_BITRIPLE            //三次双卷积插值
}InterpolateType;

/*GPU内存管理类型*/
typedef enum
{
	GPU_MALLOC = 1,           //GPU内存分配
	GPU_RELEASE               //GPU内存释放
}GPUMemoryManageType;

/*DOC动作类型*/
typedef enum
{
	DOC_SCAN = 1,             //DOC扫描进行
	DOC_PULLBACK_BEFORE,      //DOC回拉过程
	DOC_PULLBACK_AFTER        //DOC回拉完成
}DOCMotionType;

/*光源类型*/
typedef enum
{
	GpuAxsunLightSource = 0,	//Axsun光源
	GpuThorlabsLightSource		//Throlab光源
}GPULightSourceType;

/*校准类型*/
typedef enum
{
	GpuConnectCalibration = 0,	//连接导管校准
	GpuAutoCalibration			//术中自动校准
}GPUCalibrationType;

/*伪彩色映射类型*/
typedef enum
{
	Color_Golden = 1,         //黄金色
	Color_Gray,               //黑白色
	Color_Red,                //红色
	Color_Orange,             //橙色
	Color_Green,              //绿色
	Color_Blue,               //蓝色
	Color_Indigo,             //靛色
	Color_Purple              //紫色
}ColorsMapType;

/*L模式图像平滑算法类型*/
typedef enum
{
	Smooth_Bilateral_Filter = 1,                   //双边滤波平滑
	Smooth_Fast_Mean_Filter,                       //快速均值滤波
	Smooth_Double_convolution_Filter,              //双卷积平滑 
	Smooth_None                                    //不使用平滑算法
}LModeSmoothMethod;

/*L模式图像平滑等级*/
typedef enum
{
	Smooth_Off = 1,          //平滑关闭 
	Smooth_Low,              //低度平滑 
	Smooth_High              //高度平滑
}LModeSmoothLevel;

//IPA计算参数
struct att_paras {
	float z0;
	float zR;
	float zC;
	float zw;
	float SNRmax;
	float noise_level;
	int minwin;
	float stepsucc;
	float stepfail;
	float scandepth;
	int number_frames;
	int number_depths;
	int number_theta;
	int number_alines;
	float step_success;
	float step_fail;
};


#pragma region 参数配置与显存分配
/*GPU内存初始化，分配/是否内存操作*/
extern "C" __declspec(dllexport) bool VGPU_Allocate_Parameter_Manager(int current_piu_speed, int noise_max_index, int noise_width,
	int original_data_buf_lines_number, int scan_lines_number, int pullback_lines_number,int points_per_aline, int image_height, int image_width, 
	int pullback_total_fram_numer, float* calibration_data);

//设置功能配置
extern "C" __declspec(dllexport) void VGPU_SetFunctionConfig(bool is_need_remove_dc);

/*设置标定文件参数*/
extern "C" __declspec(dllexport) bool VGPU_SetCalibrationData(float* calibration_data, int points_per_aline);


//
/************************************************************************/
/* GPU内存初始化，分配/是否内存操作 */
/*
输入：all_aline_mu_data 所有μ值结果
iwidth 单帧宽度（一线数据的点数）
iheight  单帧高度（一帧数据的线数）
ipullback_frames  回拉帧数
icut_start 裁剪起点
icut_size  裁剪大小
output_circle_diameter 输出圆图的边长
输出：output_circle_data 所有圆图
返回 true 表示成功， false表示失败
*/
/************************************************************************/
extern "C" __declspec(dllexport) bool VGPU_Free_Parament_Manager(bool isfree_CalibrationConfig);

//深度学习算法调用完毕后，再次重新分配计算显存
extern "C" __declspec(dllexport) bool VGPU_Reallocate_memory();


//获取cuda错误状态 返回false代表异常，返回true代表正常
extern "C" __declspec(dllexport) bool VGPU_GetCudaErrorStatus();

//获取当前显卡显存相关参数
extern "C" __declspec(dllexport) void VGPU_GetCurrentGPUMemory(double& total_memory, double& free_memory, double& used_memory);

//计算过程出现cuda异常时，重置当前进程显存
extern "C" __declspec(dllexport) bool VGPU_ResetCudaMemory();
#pragma endregion

#pragma region 扫描回拉过程计算
/*对扫描状态和回拉结束前采集原始数据重采样，然后加汉宁窗*/
extern "C" __declspec(dllexport) bool VGPU_Data_Resampling_For_Scan(DOCMotionType status, U16* Original_data_scan, float* Hannwin_data, bool is_device_to_host);
extern "C" __declspec(dllexport) bool VGPU_Data_Resampling_For_Scan_Vivo(DOCMotionType status, double gain_multiplier, int offset_data, U8 * Original_data_scan, float* Hannwin_data, bool is_device_to_host);
/*对回拉结束后采集原始数据重采样，然后加汉宁窗*/
extern "C" __declspec(dllexport) bool VGPU_Data_Resampling_For_Pullback(DOCMotionType status, unsigned short frame_sum, float* h_Hannwin_data, bool is_device_to_host);

/*对加窗数据进行FFT变换和Log求和*/
extern "C" __declspec(dllexport) bool VGPU_Get_FFT_Power_Result(DOCMotionType status, float* h_Power_data, float times, bool is_device_to_host);
extern "C" __declspec(dllexport) bool VGPU_Get_FFT_Power_Interpolation_Result(DOCMotionType status, float ground_noise, float* h_Power_data, U16* h_interpolation_data, bool is_device_to_host);

//回拉过程处理
extern "C" __declspec(dllexport) bool VGPU_Pullback_ProcessData_ToImage(U16* Original_data, U8* Original_data_vivo, int current_pullback_frame, float ground_noise,
	double gain_multiplier, int offset_data, U16* h_One_FFT_Power_data, bool is_device_to_host);

/*对压缩后的数据取Log*/
extern "C" __declspec(dllexport) bool VGPU_Get_After_Log_Result(DOCMotionType status, float* h_Log_data, bool is_device_to_host);
/*旧记录数据Log逆变换*/
extern "C" __declspec(dllexport) bool VGPU_Get_old_data_toLog_Result(float *h_after_Log_data, int width, int height, int frame_number, float &out_record_ground_noise, U16 *h_before_Log_data);

/*旧记录数据自动裁剪掉前25个点*/
extern "C" __declspec(dllexport) bool VGPU_Get_old_data_cutfront25_Result(float *h_after_Log_data, int width, int height, int frame_number);

/*新记录数据Log变换*/
extern "C" __declspec(dllexport) bool VGPU_Get_Denoising_data_toLog_Result(U16 *h_before_Log_data, int width, int height, int frame_number, float *h_after_Log_data);

/*取Log后的U16转F32*/
extern "C" __declspec(dllexport) bool VGPU_Get_U16fft_data_toF32fft_Result(U16 *h_u16_Log_data, int width, int height, int frame_number, float *h_after_Log_data);

/*取Log后的F32转U16*/
extern "C" __declspec(dllexport) bool VGPU_Get_F32fft_data_toU16fft_Result(float *h_after_Log_data, int width, int height, int frame_number, U16 *h_u16_Log_data);

//传出当前帧FFT数据，为保存拍照原始数据功能
extern "C" __declspec(dllexport) bool VGPU_Get_Current_Frame_FFT_data(DOCMotionType status, U16* h_One_FFT_Power_data);
extern "C" __declspec(dllexport) bool VGPU_Get_Current_Frame_FFT_After_Interpolation_data(DOCMotionType status, U16* h_One_FFT_Interpolation_data);

/*对Log求和数据进行转置裁剪*/
extern "C" __declspec(dllexport) bool VGPU_Transpose(DOCMotionType status, int start, int end, cv::Mat& Transpose_Mat, bool is_device_to_host);
extern "C" __declspec(dllexport) bool VGPU_Transpose_CheckImage(DOCMotionType status, int start, int end, cv::Mat& Transpose_Mat, bool is_device_to_host);

/*对转置裁剪后的数据进行DSC(极坐标）变换*/
extern "C" __declspec(dllexport) bool VGPU_DSC(DOCMotionType status, int raw_rows, int raw_cols, float* h_DSC_data, 
	int polar_rows, int polar_cols, int inner_r, int margin_r, InterpolateType interpolate_method, bool is_device_to_host);

/*对灰度图像进行增强处理*/
extern "C" __declspec(dllexport) bool VGPU_Image_Enhancement(int dsc_rows, int dsc_cols, int frame_no, unsigned char* h_Enhance_data,
	float low_bound, float up_bound, float pow_index, GrayEnhanceType enhance_type, int is_device_to_host);

/*对增强灰度图进行伪彩色映射*/
extern "C" __declspec(dllexport) bool VGPU_Gray2Color(cv::Mat& CpuMat, int enhance_img_rows, int enhance_img_cols, bool is_device_to_host);
#pragma endregion

#pragma region 导管校准相关接口
/*参考臂自动校准*/
extern "C" __declspec(dllexport) bool VGPU_AutoCalibration_new(int TransPose_height, int Transpose_width, int pos_up_threshold, int pos_down_threshold, 
	int threshold_data, int blocksize, double LineBrightness, double PackDifference, double hdelt, double hbrightness, double NextValue, int &h_delt_y);
extern "C" __declspec(dllexport) bool VGPU_AutoCalibration_connect(GPUCalibrationType calibrate_type, float ground_noise, int indexFrams,
	int TransPose_height, int Transpose_width, int pos_up_threshold, int pos_down_threshold,
	int threshold_data, int blocksize, double LineBrightness, double PackDifference, double hdelt, double hbrightness, double NextValue);

//11版新导管校准算法
extern "C" __declspec(dllexport) bool VGPU_Catheter_AutoCalibration(GPUCalibrationType calibrate_type, GPULightSourceType light_source_type, bool is_new_catheter, float ground_noise, int indexFrams, double cutHeight,
	int TransPose_height, int Transpose_width, cv::Mat& out_calibration_data, bool is_device_to_host,bool is_twice_check);

//校准测试接口
extern "C" __declspec(dllexport)  bool VGPU_AutoCalibration_new_cs(float* inTranspose_data_for_scan, int TransPose_height, int Transpose_width, int pos_up_threshold,
	int pos_down_threshold, int threshold_data, int blocksize, double LineBrightness, double PackDifference, double hdelt, double hbrightness, double NextValue, int &h_delt_y);
extern "C" __declspec(dllexport) bool VGPU_AutoCalibration_connect_cs(int indexFrams, float* inTranspose_data_for_scan, 
	int TransPose_height, int Transpose_width, int pos_up_threshold, int pos_down_threshold,
	int threshold_data, int blocksize, double LineBrightness, double PackDifference, double hdelt, double hbrightness, double NextValue);

//返回0 算法域值问题，1硬件问题
extern "C" __declspec(dllexport) int VGPU_CheckImageInfo();
#pragma endregion


#pragma region 自动回拉造影剂检测相关接口
//10版新介质冲洗识别算法
extern "C" __declspec(dllexport) bool VGPU_Contrast_MediumCheck5(float ground_noise, double catheterCutHeight, int currentFrames);

extern "C" __declspec(dllexport) bool VGPU_Contrast_MediumCheck_Afd(float ground_noise, double catheterCutHeight, int currentFrames, bool isSmoke,
	float bright_threshold, float gap_threshold1, float gap_threshold2, float gap_threshold3);
#pragma endregion

//导管折断检测
extern "C" __declspec(dllexport) bool VGPU_CheckCatheterBreakDetection(float ground_noise, float threshold, double condition1, double condition2, cv::Mat& out_CheckImage, bool is_device_to_host);

//回拉过程guiding检测
extern "C" __declspec(dllexport) bool VGPU_guidingDetectOneFrame(int startRow, double threshold, int window, std::vector<double>& avgPixels, int totalFrame);

#pragma region 回拉后处理，分析预处理相关设计
//用于分配检测回拉数据显存
extern "C" __declspec(dllexport) bool VGPU_Check_pullback_Data_memory();

/*将回拉结束后采集的回拉序列原始数据传递给设备内存*/
//extern "C" __declspec(dllexport) bool VGPU_Set_Original_pullback_Data_To_GPU(int pullback_frame_sum, float ground_noise, U16* h_Original_data_pullback);
extern "C" __declspec(dllexport) bool VGPU_Set_Original_pullback_Data_To_GPU(int pullback_frame_sum, float ground_noise, double gain_multiplier, int offset_data, U16 * h_Original_data_pullback, U8 * h_Original_data_pullback_vivo);

/*处理所有帧的数据，生成fft数据*/
extern "C" __declspec(dllexport) void VGPU_Handle_All_Preview_data(float ground_noise);

/*获取所有帧的FFT之后的数据传给cpu*/
extern "C" __declspec(dllexport) void VGPU_Get_All_FFT_data(U16 *all_denoising_data, int pullback_frame_sum, float ground_noise);

/*获取方图和圆图数据*/
extern "C" __declspec(dllexport) void VGPU_Handle_All_FFT_data(bool is_out_after_noise_data, float in_record_ground_noise, unsigned char*output_rectangle_data, unsigned char*output_circle_data, int start, int end, int output_circle_diameter, float in_low_boundary, float in_up_boundary);

//处理所有的fft数据生成校准后的图像
extern "C" __declspec(dllexport) void VGPU_Handle_All_Calibration_Image(bool is_out_after_noise_data, float in_record_ground_noise, unsigned char* output_rectangle_data, unsigned char*output_circle_data, int icut_start, int icut_size, int output_circle_diameter, float in_low_boundary, float in_up_boundary);

//处理一帧Raw数据生成圆图图像
extern "C" __declspec(dllexport) bool VGPU_OneFrameRawData_To_Image(U16 *raw_data, int iwidth, int iheight, Mat&out_mat, int start, int end, float low_boundary, float up_boundary);


//处理一组回拉数据生成FFT之后的方图（竞品.oct数据处理成FFT数据，未裁剪）
extern "C" __declspec(dllexport) bool VGPU_PullbackRawData_To_FFT_Data(U16 *raw_data, int iwidth, int iheight, int ipullback_frames, U16* all_rectangle_data);

//处理一组回拉数据的FFT数据生成方图和圆图像（对竞品oct数据转fft数据进行运算）
extern "C" __declspec(dllexport) bool VGPU_C7C8_PullbackFFT_Data_To_Image(U16 * all_rectangle_data, int iwidth, int iheight, int ipullback_frames,
	unsigned char* output_rectangle_data, unsigned char*output_circle_data, int icut_start, int icut_size, int output_circle_diameter);

//处理一组回拉DCM方图数据生成方图和圆图（对竞品dcm数据进行运算）
extern "C" __declspec(dllexport)  bool VGPU_PullbackDcm_Data_To_Image(unsigned char * all_dcm_rectangle_data, int iwidth, int iheight, int ipullback_frames,
	unsigned char* output_rectangle_data, unsigned char*output_circle_data, int icut_start, int icut_size, int output_circle_diameter);

//处理一组回拉数据生成方图和圆图像（竞品原始.oct转方图和圆图）
extern "C" __declspec(dllexport) bool VGPU_PullbackRawData_To_Image(U16 *raw_data, int iwidth, int iheight, int ipullback_frames,
	unsigned char* output_rectangle_data, unsigned char*output_circle_data, int icut_start, int icut_size, int output_circle_diameter);


/*把所有的fft数据传给gpu*/
extern "C" __declspec(dllexport) bool VGPU_Set_all_U16_FFT_data_to_Gpu(U16* all_rectangle_data, int pullback_frame_sum, float ground_noise);
extern "C" __declspec(dllexport) bool VGPU_Set_all_FFT_data_to_Gpu(float * all_rectangle_data, int pullback_frame_sum);

/*自适应计算当前回拉数据的对比度*/
extern "C" __declspec(dllexport) bool VGPU_CalculatedContrastRange(float& low_boundary, float& up_boundary);
#pragma endregion


/*获取对应帧数据*/
extern "C" __declspec(dllexport) void VGPU_Hnad_One_Frame_Data(int iframe, Mat&out_mat, int start, int end, float low_boundary, float up_boundary, GrayEnhanceType enhance_type, float coefficient_for_enhance);


/*计算一帧取log后的均值(光灵敏度测试使用，计算过程保留去底噪前的设计)*/
extern "C" __declspec(dllexport) bool VGPU_Data_Power_aline(U16* Original_data_scan, float ground_noise, float* aline_power_data);

extern "C" __declspec(dllexport) bool VGPU_Vivo_Data_Power_aline(U8* Original_data_scan, double gain_multiplier, int offset_data, float ground_noise, float* aline_power_data);

/************************************************************************/
/* 管腔智能拼接功能 */
/*
输入：far_end_data 远端FFT数据
far_startF 远端帧起点
far_endF  远端帧终点
near_end_data  近端FFT数据
near_startF 近端帧起点
near_endF  近端帧终点
near_totation_angle 近端数据旋转角度
输出：stitching_data 拼接后的FFT数据
返回 true 表示成功， false表示失败
*/
/************************************************************************/
extern "C" __declspec(dllexport) bool VGPU_Get_Lumen_Stitching_FFT_Image(float *far_end_data, int far_startF, int far_endF, int far_cut_start, float *near_end_data, int near_startF, int near_endF, int near_cut_start, int near_totation_angle, float *stitching_data);
extern "C" __declspec(dllexport) bool VGPU_Get_Lumen_Stitching_Denoising_Data(U16 *far_end_data, int far_startF, int far_endF, int far_cut_start, U16 *near_end_data, int near_startF, int near_endF, int near_cut_start, int near_totation_angle, U16 *stitching_data);

/*------------------以下为连续校准相关处理接口--------------------*/
//输出对应帧号的圆图(连续校准预处理)
extern "C" __declspec(dllexport) bool VGPU_Continuous_Clibration_To_Circle_Image(bool is_out_after_noise_data, float in_record_ground_noise, int* frame_number, int out_frames, unsigned char*output_circle_data, int icut_start, int icut_size, int output_circle_diameter);

//处理所有的fft数据生成连续校准后的图像
extern "C" __declspec(dllexport) bool VGPU_Get_All_Continuous_Calibration_Image(bool is_out_after_noise_data, float in_record_ground_noise, unsigned char* output_rectangle_data, unsigned char*output_circle_data, int *icut_start, int icut_size, int output_circle_diameter, float in_low_boundary, float in_up_boundary);

//更新连续校准后的图像帧
extern "C" __declspec(dllexport) bool VGPU_Update_Frame_Continuous_Calibration_Image(bool is_out_after_noise_data, float in_record_ground_noise, unsigned char* output_rectangle_data, unsigned char* output_circle_data,
	int update_frame, int icut_start, int icut_size, int output_circle_diameter, float in_low_boundary, float in_up_boundary);


//处理一组竞品.oct回拉数据连续校准
extern "C" __declspec(dllexport) bool VGPU_C7C8_Get_All_Continuous_Calibration_Image(U16 * all_rectangle_data, int iwidth, int iheight, int ipullback_frames,
	unsigned char* output_rectangle_data, unsigned char*output_circle_data, int *icut_start, int icut_size, int output_circle_diameter);

/************************************************************************/
/* 连续校准功能 */
/*
输入：machine_model 0冠脉，1颈动脉，2颅内
iheight 帧图像高度
iwidth  帧图像高度
ipullback_frames  总帧数
polarPixelSpacing 像素分辨率
输出：catheterCutStartHeight 裁剪起点
返回 true 表示成功， false表示失败
*/
/************************************************************************/
extern "C" __declspec(dllexport)  bool VGPU_GetContinuousCalibration(int machine_model, bool is_new_catheter, int iheight, int iwidth, int ipullback_frames, double polarPixelSpacing, int* catheterCutStartHeight);

#pragma region IPA计算相关设计接口
/************************************************************************/
/* 计算IPA结果  */
/*
输入：
h_paras  输入att_paras结构体相关IPA计算参数
in_all_raw_data 原始数据
in_reshaped_lumen 相关管腔计算参数
in_reshaped_media  相关管腔计算参数+100
in_labels_data  相关管腔计算参数(健康非健康)
in_ipa_11_mat_cof 域值参数（原来值为11，现在值为14）
输出：out_all_aline_mu 所有μ值结果
out_carpet_att μ值结果
out_ipa_fin IPA结果
isVivoData true 表示微光的数据， false表示竞品的数据
返回 true 表示成功， false表示失败
*/
/************************************************************************/
extern "C" __declspec(dllexport) bool VGPU_Calculate_Ipa_Result(att_paras h_paras, U16* in_all_raw_data, int* in_reshaped_lumen, int in_reshaped_media, int* in_labels_data,
	float* out_all_aline_mu, float* out_carpet_att, float in_ipa_11_mat_cof, float in_record_ground_noise, bool isVivoData);

/************************************************************************/
/* 处理一组回拉数据的所有μ值数据生成圆图像 */
/*
输入：all_aline_mu_data 所有μ值结果
iwidth 单帧宽度（一线数据的点数）
iheight  单帧高度（一帧数据的线数）
ipullback_frames  回拉帧数
icut_start 裁剪起点
icut_size  裁剪大小
output_circle_diameter 输出圆图的边长
输出：output_circle_data 所有圆图
返回 true 表示成功， false表示失败
*/
/************************************************************************/
extern "C" __declspec(dllexport) bool VGPU_All_Aline_Mu_Data_To_Image(float* all_aline_mu_data, int iwidth, int iheight, int ipullback_frames,
	unsigned char* output_circle_data, int* icut_start, int icut_size, int output_circle_diameter,bool isVivoData);


/************************************************************************/
/*  调整IPA阈值，重新计算IPA值*/
/*
输入：InlineIPA 回拉序列线IPA值结果（一帧的线数 * 帧数）
iFrameNumbers 帧数
iAllLineNumbers  所有线数（一帧的线数 * 帧数）
pixelSapcing  帧间距
isVivolightIPA 是否时间微光的数据
InMode_ID  如果是非工作站版本，0；工作站版本：有选项，0：3
InThresholdT IPA阈值，软件有参数P60 9.5  其它10.5  竞品 11
输出：IPA_L  1*iFrameNumbers大小
IPA_L_RangeMean  1*iFrameNumbers大小
IPA_A
IPA_T
IPA_A_colorbar
IPA_L_colorbar
返回 true 表示成功， false表示失败
*/
/************************************************************************/
extern "C" __declspec(dllexport) bool VGPU_UpdateValueIPA(float* InlineIPA, int iFrameNumbers, int iAllLineNumbers, double pixelSapcing,
	bool isVivolightIPA, double InMode_ID, double InThresholdT, double* ipa_l_data, double* ipa_l_range_mean_data,
	float* IPA_A, unsigned char* IPA_T, double* IPA_A_colorbar, int* IPA_L_colorbar);
#pragma endregion

#endif
