from PyQt5.QtCore import QRect
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame,QVBoxLayout
from qfluentwidgets import LargeTitleLabel,SubtitleLabel,BodyLabel,PushButton

class fonts:
    title=QFont("Microsoft YaHei",30,QFont.Bold)
    biggersubheader=QFont("Microsoft YaHei",25,QFont.Bold)
    subheader=QFont("Microsoft YaHei",20,QFont.Bold)
    write=QFont("Microsoft YaHei",15)
    button=QFont("Microsoft YaHei",13)

def add_widget(widget,layout:QVBoxLayout,spacing=20):
    layout.addWidget(widget)
    layout.addSpacing(spacing)

def label(text: str,label_type,font:QFont,window:QFrame,layout:QVBoxLayout,spacing):
    label = label_type(text, window)
    label.setFont(font)
    add_widget(label,layout,spacing)
    return label

def title(text: str,window:QFrame,layout:QVBoxLayout,spacing=20):
    return label(text,LargeTitleLabel,fonts.title,window,layout,spacing)


def biggersubheader(text: str,window:QFrame,layout:QVBoxLayout,spacing=20):
    return label(text,SubtitleLabel,fonts.biggersubheader,window,layout,spacing)

def subheader(text: str,window:QFrame,layout:QVBoxLayout,spacing=20):
    return label(text,SubtitleLabel,fonts.subheader,window,layout,spacing)

def write(text: str,window:QFrame,layout:QVBoxLayout,spacing=20):
    return label(text,BodyLabel,fonts.write,window,layout,spacing)

def button(text: str,window:QFrame,layout:QVBoxLayout,spacing=20):
    return label(text,PushButton,fonts.button,window,layout,spacing)