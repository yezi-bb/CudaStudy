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
    void on_pushButton_Open_clicked();
    // CUDA处理图像
    void on_pushButton_Run_clicked();

private:
    Ui::MainWindow* ui;
    QImage m_originImg;    // 缓存原始图像
};
#endif // MAINWINDOW_H