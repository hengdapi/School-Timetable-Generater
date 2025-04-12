# coding=utf-8
# 导入必要的模块：Streamlit用于构建Web应用，menu用于设置页面菜单
import streamlit as st, menu

# 调用菜单函数，设置页面菜单
menu.menu()

# 设置主页标题
st.title("主页")

# 添加欢迎信息和工具介绍
st.subheader("欢迎使用课程表生成器！😀")
st.markdown("此工具可以帮助你生成符合需求的课程表，现在请在设置页面上填写信息，生成一个课程表吧！")

# 添加反馈区域
st.subheader("反馈")
st.write("如果您有任何意见或建议，欢迎通过[邮箱](mailto:hengxiaopi@gmail.com)联系我")