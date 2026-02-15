from style import *
from generate_core import *
import time

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

        # 解析课程信息
        global teachers,subjects,classes,class_names,class_lst
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

        # 生成课程表按钮
        self.generate_button=button("生成课程表",self,self.layout)
        self.generate_button.setFixedSize(130,40)
        self.generate_button.clicked.connect(self.generate_timetable)
        add_widget(self.generate_button,self.layout,10)

        # 课程表预览
        self.preview_layout=QHBoxLayout()
        self.layout.addLayout(self.preview_layout)
        self.preview_mode=ComboBox(self)
        self.preview_mode.addItems(["按班级查看","按教师查看","查看全部班级","查看全部教师"])
        self.preview_mode.currentIndexChanged.connect(self.change_mode)
        self.preview_mode.setVisible(False)
        add_widget(self.preview_mode,self.preview_layout)

        self.preview_object=EditableComboBox(self)
        self.preview_object.addItems(class_names)
        self.preview_object.setCompleter(QCompleter(class_names,self.preview_object))
        self.preview_object.setVisible(False)
        self.preview_object.currentIndexChanged.connect(self.show_timetable)
        add_widget(self.preview_object,self.preview_layout,0)

        self.timetable_preview=TableWidget()
        self.timetable_preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.timetable_preview.setVisible(False)
        add_widget(self.timetable_preview,self.layout,0)

        self.progress_bar=ProgressBar()
        self.progress_bar.setVisible(False)
        add_widget(self.progress_bar,self.layout,0)

        self.log_label:QLabel=write("",self,self.layout)
        self.log_label.setVisible(False)
        add_widget(self.log_label,self.layout,0)


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
            self.preview_mode.setVisible(False)
            self.preview_object.setVisible(False)
            self.timetable_preview.setVisible(False)

            # 创建并启动线程
            self.generate_start_time=time.time()
            self.generate_thread=Generate_thread()
            self.generate_thread.finished_signal.connect(self.on_generation_finished)
            self.generate_thread.progress_signal.connect(self.on_progress_update)
            self.generate_thread.start()
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表出错：\n{e}")

    def change_mode(self):
        self.preview_object.clear()
        if self.preview_mode.currentIndex()==0:
            items=class_names
            self.preview_object.setEnabled(True)
        elif self.preview_mode.currentIndex()==1:
            items=list(teachers.keys())
            self.preview_object.setEnabled(True)
        elif self.preview_mode.currentIndex()==2:
            items=[]
            self.show_timetable()
            self.preview_object.setEnabled(False)
        elif self.preview_mode.currentIndex()==3:
            items=[]
            self.show_timetable()
            self.preview_object.setEnabled(False)
        self.preview_object.addItems(items)
        self.preview_object.setCompleter(QCompleter(items,self.preview_object))

    def show_timetable(self):
        self.timetable_preview.clear()
        if self.preview_mode.currentIndex()==0:
            display_df_in_table(self.timetable_preview,classes[self.preview_object.currentText()].timetable_dataframe)
        elif self.preview_mode.currentIndex()==1:
            display_df_in_table(self.timetable_preview,teachers[self.preview_object.currentText()].timetable_dataframe)
        elif self.preview_mode.currentIndex()==2:
            display_df_in_table(self.timetable_preview,class_total_dataframe())
        elif self.preview_mode.currentIndex()==3:
            display_df_in_table(self.timetable_preview,teacher_total_dataframe())
        # 手动设置行高
        for row in range(self.timetable_preview.rowCount()):
            self.timetable_preview.setRowHeight(row, 60)
        # 手动设置列宽
        for col in range(self.timetable_preview.columnCount()):
            self.timetable_preview.setColumnWidth(col, 130)
        self.timetable_preview.setFixedHeight(min(60*self.timetable_preview.rowCount()+35,420))

    def on_generation_finished(self):
        logging.info("排课已完成")
        self.generate_button.setEnabled(True)
        self.generate_button.setText("重新生成")
        self.log_label.setVisible(False)
        self.progress_bar.setVisible(False)
        self.preview_mode.setVisible(True)
        self.preview_object.setVisible(True)
        self.show_timetable()
        self.timetable_preview.setVisible(True)

    def on_progress_update(self,progress:tuple[Class,Time]):
        try:
            used_time=round(time.time()-self.generate_start_time)
            percentage=round(class_names.index(progress[0].name)/len(class_names)*100)
            self.log_label.setText(f"当前进度：{percentage}%%，班级：{progress[0].name}，课时：{progress[1]}，已用时间：%02d:%02d"%(used_time//60,used_time%60))
            self.progress_bar.setValue(class_names.index(progress[0].name))
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表出错：\n{e}")