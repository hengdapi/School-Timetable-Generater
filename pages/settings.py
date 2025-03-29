import streamlit as st,menu,pandas as pd,tomllib,tomli_w,json
# noinspection PyUnresolvedReferences
from menu import generate_time,days
menu.menu()

st.title("设置")
settings=tomllib.load(open("settings.toml","br"))

def save_settings():
    with open("settings.toml","wb") as f:
        tomli_w.dump(settings,f)
    st.success("设置保存成功！")

grades=["一","二","三","四","五","六","七","八","九"]
st.markdown("## 表格样式")
settings["morning_class_num"]=st.number_input("每天上午上课数量",min_value=1,max_value=10,value=settings["morning_class_num"])
settings["afternoon_class_num"]=st.number_input("每天下午上课数量",min_value=1,max_value=10,value=settings["afternoon_class_num"])
settings["show_teachers"]=st.checkbox("显示教师姓名",settings["show_teachers"])
settings["transpose"]=st.checkbox("横向排版",value=settings["transpose"])
if settings["show_teachers"]:
    info="""课程信息
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
    info="课程信息"

table_style=[]
for day in range(5):
    table_style.append({"星期":days[day]})
    for i in range(1,settings["morning_class_num"]+1):
        table_style[day][f"上午第{i}节"]=info
    for i in range(1,settings["afternoon_class_num"]+1):
        table_style[day][f"下午第{i}节"]=info

st.subheader("预览")
st.markdown("##### 一年级1班课程表")
table=pd.DataFrame(table_style)
if not settings["transpose"]:
    st.dataframe(table.transpose())
else:
    table.columns = ['星期']+[f"上午第{i}节" for i in range(1,settings["morning_class_num"]+1)]+[f"下午第{i}节" for i in range(1,settings["afternoon_class_num"]+1)]
    st.dataframe(table,hide_index=True)
save_settings()
st.divider()


st.markdown("## 课程信息")
user_info_file=st.file_uploader("上传课程信息文件",type=["xls","xlsx"])
if user_info_file:
    user_info=pd.read_excel(user_info_file)
    rename_dict={}
    for i in range(2,len(user_info.keys()),2):
        rename_dict[user_info.keys()[i]]=user_info.keys()[i-1]+" - 任课老师"
        rename_dict[user_info.keys()[i-1]]=user_info.keys()[i-1]+" - 课时"
    user_info=user_info.rename(columns=rename_dict)
else:
    if settings.get("lessons_info"):
        user_info=pd.DataFrame(json.loads(settings["lessons_info"]))
    else:
        st.stop()

# @st.dialog("删除学科")
# def delete_subject():
#     del_subject=st.selectbox("选择要删除的学科",settings["subjects_info"])
#
#     if st.button("确定"):
#         settings["subjects_info"].remove(del_subject)
#         save_subjects()
#         st.rerun()
#
def save_subjects():
    new_subjects=[user_info.keys()[i][:-5] for i in range(1,len(user_info.keys()),2)]
    subjects_table_keys=["班级"]
    for subject in new_subjects:
        subjects_table_keys.append(subject+" - 课时")
        subjects_table_keys.append(subject+" - 任课老师")
    settings["subjects_info"]=new_subjects

lessons_info=st.data_editor(user_info,hide_index=True)
# if st.button("保存课程信息"):
settings["lessons_info"]=lessons_info.to_json(orient="records",lines=False,force_ascii=False)
save_settings()
st.divider()

st.markdown("## 生成规则")
subjects=[]
for subject in settings["subjects_info"]:
    if not (subject.endswith("(0.5)") or subject.endswith("（0.5）")):
        subjects.append(subject)
for lesson in settings["rules"]["must_include"]:
    if lesson not in subjects:
        settings["rules"]["must_include"].remove(lesson)
settings["rules"]["must_include"]=st.multiselect("每天必须包含的课程",subjects,default=settings["rules"]["must_include"])

priority=json.loads(settings["rules"]["priority"])
options=[]
st.subheader("排课优先位置")
for i in range(len(subjects)):
    for day in range(5):
        for time in range(1,settings["morning_class_num"]+settings["afternoon_class_num"]+1):
            if len(options)<(settings["morning_class_num"]+settings["afternoon_class_num"])*5:
                options.append(days[day]+generate_time(time))
columns_config={"priority":st.column_config.SelectboxColumn("学科总优先级",options=range(1,len(subjects)+1),required=True),
                "subject":st.column_config.TextColumn("学科",disabled=True)}
columns_config.update({str(time):st.column_config.SelectboxColumn(f"{time}级优先",width="medium",options=options) for time in range(1,(settings["morning_class_num"]+settings["afternoon_class_num"])*5+1)})
priority_table=st.data_editor(pd.DataFrame(priority),hide_index=True,column_config=columns_config)
for line in range(len(subjects)):
    line_elements=list(priority_table.iloc[line])
    for col in line_elements:
        if line_elements.count(col)>1 and not col is None:
            st.error(f"{subjects[line]}学科存在重复的优先位置！")
            st.stop()

col_elements=list(priority_table.iloc[:,1])
for line in range(len(subjects)):
    element=col_elements[line]
    if element is None:
        st.error("存在空白优先级！")
        st.stop()
    elif col_elements.count(element)>1 and not line is None:
        st.error(f"{subjects[line]}学科存在重复的优先级！")
        st.stop()
settings["rules"]["priority"]=priority_table.to_json(orient="records",lines=False,force_ascii=False)
save_settings()