#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QImage>
QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    MainWindow(QWidget* parent = nullptr);
    ~MainWindow();

public slots:
    // 打开图片
    void pushButton_Open_clicked();
    // CUDA处理图像
    void pushButton_Run_clicked();


#pragma region 时间统计
    void totalCudaAlgorithm();
    void totalCpuAlgorithm();

#pragma endregion
private:
    Ui::MainWindow* ui;
    QImage m_originImg;    // 缓存原始图像
};
#endif // MAINWINDOW_H