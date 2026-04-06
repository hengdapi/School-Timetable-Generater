# coding=utf-8
import sys
from PySide6 import QtWidgets
from PySide6.QtGui import QIcon,QFont
from PySide6.QtCore import QLocale,QSize
from qfluentwidgets import MSFluentWindow,SplashScreen,FluentTranslator,setThemeColor,setTheme,Theme
from qfluentwidgets.common.icon import FluentIcon
from pages import home,settings,generate
from qframelesswindow.utils import getSystemAccentColor
from qframelesswindow import StandardTitleBar

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
        splashScreen=SplashScreen(self.windowIcon(),self)
        splashScreen.setIconSize(QSize(150,150))
        self.show()

        self.addSubInterface(home.Home(),FluentIcon.HOME,"主页")
        self.addSubInterface(settings.Settings(),FluentIcon.SETTING,"设置")
        self.addSubInterface(generate.Generate(),FluentIcon.BRUSH,"生成")

        splashScreen.finish()


if __name__ == '__main__':
    app=QtWidgets.QApplication(sys.argv)
    translator=FluentTranslator(QLocale(QLocale.Chinese,QLocale.China))
    app.installTranslator(translator)
    ui=Window()
    ui.show()
    sys.exit(app.exec())
