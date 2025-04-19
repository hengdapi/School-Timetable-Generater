# 导入必要的模块
import streamlit as st, menu, pandas as pd, tomllib, tomli_w, json, numpy as np
# noinspection PyUnresolvedReferences
from menu import generate_time, days
from functools import cmp_to_key

# 调用菜单函数
menu.menu()

# 设置页面标题
st.title("设置")

# 读取配置文件
settings = tomllib.load(open("settings.toml", "br"))

def save_settings():
    """
    将当前设置保存到settings.toml文件
    """
    with open("settings.toml", "wb") as f:
        tomli_w.dump(settings, f)
    st.success("设置保存成功！")

# 年级列表（备用）
grades = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]

# 表格样式设置区域
st.markdown("## 表格样式")

# 设置每天上午和下午的课程数量
settings["morning_class_num"] = st.number_input("每天上午上课数量", min_value=1, max_value=10, value=settings["morning_class_num"])
settings["afternoon_class_num"] = st.number_input("每天下午上课数量", min_value=1, max_value=10, value=settings["afternoon_class_num"])

# 设置是否显示教师姓名和表格排版方式
settings["show_teachers"] = st.checkbox("显示教师姓名", settings["show_teachers"])
settings["transpose"] = st.checkbox("横向排版", value=settings["transpose"])

# 根据是否显示教师姓名调整表格信息和样式
if settings["show_teachers"]:
    info = """课程信息
（教师姓名）"""
    st.markdown(
        """
        <style>
        .dataframe tbody tr {
            height: 40px;  /* 这里设置行高为40px */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    info = "课程信息"

# 生成表格预览样式
table_style = []
for day in range(5):
    table_style.append({"星期": days[day]})
    for i in range(1, settings["morning_class_num"] + 1):
        table_style[day][f"上午第{i}节"] = info
    for i in range(1, settings["afternoon_class_num"] + 1):
        table_style[day][f"下午第{i}节"] = info

# 预览课程表
st.subheader("预览")
st.markdown("##### 一年级1班课程表")
table = pd.DataFrame(table_style)

# 根据设置选择表格显示方式
if not settings["transpose"]:
    st.dataframe(table.transpose())
else:
    table.columns = ['星期'] + [f"上午第{i}节" for i in range(1, settings["morning_class_num"] + 1)] + [f"下午第{i}节" for i in range(1, settings["afternoon_class_num"] + 1)]
    st.dataframe(table, hide_index=True)

# 保存设置
save_settings()
st.divider()

# 课程信息设置区域
st.markdown("## 课程信息")

# 上传课程信息文件
user_info_file = st.file_uploader("上传课程信息文件", type=["xls", "xlsx"])

# 处理上传的课程信息文件或使用已有配置
if user_info_file:
    user_info = pd.read_excel(user_info_file)
    rename_dict = {}
    for i in range(2, len(user_info.keys()), 2):
        rename_dict[user_info.keys()[i]] = user_info.keys()[i-1] + " - 任课老师"
        rename_dict[user_info.keys()[i-1]] = user_info.keys()[i-1] + " - 课时"
    user_info = user_info.rename(columns=rename_dict)
else:
    if settings.get("lessons_info"):
        user_info = pd.DataFrame(json.loads(settings["lessons_info"]))
    else:
        st.stop()

def save_subjects():
    """
    保存学科信息
    """
    new_subjects = [user_info.keys()[i][:-5] for i in range(1, len(user_info.keys()), 2)]
    subjects_table_keys = ["班级"]
    for subject in new_subjects:
        subjects_table_keys.append(subject + " - 课时")
        subjects_table_keys.append(subject + " - 任课老师")
    settings["subjects_info"] = new_subjects

# 可编辑的课程信息表格
lessons_info = st.data_editor(user_info, hide_index=True)
settings["lessons_info"] = lessons_info.to_json(orient="records", lines=False, force_ascii=False)
save_settings()
st.divider()

# 生成规则设置区域
st.markdown("## 生成规则")

# 筛选非0.5课时的学科
subjects = []
for subject in settings["subjects_info"]:
    if not (subject.endswith("(0.5)") or subject.endswith("（0.5）")):
        subjects.append(subject)

# 清理和设置每天必须包含的课程
for lesson in settings["rules"]["must_include"]:
    if lesson not in subjects:
        settings["rules"]["must_include"].remove(lesson)
settings["rules"]["must_include"] = st.multiselect("每天必须包含的课程", subjects, default=settings["rules"]["must_include"])

# 初始化优先级选项
options = []
options_value_map = {None: "[0, 0]", np.False_: False, np.True_: True}
options_key_map = {"[0, 0]": None, False: np.False_, True: np.True_}

# 生成排课优先位置选项
st.subheader("排课优先位置")
for i in range(len(subjects)):
    for day in range(1,6):
        for time in range(1, settings["morning_class_num"] + settings["afternoon_class_num"] + 1):
            if len(options) < (settings["morning_class_num"] + settings["afternoon_class_num"]) * 5:
                options.append(days[day] + generate_time(time))
                options_value_map[options[-1]] = str([day, time])
                options_key_map[str([day, time])] = options[-1]

# 处理优先级配置
priority = json.loads(settings["rules"]["priority"])
for subject in priority:
    for i in range(1, len(subject)-2):
        subject[str(i)] = options_key_map[subject[str(i)]]
        columns_config = {
            "priority": st.column_config.SelectboxColumn("学科总优先级", options=range(1, len(subjects)+1), required=True),
            "enabled": st.column_config.CheckboxColumn("启用优先级", default=False),
            "subject": st.column_config.TextColumn("学科", disabled=True)
        }
        columns_config.update({
            str(time): st.column_config.SelectboxColumn(f"{time}级优先位置", width="medium", options=options)
            for time in range(1, (settings["morning_class_num"] + settings["afternoon_class_num"]) * 5 + 1)
        })

# 可编辑的优先级配置表格
priority_table = st.data_editor(pd.DataFrame(priority), hide_index=True, column_config=columns_config)

# 验证和处理优先级配置
for line in range(len(subjects)):
    line_elements = list(priority_table.iloc[line])
    for col in range(len(line_elements)):
        element = line_elements[col]
        if col > 2:
            priority_table.iloc[line, col] = options_value_map[element]
        if element not in [None, False, True] and line_elements.count(element) > 1:
            st.error(f"{subjects[line]}学科存在重复的优先位置！")
            st.stop()

# 检查优先级配置的有效性
col_elements = list(priority_table.iloc[:, 1])
for line in range(len(subjects)):
    element = col_elements[line]
    if element is None:
        st.error("存在空白优先级！")
        st.stop()
    elif col_elements.count(element) > 1 and element not in [None, False, True]:
        st.error(f"{subjects[line]}学科存在重复的优先级！")
        st.stop()

# 对优先级进行排序并保存
priority_list = priority_table.to_dict(orient="records")
def cmp(x, y):
    return x["priority"] - y["priority"]
priority_list.sort(key=cmp_to_key(cmp))
settings["rules"]["priority"] = pd.DataFrame(priority_list).to_json(orient="records", lines=False, force_ascii=False)
save_settings()