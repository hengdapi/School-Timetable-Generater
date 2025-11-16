from __future__ import annotations
import copy,random
import time
import traceback

from PyQt5.QtCore import QThread,QTimer
from PyQt5.QtWidgets import QVBoxLayout,QWidget
from locals import *
from style import *

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
        self.lessons_time:dict[Time,Subject]={}  # 记录教师已占用的课程时间

    def __str__(self):
        return self.name

    def add_lesson(self,time:Time,subject:Subject):
        """
        添加教师的课程时间
        """
        self.lessons_time[time]=subject

    def is_busy(self,time:Time):
        """
        检查教师在特定时间是否有课
        :return: 是否有课
        """
        return time in self.lessons_time

    def remove_lesson(self,time:Time):
        """
        移除教师在特定时间上的课程
        """
        self.lessons_time.pop(time)

    def get_lesson(self,time:Time):
        return self.lessons_time.get(time)

class Timetable:
    def __init__(self,clas,timetable:pd.DataFrame):
        self.clas=clas
        self.data=timetable

    def add_lesson(self,time:Time,subject:Subject):
        self.data.loc[time.to_str(False,True),time.day-1]=subject.name
        if cfg.show_teachers.value:
            self.data.loc[time.to_str(False,True),time.day-1]+="\n("+subject.get_teacher(self.clas).name+")"
        subject.get_teacher(self.clas).add_lesson(time,subject)
        subject.add_lesson(time,self.clas)

    def remove_lesson(self,time:Time):
        subject=self.get_lesson(time)
        if subject:
            self.data.loc[time.to_str(False,True),time.day-1]=""
            subject.get_teacher(self.clas).remove_lesson(time)
            subject.remove_lesson(time,self.clas)

    def get_lesson(self,time:Time)->Subject|None:
        try:
            lesson:str|None=self.data.loc[time.to_str(False,True),str(time.day-1)]
        except BaseException:
            lesson:str|None=self.data.loc[time.to_str(False,True),time.day-1]
        if lesson:
            return subjects.get(lesson.split("\n")[0])
        else:
            return None

class Subject:
    def __init__(self, name:str, teachers:dict[str,Teacher],nums:dict[str,int]):
        """
        初始化课程对象

        :param name: 课程名称
        :param teachers: 课程任课教师列表({班级:老师})
        :param nums: 课程课时列表({班级:课时})
        """
        self.name = name
        self.teachers = teachers
        self.nums = nums
        self.time_list:dict[Time,int]={Time(day,lesson):0 for day in range(1,6) for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)}

    def __str__(self):
        return self.name

    def get_teacher(self,clas:Class):
        return self.teachers.get(clas.name)

    def get_num(self,clas:Class):
        if self.nums.get(clas.name):
            return self.nums.get(clas.name)
        return 0

    def get_time_num(self,time:Time):
        return self.time_list[time]

    def add_lesson(self,time:Time,clas:Class):
        self.time_list[time]+=1
        self.nums[clas.name]-=1

    def remove_lesson(self,time:Time,clas:Class):
        self.time_list[time]-=1
        self.nums[clas.name]+=1

class Class:
    def __init__(self,name,teachers:dict[str,Teacher],timetable:Timetable):
        """
        初始化班级对象

        :param name: 班级名称
        :param teachers: 班级任课教师列表({学科:老师})
        :param timetable: 班级课程表
        """
        self.name = name
        self.teachers = teachers
        self.timetable = timetable
        self.subject_times:dict[Subject,int]={}
        for subject in subjects.values():
            self.subject_times[subject]=0

    def __str__(self):
        return self.name

    def get_teacher(self,subject:Subject):
        return self.teachers[subject.name]

    @property
    def subjects(self)->list:
        return list(self.subject_times.keys())

def check(clas:Class,time:Time,subject:Subject)->bool:
    try:
        logging.debug(f"检查能否在 {clas.name} 的 {time.string} 安排 {subject.name}")
        if subject.get_teacher(clas).is_busy(time):
            logging.debug(f"{subject.name} 的任课老师 {subject.get_teacher(clas).name} 在 {time.string} 有课")
            return False
        if not subject.get_num(clas):
            logging.debug(f"{clas.name} 的 {subject.name} 已经排完课了")
            return False
        for rule in rules:
            # 不能排在指定时间
            if rule["type"]=="avoid_time":
                # 支持只写节次（如“上午第4节”）
                if rule["subject"]==subject.name and (time.string==rule["time"] or lesson_to_str(time.lesson)==rule["time"]):
                    logging.debug(f"{clas.name} 不能在 {time.string} 排 {subject.name}")
                    return False
            # 同一时间最多排几节课
            elif rule["type"]=="set_num":
                if rule["subject"]==subject.name and subject.get_time_num(time)>=int(rule["number"]):
                    return False
            # 学科不能与另一学科同一时间
            elif rule["type"]=="avoid_subject":
                clas = None
                for c in classes.values():
                    if c.timetable.get_lesson(time) == rule.get("subjectB"):
                        clas = c
                        break
                if subject.name==rule["subjectA"] and clas is not None:
                    return False
            # 老师不能与另一老师同一时间有课
            elif rule["type"]=="avoid_teacher":
                teacherA = rule["teacherA"]
                teacherB = rule["teacherB"]
                for c in classes.values():
                    lesson = c.timetable.get_lesson(time)
                    if lesson:
                        tname = lesson.get_teacher(c).name
                        if (subject.get_teacher(c).name==teacherA and tname==teacherB) or \
                           (subject.get_teacher(c).name==teacherB and tname==teacherA):
                            return False
        return True
    except Exception as e:
        logging.error(f"检查时出错：{e}")
        return False

teachers: dict[str,Teacher]={}
subjects: dict[str,Subject]={}
classes: dict[str,Class]={}
timetables: dict[str,Timetable]={}
rules=cfg.rules.value
priority_times:dict[Time,list[Subject]]={}
class_names:list[str]=[]
class_lst:list[Class]=[]

class Generate_thread(QThread):
    finished_signal=pyqtSignal(bool)  # 生成成功或失败
    progress_signal=pyqtSignal(int)  # 进度信息
    log_signal=pyqtSignal(str)

    def __init__(self,parent=None):
        super().__init__(parent)

    def run(self):
        """
        在新线程中执行的任务
        注意：不要在这里直接操作GUI组件
        """
        try:
            # 执行耗时的课程表生成逻辑
            self.generate_timetable()
            # 发送完成信号
            self.finished_signal.emit(True)
        except Exception as e:
            self.finished_signal.emit(False)

    def generate_timetable(self):
        try:
            logging.info("开始生成课程表...")
            # 1. 固定时间优先分配
            logging.debug("填充固定时间")
            for rule in rules:
                if rule["type"]=="set_time":
                    for timetable in timetables.values():
                        timetable.add_lesson(Time(string=rule["time"]),subjects[rule["subject"]])

            # 2. 自动分配剩余课程
            logging.debug("开始dfs分配剩余课程")
            self.finish=False
            self.dfs(class_lst[0],Time(1,1))
        except Exception as e:
            logging.critical(f"生成课程表时错误：{e}")

    def dfs(self,clas: Class,curr_time: Time):
        try:
            self.progress_signal.emit(class_names.index(clas.name))
            logging.debug(f"当前班级：{clas.name}，当前时间：{curr_time.string}")
            self.log_signal.emit(f"当前班级：{clas.name}，当前时间：{curr_time.string}")
            timetable=clas.timetable
            next_time=copy.deepcopy(curr_time)
            if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                if class_names[-1]==clas.name:
                    self.finished_signal.emit(True)
                    self.finish=True
                    return
            elif curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                next_time.day+=1
                next_time.lesson=1
            else:
                next_time.lesson+=1
            logging.debug(f"计算下一时间：{next_time.string}")

            if not timetable.get_lesson(curr_time):
                if curr_time in priority_times:
                    random.shuffle(priority_times[curr_time])
                    logging.debug(f"随机打乱优先课程：{[sub.name for sub in priority_times[curr_time]]}")
                    for subject in priority_times[curr_time]:
                        if check(timetable.clas,curr_time,subject):
                            timetable.add_lesson(curr_time,subject)
                            logging.debug(f"在{curr_time.string}分配{subject.name}")
                            if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                                self.dfs(class_lst[class_names.index(clas.name)+1],Time(1,1))
                            else:
                                self.dfs(clas,next_time)
                            if self.finish:
                                return
                            logging.debug(f"删除{curr_time.string}的{subject.name}")
                            timetable.remove_lesson(curr_time)
                random_subjects=clas.subjects
                random.shuffle(random_subjects)
                for subject in random_subjects:
                    if check(timetable.clas,curr_time,subject):
                        timetable.add_lesson(curr_time,subject)
                        if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                            self.dfs(class_lst[class_names.index(clas.name)+1],Time(1,1))
                        else:
                            self.dfs(clas,next_time)
                        if self.finish:
                            return
                        timetable.remove_lesson(curr_time)
            else:
                logging.debug(f"{curr_time.string}已存在课程")
                if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                    self.dfs(class_lst[class_names.index(clas.name)+1],Time(1,1))
                else:
                    self.dfs(clas,next_time)
        except Exception as e:
            err=traceback.format_exc()
            logging.critical(f"生成课程表出错：{err}")

class Generate(QFrame):
    def __init__(self,parent=None):

        super().__init__(parent=parent)
        self.setObjectName("Generate")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20,20,0,0)

        # === 创建可滚动区域 ===
        scroll_area=SingleDirectionScrollArea(orient=Qt.Vertical)
        scroll_area.setStyleSheet("QScrollArea{background: transparent; border: none}")
        scroll_area.setWidgetResizable(True)

        # === 创建内容容器 ===
        view=QWidget()
        view.setStyleSheet("QWidget{background: transparent}")
        self.layout = QVBoxLayout(view)

        self.title = title("生成",self,self.layout,0)
        # 读取配置文件
        self.cfg=load_settings()
        # 检查是否已配置课程信息
        if not self.cfg.lessons_info.value:
            save_settings(self,False,"请先在设置中配置课程信息")

        table_style=[]

        for day in range(5):
            table_style.append({"星期":days[day+1]})
            for time in range(1,self.cfg.morning_class_num.value+1):
                table_style[day].update({f"上午第{time}节":None})
            for time in range(1,self.cfg.afternoon_class_num.value+1):
                table_style[day].update({f"下午第{time}节":None})
        table_style=pd.DataFrame(table_style).transpose()
        # 解析课程信息
        logging.info("正在解析课程信息...")
        lessons = self.cfg.lessons_info.value
        subjects_str=self.cfg.subjects_info.value
        for subject in subjects_str:
            subjects[subject]=Subject(subject,{},{})
        for teacher in self.cfg.teachers_info.value:
            teachers[teacher]=Teacher(teacher)
        global class_names,class_lst
        for clas in lessons:
            class_name=clas["班级"]
            timetables[class_name]=Timetable(class_name,copy.deepcopy(table_style))
            classes[class_name]=Class(class_name,{},timetables[class_name])
            timetables[class_name].clas=classes[class_name]
            class_names=list(classes.keys())
            class_lst=[classes[clas] for clas in class_names]
            for subject in subjects_str:
                if clas[subject+" - 任课老师"]:
                    subjects[subject].teachers[class_name]=teachers[clas[subject+" - 任课老师"]]
                    subjects[subject].nums[class_name]=int(clas[subject+" - 课时"])
                    classes[class_name].teachers[subject]=teachers[clas[subject+" - 任课老师"]]
        for rule in rules:
            if rule["type"]=="priority_time":
                curr_time=Time(string=rule["time"])
                if curr_time not in priority_times:
                    priority_times[curr_time]=[subjects[rule["subject"]]]
                else:
                    priority_times[curr_time].append(subjects[rule["subject"]])
        logging.info("课程信息解析完毕")

        # 生成课程表按钮
        self.generate_button=button("生成课程表",self,self.layout)
        self.generate_button.setFixedSize(130,40)
        self.generate_button.clicked.connect(self.generate_timetable)
        add_widget(self.generate_button,self.layout)

        # 课程表预览
        self.class_combo=ComboBox(self)
        self.class_combo.addItems(class_names)
        self.class_combo.setVisible(False)
        self.class_combo.currentIndexChanged.connect(self.show_timetable)
        add_widget(self.class_combo,self.layout)

        self.timetable_preview=TableWidget()
        self.timetable_preview.setVisible(False)
        self.timetable_preview.setFixedHeight(400)
        add_widget(self.timetable_preview,self.layout)

        self.progress_bar=ProgressBar()
        self.progress_bar.setVisible(False)
        add_widget(self.progress_bar,self.layout,0)

        self.log_label:QLabel=write("",self,self.layout)
        self.log_label.setVisible(False)
        add_widget(self.log_label,self.layout)


        # === 设置滚动区域内容 ===
        self.layout.addStretch(1)
        scroll_area.setWidget(view)
        main_layout.addWidget(scroll_area)

    def generate_timetable(self):
        try:
            logging.info("生成按钮被点击")
            # 禁用生成按钮防止重复点击
            self.generate_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(len(class_names))
            self.log_label.setVisible(True)

            # 创建并启动线程
            self.generate_thread=Generate_thread()
            self.generate_thread.finished_signal.connect(self.on_generation_finished)
            self.generate_thread.progress_signal.connect(self.on_progress_update)
            self.generate_thread.log_signal.connect(self.on_log_update)
            self.generate_thread.start()
        except Exception as e:
            logging.critical(f"生成课程表出错：{e}")

    def show_timetable(self):
        display_df_in_table(self.timetable_preview,timetables[self.class_combo.currentText()].data)
        # 手动设置行高
        for row in range(1,self.timetable_preview.rowCount()):
            self.timetable_preview.setRowHeight(row, 50)
        # 手动设置列宽
        for col in range(self.timetable_preview.columnCount()):
            self.timetable_preview.setColumnWidth(col, 120)

    def on_generation_finished(self):
        logging.info("排课已完成")
        self.log_label.setVisible(False)
        self.progress_bar.setVisible(False)
        self.generate_button.setVisible(False)
        self.class_combo.setVisible(True)
        self.show_timetable()
        self.timetable_preview.setVisible(True)

    def on_progress_update(self,progress):
        try:
            self.progress_bar.setValue(progress)
        except Exception as e:
            logging.critical(f"生成课程表出错：{e}")

    def on_log_update(self,log):
        self.log_label.setText(log)