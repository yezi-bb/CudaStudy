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
    connect(ui->pushButton, &QPushButton::clicked, this, &MainWindow::on_pushButton_Open_clicked);
    connect(ui->pushButton_2, &QPushButton::clicked, this, &MainWindow::on_pushButton_Run_clicked);
}

MainWindow::~MainWindow()
{
    delete ui;
}

// 1.打开图片
void MainWindow::on_pushButton_Open_clicked()
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
void MainWindow::on_pushButton_Run_clicked()
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
    std::vector<unsigned char> outBuf(w * h, 0);

    // ===== 调用CUDA二值化 =====
    unsigned char threshold = 80; // 先改成127测试！
    CudaTool::getInstance().LaunchBinaryKernel(grayImg.bits(), outBuf.data(), w, h, threshold);

    // ===== 重点：深拷贝！防止vector销毁后内存失效 =====
    QImage resultImg(outBuf.data(), w, h, w, QImage::Format_Grayscale8);
    QImage safeImage = resultImg.copy();

    QGraphicsScene* sceneResult = new QGraphicsScene(this);
    sceneResult->addPixmap(QPixmap::fromImage(safeImage));
    ui->m_graphicsView_out->setScene(sceneResult);
    ui->m_graphicsView_out->fitInView(sceneResult->sceneRect(), Qt::KeepAspectRatio);
}