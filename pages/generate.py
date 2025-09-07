# 导入必要的模块
import copy
import os
import random

from PyQt5.QtWidgets import QVBoxLayout,QWidget

from locals import *
from style import *

class Teacher:
    """
    教师类，用于管理教师的课程时间
    """
    def __init__(self, name):
        """
        初始化教师对象

        :param name: 教师姓名
        """
        self.name = name
        self.lessons_time = []  # 记录教师已占用的课程时间

    def add_lesson_time(self, day, lesson, week):
        """
        添加教师的课程时间

        :param day: 星期几
        :param lesson: 课程节次
        :param week: 单周/双周/全周
        """
        self.lessons_time.append((day, lesson, week))

    def is_busy(self, day, lesson, week="all"):
        """
        检查教师在特定时间是否有课

        :param day: 星期几
        :param lesson: 课程节次
        :param week: 单周/双周/全周
        :return: 是否有课
        """
        return (day, lesson, week) in self.lessons_time


class Generate(QFrame):
    def add_lesson(self,class_: str,day: int,lesson: int,subject: str,week="all",mode="replace",remove=True) -> bool:
        """
        为指定班级的课程表添加课程

        :param class_: 班级名称
        :param day: 星期几
        :param lesson: 课程节次
        :param subject: 学科
        :param week: 单周/双周/全周
        :param mode: 添加模式（替换/追加）
        :param remove: 是否从可选课程中移除
        :return: 是否成功添加课程
        """

        # 处理星期索引
        day-=1
        # 周类型映射
        week_map={"single":"单 ","double":"双 ","all":""}

        # 获取该课程的任课教师
        teacher=self.dict_lessons[class_][subject+" - 任课老师"]

        # 检查教师是否有空，以及课程是否在可选课程中
        if self.teachers[teacher].is_busy(day,lesson) or subject not in self.class_subjects:
            return False

        # 获取课程时间描述
        time=generate_time(lesson)

        # 根据模式添加课程
        if mode=="replace":
            table[day][time]=week_map[week]+subject
        else:
            table[day][time]+="\n"+week_map[week]+subject

        # 如果设置显示教师，则添加教师姓名
        if self.cfg.show_teachers.value:
            table[day][time]+="\n（%s）"%teacher

        # 记录教师课程时间
        self.teachers[teacher].add_lesson_time(day,lesson,week)

        # 从可选课程中移除（如果需要）
        if subject in self.class_subjects and remove:
            self.class_subjects.remove(subject)

        return True

    def generate_curriculum(self):
        global class_,table
        for class_ in self.dict_lessons:
            continue_loop = True
            old_teachers = copy.deepcopy(self.teachers)

            # 尝试生成课程表，如果失败则重试
            while continue_loop:
                continue_loop = False
                self.teachers = copy.deepcopy(old_teachers)
                table = copy.deepcopy(self.table_style)
                self.class_subjects = []
                special_subjects = []
                already_added = []

                # 处理课程信息
                for subject in self.subjects:
                    if not self.dict_lessons[class_][subject + " - 课时"] is None:
                        if subject.endswith("(0.5)") or subject.endswith("（0.5）"):
                            special_subjects.append(subject)
                        else:
                            for i in range(int(float(self.dict_lessons[class_][subject + " - 课时"]))):
                                self.class_subjects.append(subject)

                # 处理0.5课时科目
                if len(special_subjects) > 0:
                    self.class_subjects.append(special_subjects)

                # 处理优先级配置
                for subject in self.cfg.priority.value:
                    if not subject["enabled"]:
                        continue
                    for priority in range(1, len(subject) - 2):
                        day = subject[str(priority)][0]
                        lesson = subject[str(priority)][1]
                        if day and lesson:
                            if self.add_lesson(class_, day, lesson, subject["subject"]):
                                already_added.append((day,lesson))

                # 生成课程表
                for day in range(1,6):

                    # 填充剩余课程
                    for lesson in range(1, self.cfg.morning_class_num.value + self.cfg.afternoon_class_num.value + 1):
                        if (day,lesson) in already_added:
                            continue

                        # st.table(pd.DataFrame(table).transpose())  # debug
                        subject = random.choice(self.class_subjects)

                        # 处理0.5课时科目
                        if type(subject) == list:
                            successful = (self.add_lesson(class_, day, lesson, subject[0], "single") and
                                          self.add_lesson(class_, day, lesson, subject[1], "double", "append")) or \
                                         (self.add_lesson(class_, day, lesson, subject[0], "double") and
                                          self.add_lesson(class_, day, lesson, subject[1], "single", "append"))
                            if successful:
                                self.class_subjects.remove(subject)
                        else:
                            successful = self.add_lesson(class_, day, lesson, subject)

                        # 如果添加失败，重试
                        tries = 0
                        while not successful:
                            subject = random.choice(self.class_subjects)
                            if type(subject) == list:
                                successful = (self.add_lesson(class_, day, lesson, subject[0], "single") and
                                              self.add_lesson(class_, day, lesson, subject[1], "double", "append")) or \
                                             (self.add_lesson(class_, day, lesson, subject[0], "double") and
                                              self.add_lesson(class_, day, lesson, subject[1], "single", "append"))
                                if successful:
                                    self.class_subjects.remove(subject)
                            else:
                                successful = self.add_lesson(class_, day, lesson, subject)

                            tries += 1
                            if tries >= 100:
                                continue_loop = True
                                break

                        if continue_loop:
                            break

                    if continue_loop:
                        break

        # 显示课程表
        subheader(class_ + "课程表",self,self.layout)
        if self.cfg.lessons_info.value:
            table = pd.DataFrame(table)
        else:
            table = pd.DataFrame(table).transpose()
        table_widget=TableWidget()
        display_df_in_table(table_widget, table)
        add_widget(table_widget,self.layout)

        self.class_tables[class_] = table

        # 保存课程表
        if not os.path.exists("output"):
            os.mkdir("output")

        # 保存到Excel文件
        with pd.ExcelWriter("课程表.xlsx") as writer:
            for class_, table in self.class_tables.items():
                table.to_excel(writer, sheet_name=class_, index=not self.cfg.transpose.value)
                table.to_excel(f"output/{class_}.xlsx", index=not self.cfg.transpose.value)

        # 压缩课程表文件
        # zip_buffer = BytesIO()
        # with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
        #     for class_, table in self.class_tables.items():
        #         excel_file_path = f"output/{class_}.xlsx"
        #         zipf.write(excel_file_path, arcname=os.path.basename(excel_file_path))
        #
        # # 提供下载按钮
        # col1, col2 = st.columns([1, 3])
        # with col1:
        #     st.download_button(
        #         "保存在一个文件中",
        #         open("课程表.xlsx", "rb"),
        #         file_name="课程表.xlsx",
        #         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        #     )
        # with col2:
        #     st.download_button(
        #         "保存为多个文件",
        #         zip_buffer.getvalue(),
        #         file_name="课程表.zip",
        #         mime="application/zip"
        #     )

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

        self.title = title("生成",self,self.layout)
        # 读取配置文件
        self.cfg=load_settings()
        # 检查是否已配置课程信息
        if not self.cfg.lessons_info.value:
            save_settings(self,False,"请先在设置中配置课程信息")

        # 解析课程信息
        lessons = self.cfg.lessons_info.value
        self.dict_lessons = {}
        for i in range(len(lessons)):
            self.dict_lessons[lessons[i]["班级"]] = lessons[i]

        # 创建课程表基础样式
        pd_lessons = pd.DataFrame(lessons)
        self.table_style = []

        for day in range(5):
            self.table_style.append({"星期": days[day+1]})
            for time in range(1, self.cfg.morning_class_num.value + 1):
                self.table_style[day].update({f"上午第{time}节": None})
            for time in range(1, self.cfg.afternoon_class_num.value + 1):
                self.table_style[day].update({f"下午第{time}节": None})

        self.subjects = self.cfg.subjects_info.value

        # 初始化教师字典
        self.class_tables = {}
        self.teachers = {lessons[class_][subject + " - 任课老师"]: Teacher(lessons[class_][subject + " - 任课老师"])
                    for class_ in range(len(lessons)) for subject in self.subjects}

        # 生成课程表按钮
        generate_button=button("生成课程表",self,self.layout)
        generate_button.setFixedSize(130,40)
        generate_button.clicked.connect(self.generate_curriculum)
        add_widget(generate_button,self.layout)

        # === 设置滚动区域内容 ===
        self.layout.addStretch(1)
        scroll_area.setWidget(view)
        main_layout.addWidget(scroll_area)