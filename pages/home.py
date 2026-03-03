# coding=utf-8
import os
from style import *
from PyQt5.QtWidgets import QFrame,QVBoxLayout


# noinspection PyTypeChecker
class Home(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.setObjectName("Home")
        layout=QVBoxLayout(self)
        layout.setContentsMargins(20,20,0,0)

        self.title = title("主页",self,layout)

        self.welcome_label=subheader("欢迎使用课程表生成器！😀",self,layout)

        self.introduce_label=write("此工具可以帮助你生成符合需求的课程表，现在请在设置页面上填写信息，生成一个课程表吧！",self,layout)

        self.feedback_label=subheader("反馈",self,layout)

        self.email_label=write("如果发现bug或者有更好的建议，欢迎反馈",self,layout)
        self.feedback_layout=QHBoxLayout(self)
        layout.addLayout(self.feedback_layout)

        self.send_issue=PrimaryPushButton("提个issue")
        add_widget(self.send_issue,self.feedback_layout)
        self.send_issue.setIcon(FluentIcon.GITHUB)
        self.send_issue.setFixedSize(130, 40)
        self.send_issue.clicked.connect(lambda:os.system("start https://github.com/hengdapi/School-Timetable-Generater/issues"))

        self.feedback_button=button("发送邮件",self,self.feedback_layout)
        self.feedback_button.setIcon(FluentIcon.MAIL)
        self.feedback_button.setFixedSize(130, 40)
        self.feedback_button.clicked.connect(lambda:os.system("start mailto:hengxiaopi@gmail.com"))
        self.feedback_layout.addStretch(1)

        layout.addStretch(1)  # 添加一个可伸缩的空间，值越大伸缩性越强
        self.setLayout(layout)