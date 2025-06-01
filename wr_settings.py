import tomllib,json

import tomli_w
from PyQt5.QtCore import Qt
from qfluentwidgets import QConfig,RangeConfigItem,OptionsConfigItem,BoolValidator,ConfigItem,qconfig,RangeValidator,InfoBar,InfoBarPosition


class Settings(QConfig):
    morning_class_num=RangeConfigItem("table_style","morning_class_num",4,RangeValidator(1,10))
    afternoon_class_num=RangeConfigItem("table_style","afternoon_class_num",2,RangeValidator(1,10))
    show_teachers=OptionsConfigItem("table_style","show_teachers",True,BoolValidator())

    subjects_info=ConfigItem("lessons_info","subjects_info","")
    lessons_info=ConfigItem("lessons_info","lessons_info","")

    priority=ConfigItem("rules","priority","")

def load_settings():
    cfg=Settings()
    qconfig.load("settings.json", cfg)
    return cfg


def save_settings(window,msg_type=True,error:str=None):
    if msg_type:
        InfoBar.success(
            title='设置保存成功！',
            content="设置已生效",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=window
        )
    else:
        InfoBar.error(
            title='设置保存失败！',
            content=error,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=window
        )