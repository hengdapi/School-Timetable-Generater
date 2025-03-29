import streamlit as st,tomllib
def generate_time(lesson):
    settings=tomllib.load(open("settings.toml","br"))
    if lesson<=settings["morning_class_num"]:
        time="上午"
    else:
        time="下午"
        lesson-=settings["morning_class_num"]
    return f"{time}第{lesson}节"

days=["星期一","星期二","星期三","星期四","星期五"]

def menu():
    st.set_page_config(page_title="课程表生成器",page_icon="https://s1.aigei.com/src/img/png/03/03220c68b52d4345a46e5a8ddbdc2946.png?imageMogr2/auto-orient/thumbnail/!282x282r/gravity/Center/crop/282x282/quality/85/%7CimageView2/2/w/282&e=2051020800&token=P7S2Xpzfz11vAkASLTkfHN7Fw-oOZBecqeJaxypL:8tjG1RFMJ9_G5C-LvLonO8GNvHQ=",layout="wide")
    st.sidebar.header("课程表生成器")
    st.sidebar.page_link("main.py",label="主页",icon="🏠")
    st.sidebar.page_link("pages/settings.py",label="设置",icon="⚙️")
    st.sidebar.page_link("pages/generate.py",label="生成",icon="✨")
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