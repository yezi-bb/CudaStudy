#include <QtWidgets/QApplication>
#include <QtWidgets/QMainWindow>
#include "Mainwindow.h"
int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    MainWindow w(0);
    w.show();
    //w.totalCudaAlgorithm();
    //w.totalCpuAlgorithm();
    return app.exec();
}
