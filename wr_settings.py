import logging
import traceback

from PyQt5.QtCore import Qt
from qfluentwidgets import QConfig,RangeConfigItem,OptionsConfigItem,BoolValidator,ConfigItem,qconfig,RangeValidator,InfoBar,InfoBarPosition


class Settings(QConfig):
    morning_class_num=RangeConfigItem("table_style","morning_class_num",4,RangeValidator(1,10))
    afternoon_class_num=RangeConfigItem("table_style","afternoon_class_num",2,RangeValidator(1,10))
    show_teachers=OptionsConfigItem("table_style","show_teachers",True,BoolValidator())
    text_font=ConfigItem("table_style","text_font","宋体")
    text_size=ConfigItem("table_style","text_size",9)

    subjects_info=ConfigItem("lessons_info","subjects_info","")
    lessons_info=ConfigItem("lessons_info","lessons_info","")
    teachers_info=ConfigItem("lessons_info","teachers_info","")

    school_name=ConfigItem("other_info","school_name","学校名称")
    lessons_time=ConfigItem("other_info","lessons_time","")
    activity_info=ConfigItem("other_info","activity_info","")

    rule_types=ConfigItem("rules","rule_types","")
    rules=ConfigItem("rules","rules","")

def load_settings():
    cfg=Settings()
    qconfig.load("settings.json", cfg)
    return cfg
cfg=load_settings()

def save_settings():
    try:
        logging.info(f"正在保存设置")
        # 将内存配置写入文件
        cfg.save()
        logging.info("保存设置成功")
    except:
        e=traceback.format_exc()
        logging.error(f"保存设置时出错：\n{e}")

def settings_error(window,error):
    InfoBar.error(
        title='设置保存失败！',
        content=error,
        orient=Qt.Horizontal,
        isClosable=True,
        position=InfoBarPosition.TOP,
        duration=-1,
        parent=window
    )