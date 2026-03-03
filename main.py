# coding=utf-8
import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon,QFont
from PyQt5.QtCore import Qt,QCoreApplication,QLocale,QSize,QEventLoop,QTimer
from qfluentwidgets import MSFluentWindow,SplashScreen,FluentTranslator,setThemeColor,setTheme,Theme
from qfluentwidgets.common.icon import FluentIcon
from pages import home,settings,generate
from qframelesswindow.utils import getSystemAccentColor

class Window(MSFluentWindow):
    def __init__(self):
        super().__init__()
        if sys.platform in ["win32","darwin"]:
            setThemeColor(getSystemAccentColor(),save=False)
        setTheme(Theme.AUTO,save=False)
        self.setWindowTitle("课程表生成器")
        self.setWindowIcon(QIcon("logo.ico"))
        self.setFont(QFont("Microsoft YaHei", 20))
        self.resize(1300, 700)

        screen = self.screen().availableGeometry()
        size = self.size()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2)
        )

        #启动页面
        self.splashScreen=SplashScreen(self.windowIcon(),self)
        self.splashScreen.setIconSize(QSize(102,102))
        self.show()
        loop=QEventLoop(self)
        QTimer.singleShot(500,loop.quit)
        loop.exec()
        self.splashScreen.finish()

        self.addSubInterface(home.Home(self),FluentIcon.HOME,"主页")
        self.addSubInterface(settings.Settings(self),FluentIcon.SETTING,"设置")
        self.addSubInterface(generate.Generate(self),FluentIcon.BRUSH,"生成&导出")


if __name__ == '__main__':
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app=QtWidgets.QApplication(sys.argv)
    translator=FluentTranslator(QLocale(QLocale.Chinese,QLocale.China))
    app.installTranslator(translator)
    ui=Window()
    ui.show()
    sys.exit(app.exec_())