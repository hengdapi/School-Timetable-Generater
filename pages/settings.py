# coding=utf-8
from functools import cmp_to_key

import pandas as pd
from PyQt5.QtWidgets import *
from qfluentwidgets import *
from qfluentwidgets.components.date_time.picker_base import SeparatorWidget

from menu import days,generate_time,display_df_in_table
from style import *
from wr_settings import *

class Settings(QFrame):
    def update_table_preview(self):
        save_settings(self)
        # 根据是否显示教师姓名调整表格信息和样式
        if self.cfg.show_teachers.value:
            info="课程信息\n(教师姓名)"
        else:
            info="课程信息"

        # 生成表格预览样式
        table_style=[]
        for day in range(5):
            table_style.append({"星期":days[day+1]})
            for i in range(1,self.cfg.morning_class_num.value+1):
                table_style[day][f"上午第{i}节"]=info
            for i in range(1,self.cfg.afternoon_class_num.value+1):
                table_style[day][f"下午第{i}节"]=info
        self.table=pd.DataFrame(table_style)
        # 根据设置选择表格显示方式
        display_df_in_table(self.table_style_show,self.table.transpose())
        self.table_style_show.setFixedHeight(50*self.table_style_show.rowCount()+2)

    def pick_lessons_info(self):
        user_info_file,_=QFileDialog.getOpenFileName(
            self,
            "选择课程信息文件",
            "",
            "Excel文件 (*.xlsx *.xls)"
        )
        # 处理上传的课程信息文件或使用已有配置
        if user_info_file:
            try:
                user_info=pd.read_excel(user_info_file)
                rename_dict={}
                for i in range(2,len(user_info.keys()),2):
                    rename_dict[user_info.keys()[i]]=user_info.keys()[i-1]+" - 任课老师"
                    rename_dict[user_info.keys()[i-1]]=user_info.keys()[i-1]+" - 课时"
                self.cfg.lessons_info.value=user_info.rename(columns=rename_dict).to_json(orient="records", lines=False, force_ascii=False)
                save_settings(self)
            except Exception as e:
                save_settings(self,False,str(e))
        else:
            if self.cfg.lessons_info.value!="":
                self.cfg.lessons_info.value=pd.DataFrame(json.loads(self.cfg.lessons_info.value)).to_json(orient="records", lines=False, force_ascii=False)

    def save_priority(self,item=None,row=None,col=None,subjects=None, options_key_map=None):
        priority=json.loads(self.cfg.priority.value)
        if item:
            row=item.row()
            priority[row]["enabled"]=(item.checkState()==2)
        else:
            item=self.priority_table.cellWidget(row,col)
            text=item.currentText()
            if col==2:
                priority[row]["priority"]=text
            elif col>2:
                if text=="":
                    priority[row][str(col-2)]=[0,0]
                else:
                    priority[row][str(col-2)]=[days.index(text[:3]),int(text[6])]

        priority_df=pd.DataFrame(priority)
        # 验证和处理优先级配置
        for line in range(len(subjects)):
            line_elements=list(priority_df.iloc[line])
            for col in range(3,len(line_elements)):
                element=line_elements[col]
                if element[0]!=0 and line_elements[3:].count(element)>1:
                    save_settings(self,False,f"{subjects[line]}学科存在重复的优先位置！")

        # 检查优先级配置的有效性
        col_elements=list(priority_df.iloc[:,1])
        for line in range(len(subjects)):
            element=col_elements[line]
            if element is None:
                save_settings(self,False,"存在空白优先级！")
            elif col_elements.count(element)>1 and element not in [None,False,True]:
                save_settings(self,False,f"{subjects[line]}学科存在重复的优先级！")

        # 对优先级进行排序并保存
        priority_list=priority_df.to_dict(orient="records")

        def cmp(x,y):
            return x["priority"]-y["priority"]

        priority_list.sort(key=cmp_to_key(cmp))
        self.cfg.priority.value=pd.DataFrame(priority_list).to_json(orient="records",lines=False,force_ascii=False)
        self.cfg.priority.value=json.dumps(priority)
        save_settings(self)

    def __init__(self,parent=None):

        super().__init__(parent=parent)
        self.setObjectName("Settings")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20,20,0,0)

        # === 创建可滚动区域 ===
        scroll_area=SingleDirectionScrollArea(orient=Qt.Vertical)
        scroll_area.setStyleSheet("QScrollArea{background: transparent; border: none}")
        scroll_area.setWidgetResizable(True)

        # === 创建内容容器 ===
        view=QWidget()
        view.setStyleSheet("QWidget{background: transparent}")
        layout = QVBoxLayout(view)

        self.title = title("设置",self,layout)
        # 读取配置文件
        self.cfg=load_settings()

        # 表格样式设置区域
        biggersubheader("表格样式",self,layout)

        # 设置每天上午和下午的课程数量
        morning_class_num=RangeSettingCard(self.cfg.morning_class_num,FluentIcon.FLAG,title="每天上午上课数量",content="学校每天上午的上课数量")
        morning_class_num.valueChanged.connect(self.update_table_preview)
        add_widget(morning_class_num,layout,0)
        afternoon_class_num=RangeSettingCard(self.cfg.afternoon_class_num,FluentIcon.FLAG,title="每天上午上课数量",content="学校每天下午的上课数量")
        afternoon_class_num.valueChanged.connect(self.update_table_preview)
        add_widget(afternoon_class_num,layout,0)

        # 设置是否显示教师姓名和表格排版方式
        show_teachers=SwitchSettingCard(configItem=self.cfg.show_teachers,icon=FluentIcon.TAG,title="显示教师姓名",content="在课程名称下方标注任课教师姓名")
        show_teachers.checkedChanged.connect(self.update_table_preview)
        add_widget(show_teachers,layout,0)

        # 根据是否显示教师姓名调整表格信息和样式
        if self.cfg.show_teachers.value:
            info="课程信息\n(教师姓名)"
        else:
            info="课程信息"

        # 生成表格预览样式
        table_style=[]
        for day in range(5):
            table_style.append({"星期":days[day+1]})
            for i in range(1,self.cfg.morning_class_num.value+1):
                table_style[day][f"上午第{i}节"]=info
            for i in range(1,self.cfg.afternoon_class_num.value+1):
                table_style[day][f"下午第{i}节"]=info

        # 预览课程表
        subheader("预览",self,layout)
        write("一年级1班课程表",self,layout,0)
        self.table=pd.DataFrame(table_style)

        self.table_style_show=TableWidget()
        self.table_style_show.setBorderVisible(True)
        self.table_style_show.setFont(fonts.subheader)
        self.table_style_show.setBorderRadius(8)
        self.table_style_show.verticalHeader().setDefaultSectionSize(50)
        self.table_style_show.horizontalHeader().setDefaultSectionSize(155)
        self.table_style_show.horizontalHeader().setVisible(False)
        self.table_style_show.setEditTriggers(TableWidget.NoEditTriggers)
        # 根据设置选择表格显示方式
        display_df_in_table(self.table_style_show,self.table.transpose())
        self.table_style_show.setFixedHeight(50*self.table_style_show.rowCount()+2)
        add_widget(self.table_style_show,layout)

        add_widget(SeparatorWidget(orient=Qt.Horizontal),layout)

        # 课程信息设置区域
        biggersubheader("课程信息",self,layout)

        # 上传课程信息文件
        self.user_info_file=PushSettingCard(text="选择文件",icon=FluentIcon.INFO,title="课程信息文件",content="存储任课老师及课时、班级信息的表格")
        add_widget(self.user_info_file,layout)
        self.user_info_file.clicked.connect(self.pick_lessons_info)
        lessons_info=pd.DataFrame(json.loads(self.cfg.lessons_info.value))
        lessons_info_table=TableWidget()
        display_df_in_table(lessons_info_table,lessons_info)
        lessons_info_table.setFixedHeight(500)
        lessons_info_table.setEditTriggers(TableWidget.NoEditTriggers)
        add_widget(lessons_info_table,layout)

        # 保存学科信息
        new_subjects=[lessons_info.keys()[i][:-5] for i in range(1,len(lessons_info.keys()),2)]
        subjects_table_keys=["班级"]
        for subject in new_subjects:
            subjects_table_keys.append(subject+" - 课时")
            subjects_table_keys.append(subject+" - 任课老师")
        self.cfg.subjects_info.value=new_subjects

        add_widget(SeparatorWidget(orient=Qt.Horizontal),layout)

        # 生成规则设置区域
        biggersubheader("生成规则",self,layout)

        # 筛选非0.5课时的学科
        # 所有学科
        subjects=[]
        for subject in self.cfg.subjects_info.value:
            if not (subject.endswith("(0.5)") or subject.endswith("（0.5）")):
                subjects.append(subject)

        # 初始化优先级选项
        options=[""]
        options_key_map={"[0, 0]":None}
        options_value_map = {None: "[0, 0]"}

        # 生成排课优先位置选项
        subheader("排课优先位置",self,layout)
        for i in range(len(subjects)):
            for day in range(1,6):
                for time in range(1,self.cfg.morning_class_num.value+self.cfg.afternoon_class_num.value+1):
                    if len(options)<(self.cfg.morning_class_num.value+self.cfg.afternoon_class_num.value)*5:
                        options.append(days[day]+generate_time(time))
                        options_value_map[options[-1]] = str([day, time])
                        options_key_map[str([day,time])]=options[-1]

        # 处理优先级配置
        priority = json.loads(self.cfg.priority.value)
        for subject in priority:
            for i in range(1, len(subject) - 2):
                subject[str(i)] = options_key_map[str(subject[str(i)])]

        # 创建表格
        self.priority_table = TableWidget()
        self.priority_table.setRowCount(len(priority))
        self.priority_table.setColumnCount((self.cfg.morning_class_num.value + self.cfg.afternoon_class_num.value) * 5 + 3)

        # 设置表头
        headers = ["学科", "启用优先级", "学科总优先级"]
        for time in range(1, (self.cfg.morning_class_num.value + self.cfg.afternoon_class_num.value) * 5 + 1):
            headers.append(f"{time}级优先位置")
        self.priority_table.setHorizontalHeaderLabels(headers)

        # 填充数据
        for row, subject in enumerate(priority):
            # 学科名称（禁用编辑）
            subject_item = QTableWidgetItem(subject.get("subject", ""))
            subject_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.priority_table.setItem(row, 0, subject_item)

            # 启用优先级复选框（禁用编辑）
            enabled_checkbox = QTableWidgetItem()
            enabled_checkbox.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            enabled_checkbox.setCheckState(Qt.Checked if subject.get("enabled", False) else Qt.Unchecked)
            self.priority_table.setItem(row, 1, enabled_checkbox)

            # 学科总优先级
            priority_combo = ComboBox()
            priority_combo.addItems([str(i) for i in range(1, len(subjects) + 1)])
            priority_combo.setCurrentText(str(subject.get("priority", "")))
            priority_combo.currentIndexChanged.connect(lambda _,row=row, col=2: self.save_priority(row=row, col=col,subjects=subjects,options_key_map=options_key_map))
            self.priority_table.setCellWidget(row, 2, priority_combo)

            # 各个优先位置
            for col in range(3, len(headers)):
                time = col - 2  # 因为前两列是启用和学科，第三列对应1级优先位置
                combo = ComboBox()
                combo.addItems(options)
                current_value = subject.get(str(time), "")
                combo.setCurrentText(current_value)
                combo.currentIndexChanged.connect(lambda _,row=row, col=col: self.save_priority(row=row, col=col,subjects=subjects,options_key_map=options_key_map))
                self.priority_table.setCellWidget(row, col, combo)
                self.priority_table.setColumnWidth(col, 150)

        self.priority_table.setFixedHeight(500)
        self.priority_table.itemChanged.connect(self.save_priority)
        add_widget(self.priority_table, layout)


        # === 设置滚动区域内容 ===
        scroll_area.setWidget(view)
        main_layout.addWidget(scroll_area)
