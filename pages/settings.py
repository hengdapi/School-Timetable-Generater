# coding=utf-8
from PyQt5.QtCore import QTimer
from qfluentwidgets.components.date_time.picker_base import SeparatorWidget

from locals import *
from style import *
from wr_settings import *


class Settings(QFrame):
    def update_table_preview(self):
        save_settings(self)
        # 根据是否显示教师姓名调整表格信息和样式
        if cfg.show_teachers.value:
            info="课程信息\n(教师姓名)"
        else:
            info="课程信息"

        # 生成表格预览样式
        table_style=[]
        for day in range(5):
            table_style.append({"星期":days[day+1]})
            for i in range(1,cfg.morning_class_num.value+1):
                table_style[day][f"上午第{i}节"]=info
            for i in range(1,cfg.afternoon_class_num.value+1):
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
                user_info=user_info.rename(columns=rename_dict)
                cfg.lessons_info.value=user_info.to_dict(orient="records")
                for class_ in cfg.lessons_info.value:
                    for key,value in class_.items():
                        if pd.isna(value):
                            class_[key]=None

                new_subjects=[user_info.keys()[i][:-5] for i in range(1,len(user_info.keys()),2)]
                new_teachers=set()
                subjects_table_keys=["班级"]
                for subject in new_subjects:
                    new_teachers|=set(user_info[subject+" - 任课老师"].to_list())
                    subjects_table_keys.append(subject+" - 课时")
                    subjects_table_keys.append(subject+" - 任课老师")
                cfg.subjects_info.value=new_subjects
                new_teachers=[x for x in new_teachers if not pd.isna(x)]
                cfg.teachers_info.value=list(new_teachers)
                save_settings(self)
            except Exception as e:
                save_settings(self,False,str(e))
        else:
            if cfg.lessons_info.value!="":
                cfg.lessons_info.value=pd.DataFrame(cfg.lessons_info.value).to_json(orient="records", lines=False, force_ascii=False)

    def show_rule_strings(self):
        name=self.rule_combo.currentData()[0]
        for layout in self.string_layouts:
            while layout.count():
                item=layout.takeAt(0)
                if item.widget():
                    item.widget().hide()
                    item.widget().deleteLater()
        self.string_elements.clear()
        if name is None:
            self.add_rule_button.setEnabled(False)
            return
        self.add_rule_button.setEnabled(True)
        name=name.split("|")
        name.reverse()
        for string in name:
            if string[0]=="{" and string[-1]=="}":
                string_name=string[1:-1]
                string_layout=QHBoxLayout()
                self.layout.insertLayout(33,string_layout)
                name_label=write(f"请填写{string_name}字段：",self,string_layout)
                combo=EditableComboBox()
                if "subject" in string_name:
                    items=cfg.subjects_info.value
                elif "lesson" in string_name:
                    items=self.times
                elif "number" in string_name:
                    items=[str(i) for i in range(1,len(cfg.lessons_info.value)+1)]
                elif "teacher" in string_name:
                    items=cfg.teachers_info.value
                elif "class" in string_name:
                    items=[clas["班级"] for clas in cfg.lessons_info.value]
                else:
                    items=["无可选项"]
                combo.addItems(items)
                completer=QCompleter(items,combo)
                combo.setCompleter(completer)
                add_widget(combo,string_layout)
                self.string_layouts.append(string_layout)
                self.string_elements[string_name]=[name_label,combo]
        QTimer.singleShot(100,lambda :self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def add_rule(self):
        name,type=self.rule_combo.currentData()
        name=name.replace("{","").replace("}","").replace("|","")
        new_rule={"type":type}
        if name is None:
            return
        for string_name,elements in self.string_elements.items():
            combo:ComboBox=elements[1]
            if combo.currentText() not in [item.text for item in combo.items]:
                return
            name=name.replace(string_name,combo.currentText())
            new_rule[string_name]=combo.currentText()
        success,rule=self.check_rule(new_rule)
        if success:
            cfg.rules.value.append(new_rule)
            item=QListWidgetItem(name)
            item.setData(Qt.UserRole,new_rule)
            self.rule_list.addItem(item)
            save_settings(self)
        else:
            save_settings(self,False,"新规则与现有规则冲突或重复："+rule_to_string(rule))

    def remove_rule(self):
        try:
            selected_rule=self.rule_list.selectedItems()[0]
            cfg.rules.value.remove(selected_rule.data(Qt.UserRole))
            self.rule_list.takeItem(self.rule_list.row(selected_rule))
            self.remove_rule_button.setEnabled(len(cfg.rules.value))
            save_settings(self)
        except Exception as e:
            save_settings(self,False,str(e))

    def check_rule(self,new_rule):
        new_type=new_rule["type"]
        if new_type in ["set_time","avoid_time","priority_time"]:
            for rule in cfg.rules.value:
                if rule["type"] in ["set_time","avoid_time","priority_time"] and rule["lesson"]==new_rule["lesson"] and rule["subject"]==new_rule["subject"]:
                    return False,rule
        elif new_type=="set_time":
            for rule in cfg.rules.value:
                if rule["type"]=="set_time" and rule["lesson"]==new_rule["lesson"]:
                    return False,rule
                elif rule["type"]=="priority_time" and rule["lesson"]==new_rule["lesson"]:
                    return False,rule
        elif new_type=="priority_time":
            for rule in cfg.rules.value:
                if rule["type"]=="priority_time" and rule["lesson"]==new_rule["lesson"]:
                    return False,rule
                elif rule["type"]=="set_time" and rule["lesson"]==new_rule["lesson"]:
                    return False,rule
        elif new_type=="set_num":
            for rule in cfg.rules.value:
                if rule["type"]=="set_num" and rule["subject"]==new_rule["subject"]:
                    return False,rule
        elif new_type=="avoid_subject":
            if new_rule["subjectA"]==new_rule["subjectB"]:
                return False,new_rule
            for rule in cfg.rules.value:
                if rule["type"]=="avoid_subject" and {rule["subjectA"],rule["subjectB"]}=={new_rule["subjectA"],new_rule["subjectB"]}:
                    return False,rule
        elif new_type=="avoid_teacher":
            if new_rule["teacherA"]==new_rule["teacherB"]:
                return False,new_rule
            for rule in cfg.rules.value:
                if rule["type"]=="avoid_teacher" and {rule["teacherA"],rule["teacherB"]}=={new_rule["teacherA"],new_rule["teacherB"]}:
                    return False,rule
        elif new_type=="set_continue":
            for rule in cfg.rules.value:
                if rule["type"]=="set_continue" and rule["subject"]==new_rule["subject"]:
                    return False,rule
        elif new_type=="set_same_time":
            if new_rule["classA"]==new_rule["classB"]:
                return False,new_rule
            for rule in cfg.rules.value:
                if rule["type"]=="set_same_time" and rule["subject"]==new_rule["subject"] and {rule["classA"],rule["classB"]}=={new_rule["classA"],new_rule["classB"]}:
                    return False,rule
        return True,None

    def __init__(self,parent=None):
        try:
            super().__init__(parent=parent)
            logging.info("开始加载设置页面")
            self.setObjectName("Settings")
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(20,20,0,0)

            # === 创建可滚动区域 ===
            self.scroll_area=SingleDirectionScrollArea(orient=Qt.Vertical)
            self.scroll_area.setStyleSheet("QScrollArea{background: transparent; border: none}")
            self.scroll_area.setWidgetResizable(True)

            # === 创建内容容器 ===
            view=QWidget()
            view.setStyleSheet("QWidget{background: transparent}")
            self.layout = QVBoxLayout(view)

            self.title = title("设置",self,self.layout)

            # 表格样式设置区域
            biggersubheader("表格样式",self,self.layout)

            # 设置每天上午和下午的课程数量
            morning_class_num=RangeSettingCard(cfg.morning_class_num,FluentIcon.FLAG,title="每天上午上课数量",content="学校每天上午的上课数量")
            morning_class_num.valueChanged.connect(self.update_table_preview)
            add_widget(morning_class_num,self.layout,0)
            afternoon_class_num=RangeSettingCard(cfg.afternoon_class_num,FluentIcon.FLAG,title="每天下午上课数量",content="学校每天下午的上课数量")
            afternoon_class_num.valueChanged.connect(self.update_table_preview)
            add_widget(afternoon_class_num,self.layout,0)

            # 设置是否显示教师姓名和表格排版方式
            show_teachers=SwitchSettingCard(configItem=cfg.show_teachers,icon=FluentIcon.TAG,title="显示教师姓名",content="在课程名称下方标注任课教师姓名")
            show_teachers.checkedChanged.connect(self.update_table_preview)
            add_widget(show_teachers,self.layout,0)

            # 根据是否显示教师姓名调整表格信息和样式
            if cfg.show_teachers.value:
                info="课程信息\n(教师姓名)"
            else:
                info="课程信息"

            # 生成表格预览样式
            table_style=[]
            for day in range(5):
                table_style.append({"星期":days[day+1]})
                for i in range(1,cfg.morning_class_num.value+1):
                    table_style[day][f"上午第{i}节"]=info
                for i in range(1,cfg.afternoon_class_num.value+1):
                    table_style[day][f"下午第{i}节"]=info

            # 预览课程表
            subheader("预览",self,self.layout)
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
            add_widget(self.table_style_show,self.layout)

            add_widget(SeparatorWidget(orient=Qt.Horizontal),self.layout)

            # 课程信息设置区域
            biggersubheader("课程信息",self,self.layout)

            # 上传课程信息文件
            self.user_info_file=PushSettingCard(text="选择文件",icon=FluentIcon.INFO,title="课程信息文件",content="存储任课老师及课时、班级信息的表格")
            add_widget(self.user_info_file,self.layout)
            self.user_info_file.clicked.connect(self.pick_lessons_info)
            lessons_info=pd.DataFrame(cfg.lessons_info.value)
            lessons_info_table=TableWidget()
            display_df_in_table(lessons_info_table,lessons_info)
            lessons_info_table.setFixedHeight(500)
            lessons_info_table.setEditTriggers(TableWidget.NoEditTriggers)
            add_widget(lessons_info_table,self.layout)

            # 保存学科信息
            new_subjects=[lessons_info.keys()[i][:-5] for i in range(1,len(lessons_info.keys()),2)]
            subjects_table_keys=["班级"]
            for subject in new_subjects:
                subjects_table_keys.append(subject+" - 课时")
                subjects_table_keys.append(subject+" - 任课老师")
            cfg.subjects_info.value=new_subjects

            add_widget(SeparatorWidget(orient=Qt.Horizontal),self.layout)

            # 生成规则设置区域
            biggersubheader("生成规则",self,self.layout)
            rule_types=cfg.rule_types.value
            self.times=[day+lesson_to_str(lesson) for day in days[1:] for lesson in range(1,cfg.morning_class_num.value+cfg.afternoon_class_num.value+1)]
            self.string_elements={}
            self.string_layouts=[]

            rule_list_layout=QHBoxLayout()
            self.layout.addLayout(rule_list_layout)
            write("当前规则：",self,rule_list_layout)
            self.remove_rule_button=button("删除规则",self,rule_list_layout)
            self.remove_rule_button.setEnabled(False)
            self.remove_rule_button.setIcon(FluentIcon.REMOVE)
            self.remove_rule_button.setFixedWidth(200)
            self.remove_rule_button.clicked.connect(self.remove_rule)

            rule_list_layout.addWidget(self.remove_rule_button)
            self.rule_list=ListWidget()
            self.rule_list.setFixedHeight(200)
            self.rule_list.itemClicked.connect(lambda :self.remove_rule_button.setEnabled(True))
            for i in range(len(cfg.rules.value)):
                rule=cfg.rules.value[i]
                item=QListWidgetItem(rule_to_string(rule))
                item.setData(Qt.UserRole,rule)
                self.rule_list.addItem(item)
            add_widget(self.rule_list,self.layout)

            rule_layout=QHBoxLayout()
            self.layout.addLayout(rule_layout)
            self.rule_type_label=write("规则类型：",self,rule_layout)
            self.rule_type_label.setFixedWidth(150)

            self.rule_combo=ComboBox()
            self.rule_combo.addItem("请选择规则类型",userData=[None,None])
            for type,name in rule_types.items():
                self.rule_combo.addItem(name.replace("|",""),userData=[name,type])
            add_widget(self.rule_combo,rule_layout)
            self.rule_combo.currentIndexChanged.connect(self.show_rule_strings)

            self.add_rule_button=button("添加规则",self,rule_layout,0)
            self.add_rule_button.setEnabled(False)
            self.add_rule_button.setIcon(FluentIcon.ADD)
            self.add_rule_button.setFixedWidth(200)
            self.add_rule_button.clicked.connect(self.add_rule)

            # === 设置滚动区域内容 ===
            self.scroll_area.setWidget(view)
            main_layout.addWidget(self.scroll_area)
            logging.info("设置页面加载完成")
        except Exception as e:
            logging.critical(e)