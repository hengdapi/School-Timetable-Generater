# 导入必要的模块：Streamlit用于构建Web应用，tomllib用于读取TOML配置文件
import streamlit as st, tomllib

def generate_time(lesson):
    """
    根据课程节次生成时间描述

    :param lesson: 课程节次
    :return: 时间描述（如"上午第1节"）
    """
    # 读取设置文件，获取上午课程数量
    settings = tomllib.load(open("settings.toml", "br"))

    # 判断课程是在上午还是下午
    if lesson <= settings["morning_class_num"]:
        time = "上午"
    else:
        time = "下午"
        # 调整课程节次为下午的相对节次
        lesson -= settings["morning_class_num"]

    return f"{time}第{lesson}节"

# 定义工作日列表
days = ["星期一", "星期二", "星期三", "星期四", "星期五"]

def menu():
    """
    设置Streamlit应用的页面配置和侧边栏菜单
    """
    # 设置页面标题、图标和布局
    st.set_page_config(
        page_title="课程表生成器",
        page_icon="https://s1.aigei.com/src/img/png/03/03220c68b52d4345a46e5a8ddbdc2946.png?imageMogr2/auto-orient/thumbnail/!282x282r/gravity/Center/crop/282x282/quality/85/%7CimageView2/2/w/282&e=2051020800&token=P7S2Xpzfz11vAkASLTkfHN7Fw-oOZBecqeJaxypL:8tjG1RFMJ9_G5C-LvLonO8GNvHQ=",
        layout="wide"
    )

    # 设置侧边栏菜单
    st.sidebar.header("课程表生成器")
    st.sidebar.page_link("main.py", label="主页", icon="🏠")
    st.sidebar.page_link("pages/settings.py", label="设置", icon="⚙️")
    st.sidebar.page_link("pages/generate.py", label="生成", icon="✨")

    # 设置全局字体为微软雅黑
    st.markdown(
        """
        <style>
        * {
            font-family: 'Microsoft YaHei', sans-serif !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )