import logging
import sys

import pandas as pd
from PyQt5.QtWidgets import QTableWidgetItem
from qfluentwidgets import TableWidget

from wr_settings import *

sys.setrecursionlimit(10000)
logging.basicConfig(format="%(levelname)s %(filename)s %(funcName)s %(lineno)d行:\t%(message)s",
                    level=logging.DEBUG)
def lesson_to_str(lesson):
    """
    根据课程节次生成时间描述

    :param lesson: 课程节次
    :return: 时间描述（如"上午第1节"）
    """
    # 判断课程是在上午还是下午
    if lesson <= cfg.morning_class_num.value:
        time = "上午"
    else:
        time = "下午"
        # 调整课程节次为下午的相对节次
        lesson -= cfg.morning_class_num.value

    return f"{time}第{lesson}节"

def is_special(subject:str):
    """
    判断给定的课程名称是否为特殊课程

    :param subject: 课程名称
    :return: 如果课程是特殊课程，则返回True；否则返回False
    """
    return subject.endswith("(0.5)") or subject.endswith("（0.5）")

# 定义工作日列表
days = [0,"星期一", "星期二", "星期三", "星期四", "星期五"]

def display_df_in_table(table_widget: TableWidget, df: pd.DataFrame):
    df.columns=df.columns.astype(str)
    # 设置行数和列数
    table_widget.setRowCount(df.shape[0])
    table_widget.setColumnCount(df.shape[1])

    # 设置表头
    table_widget.setHorizontalHeaderLabels(df.columns)
    table_widget.setVerticalHeaderLabels([str(idx) for idx in df.index])

    # 填充数据
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            if str(df.iat[i, j]) in ["nan","None"]:
                continue
            item = QTableWidgetItem(str(df.iat[i, j]))
            item.setTextAlignment(Qt.AlignCenter)
            table_widget.setItem(i, j, item)

def rule_to_string(rule):
    """
    将规则转换为字符串

    :param rule: 规则
    :return: 规则的字符串表示
    """
    ans=cfg.rule_types.value[rule["type"]].replace("|","").replace("{","").replace("}","")
    for string in rule:
        if string=="type":
            continue
        ans=ans.replace(string,rule[string])
    return ans