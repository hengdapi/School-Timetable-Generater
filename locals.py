from __future__ import annotations

import sys,copy
from typing import Literal

import pandas as pd
from PySide6.QtWidgets import QTableWidgetItem
from qfluentwidgets import TableWidget

from wr_settings import *

sys.setrecursionlimit(10000)
logging.basicConfig(format="[%(levelname)s] %(filename)s %(funcName)s %(lineno)d行:\t%(message)s",
                    level=logging.INFO)
# ,filename="log.txt",filemode="w",encoding="utf-8"
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

def table_style(content=None)->pd.DataFrame:
    table_style={}
    for day in days[1:]:
        table_style[day]={}
        for lesson in range(1,cfg.morning_class_num.value+1):
            table_style[day][f"上午第{lesson}节"]=content
        for lesson in range(1,cfg.afternoon_class_num.value+1):
            table_style[day][f"下午第{lesson}节"]=content
    return pd.DataFrame(table_style)

def class_total_dataframe()->pd.DataFrame:
    data={}
    for clas in results.class_lst:
        data[clas.name]={}
        timetable=clas.timetable_dataframe.to_dict()
        for day,lessons in timetable.items():
            for time,lesson in lessons.items():
                data[clas.name][day+time]=lesson
    return pd.DataFrame(data).transpose()

def teacher_total_dataframe()->pd.DataFrame:
    data={}
    for teacher in results.teachers.values():
        data[teacher.name]={}
        timetable=teacher.timetable_dataframe.to_dict()
        for day,lessons in timetable.items():
            for time,lesson in lessons.items():
                data[teacher.name][day+time]=lesson
    dataframe=pd.DataFrame(data).transpose()
    dataframe=dataframe[[str(Time(day,lesson)) for day in range(1,6) for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)]]
    return dataframe

class Time:
    def __init__(self,day:int=0,lesson:int=0,week:Literal["sin","dou","all"]="all",string:str=None):
        if string:
            self.day=days.index(string[:3])
            self.lesson=int(string[6:-1])
            if "下午" in string:
                self.lesson+=cfg.morning_class_num.value
            if "【单】" in string:
                self.week="sin"
            elif "【双】" in string:
                self.week="dou"
            else:
                self.week="all"
        else:
            self.day=day
            self.lesson=lesson
            self.week=week
        self.sin=(self.week=="sin")
        self.dou=(self.week=="dou")
        self.all=(self.week=="all")
        self.half=not self.all
    def __eq__(self, other):
        return self.day==other.day and self.lesson==other.lesson and self.week==other.week
    def __hash__(self):
        return hash((self.day,self.lesson,self.week))
    def __str__(self):
        return {"sin":"【单】","dou":"【双】","all":""}[self.week]+days[self.day]+lesson_to_str(self.lesson)

    def to_str(self,day:bool,lesson:bool,week:bool=False):
        string=""
        if week:
            string+={"sin":"【单】","dou":"【双】","all":""}[self.week]
        if day:
            string+=days[self.day]
        if lesson:
            string+=lesson_to_str(self.lesson)
        return string

    @property
    def sin_week(self):
        return Time(self.day,self.lesson,"sin")
    @property
    def dou_week(self):
        return Time(self.day,self.lesson,"dou")
    @property
    def all_week(self):
        return Time(self.day,self.lesson,"all")

class Teacher:
    """
    教师类，用于管理教师的课程时间
    """
    def __init__(self, name:str):
        """
        初始化教师对象

        :param name: 教师姓名
        """
        self.name = name
        self.timetable:dict[Time,tuple[Class,Subject]]={}  # 记录教师已占用的课程时间

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, Teacher):
            return False
        return self.name==other.name

    def __hash__(self):
        return hash(self.name)

    def add_lesson(self,time:Time,clas:Class,subject:Subject):
        """
        添加教师的课程时间
        """
        self.timetable[time]=(clas,subject)

    def is_busy(self,time:Time):
        """
        检查教师在特定时间是否有课
        :return: 是否有课
        """
        if time.all:
            return time.dou_week in self.timetable or time.sin_week in self.timetable or time.all_week in self.timetable
        elif time.sin:
            return time.sin_week in self.timetable or time.all_week in self.timetable
        else:
            return time.dou_week in self.timetable or time.all_week in self.timetable

    def remove_lesson(self,time:Time):
        """
        移除教师在特定时间上的课程
        """
        self.timetable.pop(time)

    @property
    def timetable_dataframe(self)->pd.DataFrame:
        data=copy.deepcopy(table_style())
        for time,lesson in self.timetable.items():
            if data.loc[time.to_str(False,True),time.to_str(True,False)]:
                lines=data.loc[time.to_str(False,True),time.to_str(True,False)].split("\n")
                lines[0]+=f"/{lesson[0]}"
                lines[1]+=f"/{time.to_str(False,False,True)}{lesson[1]}"
                data.loc[time.to_str(False,True),time.to_str(True,False)]="\n".join(lines)
            else:
                data.loc[time.to_str(False,True),time.to_str(True,False)]=f"{lesson[0]}\n{time.to_str(False,False,True)}{lesson[1]}"
        return data

class Subject:
    def __init__(self, name:str, teachers:dict[str,Teacher]):
        """
        初始化课程对象

        :param name: 课程名称
        :param teachers: 课程任课教师列表({班级:老师})
        """
        self.name = name
        self.teachers = teachers
        self.continue_lesson=False
        self.time_list:dict[Time,int]={Time(day,lesson):0 for day in range(1,6) for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)}
        self.timetable:dict[Time,list[Class]]={}

    def __str__(self):
        if self.continue_lesson:
            return f"【连】{self.name}"
        return self.name

    def __eq__(self, other):
        if not isinstance(other,Subject):
            return False
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def get_teacher(self,clas:Class):
        return self.teachers.get(clas.name)

    def get_time_num(self,time:Time):
        return self.time_list[time]

    def add_lesson(self,clas:Class,time:Time):
        self.time_list[time]+=1
        if time in self.timetable:
            self.timetable[time].append(clas)
        else:
            self.timetable[time]=[clas]

    def remove_lesson(self,clas:Class,time:Time):
        self.time_list[time]-=1
        self.timetable[time].remove(clas)

    def to_continue_lesson(self):
        subject2=copy.copy(self)
        subject2.continue_lesson=True
        return subject2

    def to_normal_lesson(self):
        subject2=copy.copy(self)
        subject2.continue_lesson=False
        return subject2

class Class:
    def __init__(self,name,teachers:dict[str,Teacher]):
        """
        初始化班级对象

        :param name: 班级名称
        :param teachers: 班级任课教师列表({学科:老师})
        """
        self.name=name
        self.teachers=teachers
        self.timetable:dict[Time,list[Subject]]={}
        self.left_subjects:list[Subject]=[]

    def __str__(self):
        return self.name

    def get_teacher(self,subject:Subject):
        return self.teachers[subject.name]

    def get_subject_num(self,subject:Subject)->int:
        return self.left_subjects.count(subject)

    def add_lesson(self,time:Time,subject:Subject):
        logging.debug(f"在 {self.name} 的 {time} 安排 {subject}")
        subject.get_teacher(self).add_lesson(time,self,subject)
        time=time.all_week
        if time in self.timetable:
            self.timetable[time].append(subject)
        else:
            self.timetable[time]=[subject]
        subject.add_lesson(self,time)
        self.left_subjects.remove(subject)

    def remove_lesson(self,time:Time,subject:Subject):
        subjects=self.timetable.get(time.all_week)
        if subjects:
            logging.debug(f"删除 {self} {time} 的 {subject}")
            subject.get_teacher(self).remove_lesson(time)
            time=time.all_week
            self.timetable[time].remove(subject)
            subject.remove_lesson(self,time)
            self.left_subjects.append(subject)

    def get_lessons(self,time:Time)->list[Subject]|None:
        return self.timetable.get(time)

    @property
    def timetable_dataframe(self)->pd.DataFrame:
        data=copy.deepcopy(table_style())
        for time,subjects in self.timetable.items():
            if len(subjects)==1:
                subject=subjects[0]
                data.loc[time.to_str(False,True),time.to_str(True,False)]=str(subject)
                if cfg.show_teachers.value:
                    data.loc[time.to_str(False,True),time.to_str(True,False)]+=f"\n{subject.get_teacher(self)}"
            else:
                data.loc[time.to_str(False,True),time.to_str(True,False)]=f"【单】{subjects[0]}/"
                data.loc[time.to_str(False,True),time.to_str(True,False)]+=f"【双】{subjects[1]}"
                if cfg.show_teachers.value:
                    data.loc[time.to_str(False,True),time.to_str(True,False)]+=f"\n【单】{subjects[0].get_teacher(self)}/"
                    data.loc[time.to_str(False,True),time.to_str(True,False)]+=f"【双】{subjects[1].get_teacher(self)}"
        return data

class Rule_type:
    set_time="set_time"
    avoid_time="avoid_time"
    priority_time="priority_time"
    set_num="set_num"
    avoid_subject="avoid_subject"
    avoid_teacher="avoid_teacher"
    set_continue="set_continue"
    half_num="half_num"

class Rule:
    def __init__(self,**kwargs):
        self.type=kwargs["type"]
        if self.type in [Rule_type.set_time,Rule_type.avoid_time,Rule_type.priority_time]:
            self.time=Time(string=kwargs["time"])
        if self.type in [Rule_type.set_time,Rule_type.avoid_time,Rule_type.priority_time,Rule_type.set_num,Rule_type.set_continue,Rule_type.half_num]:
            self.subject=results.subjects.get(kwargs["subject"])
        if self.type in [Rule_type.set_num]:
            self.number=kwargs["number"]
        if self.type==Rule_type.avoid_subject:
            self.subjectA=results.subjects.get(kwargs["subjectA"])
            self.subjectB=results.subjects.get(kwargs["subjectB"])
        if self.type==Rule_type.avoid_teacher:
            self.teacherA=results.teachers.get(kwargs["teacherA"])
            self.teacherB=results.teachers.get(kwargs["teacherB"])

    def __str__(self):
        ans=cfg.rule_types.value[self.type].replace("|","").replace("{"," ").replace("}"," ")
        for string in self.__dict__:
            if string=="type":
                continue
            ans=ans.replace(string,str(self.__dict__[string]))
        return ans

    def to_dict(self)->dict:
        ans={}
        for string in self.__dict__:
            ans[str(string)]=str(self.__dict__[string])
        return ans

    def __eq__(self, other):
        return self.type==other.type and self.__dict__==other.__dict__

    def __hash__(self):
        return hash(self.__dict__)

# 解析课程信息
class Results:
    def __init__(self):
        self.teachers: dict[str,Teacher]={}
        self.subjects: dict[str,Subject]={}
        self.classes: dict[str,Class]={}
        self.class_names:list[str]=[]
        self.class_lst:list[Class]=[]
        logging.info("正在解析课程信息...")
        lessons=cfg.lessons_info.value
        subjects_str=cfg.subjects_info.value
        for subject in subjects_str:
            self.subjects[subject]=Subject(subject,{})
        for teacher in cfg.teachers_info.value:
            self.teachers[teacher]=Teacher(teacher)
        for clas in lessons:
            class_name=clas["班级"]
            self.classes[class_name]=Class(class_name,{})
            self.class_names=list(self.classes.keys())
            self.class_lst=[self.classes[clas] for clas in self.class_names]
            for subject in subjects_str:
                if clas[subject+" - 任课老师"]:
                    self.subjects[subject].teachers[class_name]=self.teachers[clas[subject+" - 任课老师"]]
                    for i in range(int(clas[subject+" - 课时"])):
                        self.classes[class_name].left_subjects.append(self.subjects[subject])
                    self.classes[class_name].teachers[subject]=self.teachers[clas[subject+" - 任课老师"]]
results=Results()

rules:list[Rule]=[]
priority_subjects:dict[Time,list[Subject]]={}
half_subjects:set[Subject]=set()
continue_subjects:set[Subject]=set()
set_lessons:list[tuple[Time,Subject]]=[]
for rule in cfg.rules.value:
    rule=Rule(**rule)
    rules.append(rule)
    if rule.type==Rule_type.set_time:
        set_lessons.append((rule.time,rule.subject))
    elif rule.type==Rule_type.priority_time:
        if rule.time not in priority_subjects:
            priority_subjects[rule.time]=[rule.subject]
        else:
            priority_subjects[rule.time].append(rule.subject)
    elif rule.type==Rule_type.half_num:
        half_subjects.add(rule.subject)
    elif rule.type==Rule_type.set_continue:
        continue_subjects.add(rule.subject)
logging.info("课程信息解析完毕，生成初始化完成")