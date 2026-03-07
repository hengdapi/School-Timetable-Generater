import traceback

from PyQt5.QtWidgets import QFileDialog,QFrame

from locals import *

def save_timetable(window:QFrame):
    try:
        filename,_=QFileDialog.getSaveFileName(window,"保存课程表","","Microsoft Excel 工作表(*.xlsx);;Microsoft Excel 97-2003 工作表(*.xls)")
        if not filename:
            return
        logging.info(f"保存课程表文件名：{filename}")

    except:
        e=traceback.format_exc()
        logging.critical(f"保存课程表出错：\n{e}")