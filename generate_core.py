from __future__ import annotations

import copy
import random
import traceback
from locals import *
from PyQt5.QtCore import QThread,pyqtSignal

table_style={}
for day in days[1:]:
    table_style[day]={}
    for lesson in range(1,cfg.morning_class_num.value+1):
        table_style[day][f"上午第{lesson}节"]=None
    for lesson in range(1,cfg.afternoon_class_num.value+1):
        table_style[day][f"下午第{lesson}节"]=None
table_style=pd.DataFrame(table_style)

class_total_timetable:dict[Class,dict[Time,Subject]]={}
teacher_total_timetable:dict[Teacher,dict[Time,tuple[Class,Subject]]]={}
def class_total_dataframe()->pd.DataFrame:
    data={}
    for clas,lesson in class_total_timetable.items():
        data[clas.name]={}
        for time,subject in lesson.items():
            data[clas.name][time.string]=subject.name
            if cfg.show_teachers:
                data[clas.name][time.string]+=f"\n({subject.get_teacher(clas).name})"
    return pd.DataFrame(data).transpose()

def teacher_total_dataframe()->pd.DataFrame:
    data={}
    for teacher,lesson in teacher_total_timetable.items():
        data[teacher.name]={}
        for time,lesson2 in lesson.items():
            data[teacher.name][time.string]=lesson2[0].name+"\n"+lesson2[1].name
    dataframe=pd.DataFrame(data).transpose()
    dataframe=dataframe[[Time(day,lesson).string for day in range(1,6) for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)]]
    return dataframe

class Time:
    def __init__(self,day:int=0,lesson:int=0,string:str=None):
        if string:
            self.day=days.index(string[:3])
            self.lesson=int(string[6:-1])
            if "下午" in string:
                self.lesson+=cfg.morning_class_num.value
        else:
            self.day=day
            self.lesson=lesson

    def __eq__(self, other):
        return self.day==other.day and self.lesson==other.lesson
    def __hash__(self):
        return hash((self.day,self.lesson))
    def __str__(self):
        return self.string

    def to_str(self,day:bool,lesson:bool):
        string=""
        if day and self.day:
            string=days[self.day]
        if lesson and self.lesson:
            string+=lesson_to_str(self.lesson)
        return string

    @property
    def string(self):
        return days[self.day]+lesson_to_str(self.lesson)

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

    def __hash__(self):
        return hash(self.name)

    def add_lesson(self,time:Time,clas:Class,subject:Subject):
        """
        添加教师的课程时间
        """
        global teacher_total_timetable
        self.timetable[time]=(clas,subject)
        if self in teacher_total_timetable:
            teacher_total_timetable[self][time]=(clas,subject)
        else:
            teacher_total_timetable[self]={time:(clas,subject)}

    def is_busy(self,time:Time):
        """
        检查教师在特定时间是否有课
        :return: 是否有课
        """
        return time in self.timetable

    def remove_lesson(self,time:Time):
        """
        移除教师在特定时间上的课程
        """
        global teacher_total_timetable
        self.timetable.pop(time)
        teacher_total_timetable[self].pop(time)

    @property
    def timetable_dataframe(self)->pd.DataFrame:
        data=copy.deepcopy(table_style)
        for time,lesson in self.timetable.items():
            data.loc[time.to_str(False,True),time.to_str(True,False)]=lesson[1].name+"\n"+lesson[0].name
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
        self.time_list:dict[Time,int]={Time(day,lesson):0 for day in range(1,6) for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)}

    def __str__(self):
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

    def add_lesson(self,time:Time):
        self.time_list[time]+=1

    def remove_lesson(self,time:Time):
        self.time_list[time]-=1

class Class:
    def __init__(self,name,teachers:dict[str,Teacher]):
        """
        初始化班级对象

        :param name: 班级名称
        :param teachers: 班级任课教师列表({学科:老师})
        """
        self.name=name
        self.teachers=teachers
        self.timetable:dict[Time,Subject]={}
        self.left_subjects:list[Subject]=[]

    def __str__(self):
        return self.name

    def get_teacher(self,subject:Subject):
        return self.teachers[subject.name]

    def get_subject_num(self,subject:Subject)->int:
        return self.left_subjects.count(subject)

    def add_lesson(self,time:Time,subject:Subject):
        global class_total_timetable
        self.timetable[time]=subject
        subject.get_teacher(self).add_lesson(time,self,subject)
        subject.add_lesson(time)
        self.left_subjects.remove(subject)
        if self in class_total_timetable:
            class_total_timetable[self][time]=subject
        else:
            class_total_timetable[self]={time:subject}

    def remove_lesson(self,time:Time):
        subject=self.timetable.get(time)
        if subject:
            global class_total_timetable
            self.timetable.pop(time)
            subject.get_teacher(self).remove_lesson(time)
            subject.remove_lesson(time)
            self.left_subjects.append(subject)
            class_total_timetable[self].pop(time)

    def get_lesson(self,time:Time)->Subject|None:
        return self.timetable.get(time)

    @property
    def timetable_dataframe(self)->pd.DataFrame:
        data=copy.deepcopy(table_style)
        for time,subject in self.timetable.items():
            data.loc[time.to_str(False,True),time.to_str(True,False)]=subject.name
            if cfg.show_teachers.value:
                data.loc[time.to_str(False,True),time.to_str(True,False)]+="\n("+subject.get_teacher(self).name+")"
        return data

def check(clas: Class,time: Time,subject: Subject) -> bool:
    try:
        logging.debug(f"检查能否在 {clas.name} 的 {time.string} 安排 {subject.name}")
        if subject.get_teacher(clas).is_busy(time):
            logging.debug(f"{subject.name} 的任课老师 {subject.get_teacher(clas).name} 在 {time.string} 有课")
            return False
        if clas.get_subject_num(subject)==0:
            logging.debug(f"{clas.name} 的 {subject.name} 已经排完课了")
            return False
        for rule in rules:
            # 不能排在指定时间
            if rule["type"]=="avoid_time":
                # 支持只写节次（如"上午第4节"）
                if rule["subject"]==subject.name and (time.string==rule["lesson"] or lesson_to_str(time.lesson)==rule["lesson"]):
                    logging.debug(f"{clas.name} 不能在 {time.string} 排 {subject.name}")
                    return False
            # 同一时间最多排几节课
            elif rule["type"]=="set_num":
                if rule["subject"]==subject.name and subject.get_time_num(time)>=int(rule["number"]):
                    logging.debug(f"{clas.name} 同一时间 最多排 {rule['number']} 节课")
                    return False
            # 学科不能与另一学科同一时间
            elif rule["type"]=="avoid_subject":
                if subject.name==rule["subjectA"]:
                    for c in class_lst:
                        if c.get_lesson(time) == subjects.get(rule.get("subjectB")):
                            logging.debug(f"{c.name} 已经在 {time.string} 安排了会引起冲突的 {rule['subjectB']}")
                            return False
            # 老师不能与另一老师同一时间有课
            elif rule["type"]=="avoid_teacher":
                teacherA = rule["teacherA"]
                teacherB = rule["teacherB"]
                for c in class_lst:
                    if subject.get_teacher(c) is None:
                        continue
                    lesson = c.get_lesson(time)
                    if lesson:
                        tname = lesson.get_teacher(c).name
                        if (subject.get_teacher(c).name==teacherA and tname==teacherB) or \
                           (subject.get_teacher(c).name==teacherB and tname==teacherA):
                            logging.debug(f"{c.name} {subject.name} 的教师 {subject.get_teacher(c).name} 和 {tname} 在 {time.string} 都有课")
                            return False
        logging.debug("可以安排")
        return True
    except:
        e=traceback.format_exc()
        logging.error(f"检查时出错：\n{e}")
        return False

teachers: dict[str,Teacher]={}
subjects: dict[str,Subject]={}
classes: dict[str,Class]={}
rules=cfg.rules.value
priority_subjects:dict[Time,list[Subject]]={}
class_names:list[str]=[]
class_lst:list[Class]=[]

class Generate_thread(QThread):
    finished_signal=pyqtSignal(bool)  # 生成成功或失败
    progress_signal=pyqtSignal(tuple)  # 进度信息

    def __init__(self,parent=None):
        super().__init__(parent)

    def run(self):
        # 执行耗时的课程表生成逻辑
        try:
            global teachers,subjects,classes,rules,priority_subjects,class_names,class_lst
            # 解析课程信息
            teachers.clear()
            subjects.clear()
            classes.clear()
            priority_subjects.clear()
            class_names.clear()
            class_lst.clear()
            logging.info("正在解析课程信息...")
            lessons=cfg.lessons_info.value
            subjects_str=cfg.subjects_info.value
            for subject in subjects_str:
                subjects[subject]=Subject(subject,{})
            for teacher in cfg.teachers_info.value:
                teachers[teacher]=Teacher(teacher)
            for clas in lessons:
                class_name=clas["班级"]
                classes[class_name]=Class(class_name,{})
                class_names=list(classes.keys())
                class_lst=[classes[clas] for clas in class_names]
                for subject in subjects_str:
                    if clas[subject+" - 任课老师"]:
                        subjects[subject].teachers[class_name]=teachers[clas[subject+" - 任课老师"]]
                        for i in range(int(clas[subject+" - 课时"])):
                            classes[class_name].left_subjects.append(subjects[subject])
                        classes[class_name].teachers[subject]=teachers[clas[subject+" - 任课老师"]]
            for rule in rules:
                if rule["type"]=="priority_time":
                    curr_time=Time(string=rule["time"])
                    if curr_time not in priority_subjects:
                        priority_subjects[curr_time]=[subjects[rule["subject"]]]
                    else:
                        priority_subjects[curr_time].append(subjects[rule["subject"]])
            logging.info("课程信息解析完毕，生成初始化完成")

            logging.info("开始生成课程表...")
            # 1. 固定时间优先分配
            logging.debug("填充固定时间")
            for rule in rules:
                if rule["type"]=="set_time":
                    for clas in class_lst:
                        clas.add_lesson(Time(string=rule["time"]),subjects[rule["subject"]])

            # 2. 自动分配剩余课程
            logging.debug("开始dfs分配剩余课程")
            self.finish=False
            self.dfs(class_lst[0],Time(1,1))
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表时错误：\n{e}")
        finally:
            self.finished_signal.emit(True)

    def dfs(self,clas: Class,curr_time: Time):
        try:
            if self.finish:
                return
            self.progress_signal.emit((clas,curr_time))
            next_time=copy.deepcopy(curr_time)
            last=False
            if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                if class_names[-1]==clas.name:
                    last=True
            elif curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                next_time.day+=1
                next_time.lesson=1
            else:
                next_time.lesson+=1
            logging.debug(f"计算下一时间：{next_time.string}")

            if not clas.get_lesson(curr_time):
                if curr_time in priority_subjects:
                    curr_priority=priority_subjects[curr_time]
                else:
                    curr_priority=[]
                logging.debug(f"当前优先课程：{[i.name for i in curr_priority]}")

                curr_subjects=list(set(clas.left_subjects))
                random.shuffle(curr_subjects)
                for subject in curr_subjects:
                    if subject in curr_priority:
                        curr_subjects.remove(subject)
                        curr_subjects.insert(0,subject)

                logging.debug(f"当前课程：{[i.name for i in curr_subjects]}")

                for subject in curr_subjects:
                    if check(clas, curr_time, subject):
                        logging.debug(f"在{curr_time.string}分配{subject.name}")
                        clas.add_lesson(curr_time,subject)
                        if not last:
                            if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                                self.dfs(class_lst[class_names.index(clas.name)+1],Time(1,1))
                            else:
                                self.dfs(clas,next_time)
                            if self.finish:
                                return
                            logging.debug(f"删除{curr_time.string}的{subject.name}")
                            clas.remove_lesson(curr_time)
            else:
                logging.debug(f"{curr_time.string}已存在课程")
                if not last:
                    if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                        self.dfs(class_lst[class_names.index(clas.name)+1],Time(1,1))
                    else:
                        self.dfs(clas,next_time)
            if last and bool(clas.get_lesson(curr_time)):
                self.finished_signal.emit(True)
                self.finish=True
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表出错：\n{e}")

def generate_timetable(window):
    generate_thread=Generate_thread()
    generate_thread.finished_signal.connect(window.on_generation_finished)
    generate_thread.progress_signal.connect(window.on_progress_update)
    generate_thread.start()