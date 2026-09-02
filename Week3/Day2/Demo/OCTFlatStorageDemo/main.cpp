#include <stdio.h>
#include "kernel.cu"
#include "opencv2/opencv.hpp"
#include "cstring"
#include <filesystem>
namespace fs = std::filesystem;

/**
 * Description:
 *		扁平化图片
 * @param imagePaths
 * @param width
 * @param height
 * @return
 */
unsigned char* loadImage(std::vector<std::string> imagePaths, int width, int height)
{
	// 解析图片
	int imageCount = imagePaths.size();
	size_t sliceBytes = (size_t)width * height;
	size_t volBytes = sliceBytes * imageCount;
	unsigned char* imagePtr = new unsigned char[volBytes];
	for (int y = 0; y < imageCount; y++)
	{
		auto image = cv::imread(imagePaths[y]);

		// 第y个切片起始偏移
		size_t dstOffset = (size_t)y * sliceBytes;
		memcpy(imagePtr + dstOffset, image.data, sliceBytes);
	}
	std::cout << "图片加载完毕" << std::endl;
    return imagePtr;
}
/**
 * Description:
 *
 * @param argc
 * @param argv
 * @return
 */
int main(int argc, char* argv[])
{
	const std::string folderPath = "E:\\CUDA\\Learning\\CudaStudy\\ImageTool\\DcmRead\\DcmReadPro\\output\\images";
	std::vector<std::string> imagePaths;
	if (!fs::is_directory(folderPath))
	{
		std::cout << "文件夹不存在" << std::endl;
	}
	for (const auto& entry : fs::directory_iterator(folderPath))
	{
		if (!entry.is_regular_file())
		{
			continue;
		}
		auto ext = entry.path().extension().string();
		if (ext != ".bmp" && ext != ".png")
		{
			continue;
		}
		imagePaths.push_back(entry.path().string());
	}
	if (imagePaths.empty())
	{
		std::cout << "文件夹内无图片" << std::endl;
		return -1;
	}
	auto image = cv::imread(imagePaths[0]);
	std::cout << "图片数量：" << imagePaths.size() << std::endl;
	std::cout << "图片宽度：" << image.rows << " 图片高度" << image.cols << std::endl;
	unsigned char* imagePtr = loadImage(imagePaths, image.rows, image.cols);


	// CUDA处理
	return 0;
}