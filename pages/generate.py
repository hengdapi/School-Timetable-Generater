import os

from style import *
from generate_core import *
from save_core import SaveThread
from PySide6.QtCore import Qt
from PySide6 import QtGui
import time

class Generate(QFrame):
    def hide_widgets(self):
        for widget in self.hidden_widgets:
            widget.hide()

    def show_widgets(self):
        for widget in self.hidden_widgets:
            widget.show()

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

        self.title = title("生成",self,self.layout,10)
        # 读取配置文件
        self.cfg=load_settings()
        # 检查是否已配置课程信息
        if not self.cfg.lessons_info.value:
            settings_error(self,"请先在设置中配置课程信息")

        self.operation_layout=QHBoxLayout(self)
        self.layout.addLayout(self.operation_layout)
        # 生成课程表按钮
        self.generate_button=PrimaryPushButton("生成课程表",self)
        add_widget(self.generate_button,self.layout,0)
        self.generate_button.setIcon(FluentIcon.BRUSH)
        self.generate_button.setFixedSize(160,40)
        self.generate_button.clicked.connect(self.generate_timetable)
        add_widget(self.generate_button,self.operation_layout)

        self.save_button=PrimaryPushButton()
        self.save_button.setText("保存课程表")
        self.save_button.setIcon(FluentIcon.SAVE)
        self.save_button.setFixedSize(160,40)
        self.save_button.clicked.connect(self.save_timetable)
        add_widget(self.save_button,self.operation_layout)
        self.operation_layout.addStretch(1)

        self.progress_bar=ProgressBar()
        self.progress_bar.hide()
        add_widget(self.progress_bar,self.layout,0)

        self.log_label:BodyLabel=write("",self,self.layout)
        self.log_label.hide()
        add_widget(self.log_label,self.layout,0)

        # 课程表预览
        self.preview_layout=QHBoxLayout()
        self.layout.addLayout(self.preview_layout)
        self.preview_mode=ComboBox(self)
        self.preview_mode.addItems(["按班级查看","按教师查看","查看全部班级","查看全部教师"])
        self.preview_mode.currentIndexChanged.connect(self.change_mode)
        add_widget(self.preview_mode,self.preview_layout)

        self.preview_object=EditableComboBox(self)
        self.preview_object.addItems(results.class_names)
        self.preview_object.setCompleter(QCompleter(results.class_names,self.preview_object))
        self.preview_object.currentIndexChanged.connect(self.show_timetable)
        add_widget(self.preview_object,self.preview_layout,0)

        self.timetable_preview=TableWidget()
        self.timetable_preview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.timetable_preview.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.timetable_preview.clicked.connect(self.on_timetable_preview_clicked)
        self.timetable_preview.setContextMenuPolicy(Qt.CustomContextMenu)
        self.timetable_preview.customContextMenuRequested.connect(self.select_target)
        add_widget(self.timetable_preview,self.layout,0)

        self.exchange_layout=QHBoxLayout()
        self.layout.addLayout(self.exchange_layout)
        self.exchange_label=write("调整课程：",self,self.exchange_layout,10)
        self.from_lesson=LineEdit()
        self.from_lesson.setReadOnly(True)
        self.from_lesson.setPlaceholderText("左键点击表格中对应课程即可")
        add_widget(self.from_lesson,self.exchange_layout,0)

        self.exchange_button=PrimaryPushButton()
        self.exchange_button.setText("交换课程")
        self.exchange_button.setIcon(FluentIcon.SCROLL)
        self.exchange_button.setEnabled(False)
        self.exchange_button.clicked.connect(self.exchange_lesson)
        add_widget(self.exchange_button,self.exchange_layout,0)

        self.target_lesson=ComboBox()
        add_widget(self.target_lesson,self.exchange_layout,0)

        self.hidden_widgets=[self.save_button,self.exchange_label,self.target_lesson,self.exchange_button,self.from_lesson,self.preview_mode,self.preview_object,self.timetable_preview]
        self.hide_widgets()
        # === 设置滚动区域内容 ===
        self.layout.addStretch(1)
        scroll_area.setWidget(view)
        main_layout.addWidget(scroll_area)

    def select_target(self,pos):
        # 获取点击位置的行列
        item=self.timetable_preview.itemAt(pos)
        curr_text=f"{Time(item.column()+1,item.row()+1)} {item.text().split("\n")[0]}"
        self.target_lesson.setCurrentText(curr_text)
        if self.target_lesson.currentText()==curr_text:
            self.exchange_lesson()

    def generate_timetable(self):
        try:
            logging.info("生成按钮被点击")
            # 禁用生成按钮防止重复点击
            self.generate_button.setEnabled(False)
            self.progress_bar.show()
            self.progress_bar.setValue(0)
            self.progress_bar.setMaximum(len(results.class_names))
            self.log_label.show()
            self.hide_widgets()

            # 创建并启动线程
            self.generate_start_time=time.time()
            self.generate_thread=GenerateThread()
            self.generate_thread.finished_signal.connect(self.on_generation_finished)
            self.generate_thread.progress_signal.connect(self.on_progress_update)
            self.generate_thread.start()
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表出错：\n{e}")

    def on_timetable_preview_clicked(self):
        try:
            if self.preview_mode.currentIndex()!=0:
                return
            self.target_lesson.clear()
            self.from_lesson.clear()
            self.exchange_button.setEnabled(False)
            if self.timetable_preview.currentItem().background()==QColor(255,255,200):
                for j in range(self.timetable_preview.columnCount()):
                    for i in range(self.timetable_preview.rowCount()):
                        item=self.timetable_preview.item(i,j)
                        item.setBackground(QtGui.QBrush(Qt.NoBrush))
                        item.setToolTip("")
                return
            curr_item=self.timetable_preview.currentItem()
            clas=results.classes[self.preview_object.currentText()]
            curr_time=Time(curr_item.column()+1,curr_item.row()+1)
            curr_subjects=clas.get_lessons(curr_time)
            self.from_lesson.setText(f"{curr_time} {curr_item.text().split("\n")[0]}")
            for j in range(self.timetable_preview.columnCount()):
                for i in range(self.timetable_preview.rowCount()):
                    item=self.timetable_preview.item(i,j)
                    time=Time(item.column()+1,item.row()+1)
                    subjects=clas.get_lessons(time)
                    if (len(subjects)==1 and check(clas,curr_time,subjects[0]) or
                        len(subjects)==2 and check(clas,curr_time,subjects[0]) and check(clas,curr_time,subjects[1])) and\
                        (len(curr_subjects)==1 and check(clas,time,curr_subjects[0]) or
                        len(curr_subjects)==2 and check(clas,time,curr_subjects[0]) and check(clas,time,curr_subjects[1])) and\
                        subjects[0] not in [lesson[1] for lesson in set_lessons] and curr_subjects[0] not in [lesson[1] for lesson in set_lessons] and\
                        not subjects[0].continue_lesson and not curr_subjects[0].continue_lesson:
                        item.setBackground(QColor(150,255,150))
                        item.setToolTip("右键点击可交换")
                        self.target_lesson.addItem(f"{time} {item.text().split("\n")[0]}",userData=(time,copy.copy(subjects)))
                        self.exchange_button.setEnabled(True)
                    else:
                        item.setBackground(QColor(255,150,150))
                        item.setToolTip("不可交换")
            curr_item.setBackground(QColor(255,255,200))
            curr_item.setToolTip("当前选中（再次点击可取消）")
        except:
            e=traceback.format_exc()
            logging.critical(f"点击课程表出错：\n{e}")

    def exchange_lesson(self):
        try:
            curr_item=self.timetable_preview.currentItem()
            clas=results.classes[self.preview_object.currentText()]
            curr_time=Time(curr_item.column()+1,curr_item.row()+1)
            curr_subjects=copy.copy(clas.get_lessons(curr_time))
            target_time,target_subjects=self.target_lesson.currentData()
            if len(curr_subjects)==1:
                clas.remove_lesson(curr_time,curr_subjects[0])
            else:
                clas.remove_lesson(curr_time.sin_week,curr_subjects[0])
                clas.remove_lesson(curr_time.dou_week,curr_subjects[1])
            if len(target_subjects)==1:
                clas.remove_lesson(target_time,target_subjects[0])
            else:
                clas.remove_lesson(target_time.sin_week,target_subjects[0])
                clas.remove_lesson(target_time.dou_week,target_subjects[1])
            if len(curr_subjects)==1:
                clas.add_lesson(target_time,curr_subjects[0])
            else:
                clas.add_lesson(target_time.sin_week,curr_subjects[0])
                clas.add_lesson(target_time.dou_week,curr_subjects[1])
            if len(target_subjects)==1:
                clas.add_lesson(curr_time,target_subjects[0])
            else:
                clas.add_lesson(curr_time.sin_week,target_subjects[0])
                clas.add_lesson(curr_time.dou_week,target_subjects[1])
            self.show_timetable()
        except:
            e=traceback.format_exc()
            logging.critical(f"交换课程出错：\n{e}")

    def change_mode(self):
        self.preview_object.clear()
        if self.preview_mode.currentIndex()==0:
            items=results.class_names
            self.preview_object.setEnabled(True)
        elif self.preview_mode.currentIndex()==1:
            items=list(results.teachers.keys())
            self.preview_object.setEnabled(True)
        elif self.preview_mode.currentIndex()==2:
            items=[]
            self.show_timetable()
            self.preview_object.setEnabled(False)
        else:
            items=[]
            self.show_timetable()
            self.preview_object.setEnabled(False)
        self.preview_object.addItems(items)
        self.preview_object.setCompleter(QCompleter(items,self.preview_object))

    def show_timetable(self):
        self.from_lesson.clear()
        self.target_lesson.clear()
        self.exchange_button.setEnabled(False)
        self.timetable_preview.clear()
        if self.preview_mode.currentIndex()==0:
            display_df_in_table(self.timetable_preview,results.classes[self.preview_object.currentText()].timetable_dataframe)
            self.exchange_label.show()
            self.from_lesson.show()
            self.target_lesson.show()
            self.exchange_button.show()
        elif self.preview_mode.currentIndex()==1:
            display_df_in_table(self.timetable_preview,results.teachers[self.preview_object.currentText()].timetable_dataframe)
            self.exchange_label.hide()
            self.from_lesson.hide()
            self.target_lesson.hide()
            self.exchange_button.hide()
        elif self.preview_mode.currentIndex()==2:
            display_df_in_table(self.timetable_preview,class_total_dataframe())
            self.exchange_label.hide()
            self.from_lesson.hide()
            self.target_lesson.hide()
            self.exchange_button.hide()
        elif self.preview_mode.currentIndex()==3:
            display_df_in_table(self.timetable_preview,teacher_total_dataframe())
            self.exchange_label.hide()
            self.from_lesson.hide()
            self.target_lesson.hide()
            self.exchange_button.hide()
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
        self.log_label.hide()
        self.progress_bar.hide()
        self.show_widgets()
        self.show_timetable()

    def on_progress_update(self,progress:tuple[Class,Time]):
        try:
            used_time=round(time.time()-self.generate_start_time)
            percentage=round(results.class_names.index(progress[0].name)/len(results.class_names)*100)
            self.log_label.setText(f"当前进度：{percentage}%%，班级：{progress[0].name}，课时：{progress[1]}，已用时间：%02d:%02d"%(used_time//60,used_time%60))
            self.progress_bar.setValue(results.class_names.index(progress[0].name))
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表出错：\n{e}")

    def save_timetable(self):
        filename,_=QFileDialog.getSaveFileName(self,"保存课程表","","Microsoft Excel 工作表(*.xlsx);;Microsoft Excel 97-2003 工作表(*.xls)")
        if not filename:
            return
        logging.info(f"保存课程表文件名：{filename}")

        self.save_infobar=InfoBar(InfoBarIcon.INFORMATION,"正在保存课程表，请稍候...","",parent=self,duration=-1)
        self.save_progress=IndeterminateProgressBar()
        self.save_infobar.addWidget(self.save_progress)
        self.save_infobar.show()

        name,ext=os.path.splitext(filename)
        save_thread=SaveThread(name,ext,self)
        save_thread.success.connect(self.on_save_success)
        save_thread.error.connect(self.on_save_error)
        save_thread.start()

    def on_save_success(self):
        self.save_infobar.close()
        InfoBar.success("课程表保存成功！","",parent=self,duration=-1)

    def on_save_error(self,error):
        self.save_infobar.close()
        InfoBar.error("课程表保存失败！",error,parent=self,duration=-1)