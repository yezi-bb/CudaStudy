#include "MainWindow.h"
#include "ui_MainWindow.h"
#include <QFileDialog>
#include <QGraphicsScene>
#include <QPixmap>
#include "CudaTool.h"   // 引入你之前写好的CUDA头文件

MainWindow::MainWindow(QWidget* parent)
	: QMainWindow(parent)
	, ui(new Ui::MainWindow)
{
	ui->setupUi(this);
	connect(ui->pushButton, &QPushButton::clicked, this, &MainWindow::pushButton_Open_clicked);
	connect(ui->pushButton_2, &QPushButton::clicked, this, &MainWindow::pushButton_Run_clicked);
}

MainWindow::~MainWindow()
{
	delete ui;
}

// 1.打开图片
void MainWindow::pushButton_Open_clicked()
{
	QString filePath = QFileDialog::getOpenFileName(this,
		tr("打开图像"),
		"./",
		tr("图片(*.png *.jpg *.bmp *.tiff)"));
	if (filePath.isEmpty())
		return;

	m_originImg.load(filePath);
	if (m_originImg.isNull())
		return;

	// 在左侧GraphicsView显示原图
	QGraphicsScene* scene = new QGraphicsScene(this);
	scene->addPixmap(QPixmap::fromImage(m_originImg));
	ui->m_graphicsView_in->setScene(scene);
	ui->m_graphicsView_in->fitInView(scene->sceneRect(), Qt::KeepAspectRatio);
}

// 2.调用CUDA二值化处理
void MainWindow::pushButton_Run_clicked()
{
	if (m_originImg.isNull())
		return;

	// ========== 图像统一转为8位灰度图 ==========
	QImage grayImg = m_originImg.convertToFormat(QImage::Format_Grayscale8);
	int w = grayImg.width();
	int h = grayImg.height();

	// ===== 消除Qt行对齐padding，保证每行字节 = width =====
	if (grayImg.bytesPerLine() != w)
	{
		QImage tempImg(w, h, QImage::Format_Grayscale8);
		for (int y = 0; y < h; ++y)
		{
			memcpy(tempImg.scanLine(y), grayImg.scanLine(y), w);
		}
		grayImg.swap(tempImg);
	}

	// 分配CPU输出缓冲区
	unsigned char* outBuf = new unsigned char[w * h];

	// ===== 调用CUDA二值化 =====
	unsigned char* threshold = new unsigned char[0]; // 先改成127测试！

	//求取阈值
	CudaTool::getInstance().LaunchHistsholdKernel(grayImg.bits(), threshold, w, h);
	qDebug() << "阈值：" << *threshold ;
	CudaTool::getInstance().LaunchBinaryKernel(grayImg.bits(), outBuf, w, h, *threshold);

	QImage resultImg(outBuf, w, h, w, QImage::Format_Grayscale8);
	if (outBuf != nullptr)
	{
		delete[] outBuf;
	}
	QImage safeImage = resultImg.copy();

	QGraphicsScene* sceneResult = new QGraphicsScene(this);
	sceneResult->addPixmap(QPixmap::fromImage(safeImage));
	ui->m_graphicsView_out->setScene(sceneResult);
	ui->m_graphicsView_out->fitInView(sceneResult->sceneRect(), Qt::KeepAspectRatio);

}

const QString ori_file = "./images";
const QString out_cuda_file = "./gpu_images";
const QString out_cpu_file = "./cpu_images";
void MainWindow::totalCudaAlgorithm()
{
	QDir dir(ori_file);
	QStringList filters;
	filters << "*.png" << "*.jpg" << "*.bmp" << "*.tiff";
	dir.setNameFilters(filters);
	QStringList fileList = dir.entryList();
	if (fileList.isEmpty())
	{
		qDebug() << "文件夹内无图片";
		return;
	}

	qint64 start = QDateTime::currentMSecsSinceEpoch();

	for (int i = 0; i < fileList.size(); ++i)
	{
		// 局部图片，不再复用m_originImg
		QImage srcImg;
		srcImg.load(ori_file + "/" + fileList[i]);
		if (srcImg.isNull())
			continue;

		QImage grayImg = srcImg.convertToFormat(QImage::Format_Grayscale8);
		int w = grayImg.width();
		int h = grayImg.height();

		// 消除行padding
		if (grayImg.bytesPerLine() != w)
		{
			QImage tempImg(w, h, QImage::Format_Grayscale8);
			for (int y = 0; y < h; ++y)
			{
				memcpy(tempImg.scanLine(y), grayImg.scanLine(y), w);
			}
			grayImg.swap(tempImg);
		}

		// ✅ 每张图像单独分配释放缓冲区，杜绝尺寸不一致越界
		unsigned char* outBuf = new unsigned char[w * h];
		memset(outBuf, 0, w * h);

		unsigned char threshold = 80;
		CudaTool::getInstance().LaunchBinaryKernel(grayImg.bits(), outBuf, w, h, threshold);

		QImage resultImg(outBuf, w, h, w, QImage::Format_Grayscale8);
		QImage saveImg = resultImg.copy(); // 内存独立！
		saveImg.save(out_cuda_file + "/" + fileList[i]);

		delete[] outBuf;
	}

	qint64 end = QDateTime::currentMSecsSinceEpoch();
	qDebug() << "CUDA total time(ms):" << end - start;
}

void MainWindow::totalCpuAlgorithm()
{
	QDir dir(ori_file);
	QStringList filters;
	filters << "*.png" << "*.jpg" << "*.bmp" << "*.tiff";
	dir.setNameFilters(filters);
	QStringList fileList = dir.entryList();
	if (fileList.isEmpty())
	{
		qDebug() << "文件夹内无图片";
		return;
	}

	qint64 start = QDateTime::currentMSecsSinceEpoch();
	const unsigned char threshold = 80;

	for (int i = 0; i < fileList.size(); ++i)
	{
		QImage srcImg;
		srcImg.load(ori_file + "/" + fileList[i]);
		if (srcImg.isNull())
			continue;

		QImage grayImg = srcImg.convertToFormat(QImage::Format_Grayscale8);
		int w = grayImg.width();
		int h = grayImg.height();

		// 和GPU代码保持一致：去除行padding
		if (grayImg.bytesPerLine() != w)
		{
			QImage tempImg(w, h, QImage::Format_Grayscale8);
			for (int y = 0; y < h; ++y)
			{
				memcpy(tempImg.scanLine(y), grayImg.scanLine(y), w);
			}
			grayImg.swap(tempImg);
		}

		unsigned char* outBuf = new unsigned char[w * h];
		const unsigned char* inData = grayImg.bits();

		// ========== CPU串行二值化（与BinaryKernel算法完全一致） ==========
		int pixelCount = w * h;
		for (int idx = 0; idx < pixelCount; idx++)
		{
			outBuf[idx] = inData[idx] > threshold ? 255 : 0;
		}

		QImage resultImg(outBuf, w, h, w, QImage::Format_Grayscale8);
		QImage saveImg = resultImg.copy();
		saveImg.save(out_cpu_file + "/" + fileList[i]);

		delete[] outBuf;
	}

	qint64 end = QDateTime::currentMSecsSinceEpoch();
	qDebug() << "CPU total time(ms):" << end - start;
}
