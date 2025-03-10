import streamlit as st,menu,pandas as pd,random,copy,tomllib,zipfile,os,json
from io import BytesIO
from menu import generate_time
class Teacher:
    def __init__(self,name):
        self.name=name
        self.lessons_time=[]

    def add_lesson_time(self,day,lesson,week):
        self.lessons_time.append((day,lesson,week))

    def is_busy(self,day,lesson,week="all"):
        return (day,lesson,week) in self.lessons_time

def add_lesson(class_,day,lesson,subject,week="all",mode="replace",remove=True):
    global table,teachers,class_subjects,special_subjects
    week_map={"single":"单 ","double":"双 ","all":""}
    teacher=dict_lessons[class_][subject+" - 任课老师"]
    if teachers[teacher].is_busy(day,lesson):
        return False
    time=generate_time(lesson)
    if mode=="replace":
        table[day][time]=week_map[week]+subject
    else:
        table[day][time]+="\n"+week_map[week]+subject
    if settings["show_teachers"]:
        table[day][time]+="\n（%s）"%teacher
    teachers[teacher].add_lesson_time(day,lesson,week)
    if subject in class_subjects and remove:
        class_subjects.remove(subject)
    return True

if __name__ == '__main__':
    menu.menu()

    st.title("生成")
    with open("settings.toml","br") as f:
        settings=tomllib.load(f)
        if "lessons_info" not in settings:
            st.error("请先在设置中配置课程信息")
            st.stop()
        lessons=json.loads(settings["lessons_info"])
        dict_lessons={}
        for i in range(len(lessons)):
            dict_lessons[lessons[i]["班级"]]=lessons[i]
        pd_lessons=pd.DataFrame(lessons)
        table_style=settings["table_style"]
        subjects=settings["subjects_info"]

    class_tables={}
    teachers={lessons[class_][subject+" - 任课老师"]:Teacher(lessons[class_][subject+" - 任课老师"]) for class_ in range(len(lessons)) for subject in subjects}

    if st.button("生成课程表"):
        for class_ in dict_lessons:
            continue_loop=True
            old_teachers=copy.deepcopy(teachers)
            while continue_loop:
                continue_loop=False
                teachers=copy.deepcopy(old_teachers)
                table=copy.deepcopy(table_style)
                class_subjects=[]
                special_subjects=[]
                for subject in subjects:
                    if not dict_lessons[class_][subject+" - 课时"] is None:
                        if subject.endswith("(0.5)") or subject.endswith("（0.5）"):
                            special_subjects.append(subject)
                        elif subject in settings["rules"]["must_include"]:
                            for i in range(int(float(dict_lessons[class_][subject+" - 课时"]))-5):
                                class_subjects.append(subject)
                        else:
                            for i in range(int(float(dict_lessons[class_][subject+" - 课时"]))):
                                class_subjects.append(subject)
                if len(special_subjects)>0:
                    class_subjects.append(special_subjects)
                for day in range(5):
                    must_lessons=[]
                    for must_include in settings["rules"]["must_include"]:
                        must_lesson=random.choice(list(set(range(1,settings["morning_class_num"]+settings["afternoon_class_num"]+1))-set(must_lessons)))
                        successful=add_lesson(class_,day,must_lesson,must_include,remove=False)
                        while not successful:
                            must_lesson=random.choice(list(set(range(1,settings["morning_class_num"]+settings["afternoon_class_num"]+1))-set(must_lessons)))
                            successful=add_lesson(class_,day,must_lesson,must_include,remove=False)
                        must_lessons.append(must_lesson)
                    # st.table(pd.DataFrame(table).transpose())
                    for lesson in range(1,settings["morning_class_num"]+settings["afternoon_class_num"]+1):
                        if lesson in must_lessons:
                            continue
                        subject=random.choice(class_subjects)
                        if type(subject)==list:
                            successful=add_lesson(class_,day,lesson,subject[0],"single") and add_lesson(class_,day,lesson,subject[1],"double","append") or add_lesson(class_,day,lesson,subject[0],"double") and add_lesson(class_,day,lesson,subject[1],"single","append")
                            if successful:
                                class_subjects.remove(subject)
                        else:
                            successful=add_lesson(class_,day,lesson,subject)
                        tries=0
                        while not successful:
                            subject=random.choice(class_subjects)
                            if type(subject)==list:
                                successful=add_lesson(class_,day,lesson,subject[0],"single") and add_lesson(class_,day,lesson,subject[1],"double","append") or add_lesson(class_,day,lesson,subject[0],"double") and add_lesson(class_,day,lesson,subject[1],"single","append")
                                if successful:
                                    class_subjects.remove(subject)
                            else:
                                successful=add_lesson(class_,day,lesson,subject)
                            tries+=1
                            if tries>=100:
                                continue_loop=True
                                break
                        if continue_loop:
                            break
                    if continue_loop:
                        break

            # st.subheader(settings["table_title"].replace("%g",grades[grade-1]).replace("%c",str(class_)))
            st.subheader(class_+"课程表")
            if settings["transpose"]:
                table=pd.DataFrame(table)
                # st.table(table,hide_index=True)
                st.dataframe(table,hide_index=True)
            else:
                table=pd.DataFrame(table).transpose()
                # st.table(table)
                st.table(table)
            class_tables[class_]=table

        if not os.path.exists("output"):
            os.mkdir("output")

        with pd.ExcelWriter("课程表.xlsx") as writer:
            for class_,table in class_tables.items():
                table.to_excel(writer,sheet_name=class_,index=not settings["transpose"])
                table.to_excel(f"output/{class_}.xlsx",index=not settings["transpose"])

        zip_buffer=BytesIO()
        with zipfile.ZipFile(zip_buffer,mode='w',compression=zipfile.ZIP_DEFLATED) as zipf:
            for class_,table in class_tables.items():
                excel_file_path=f"output/{class_}.xlsx"
                zipf.write(excel_file_path,arcname=os.path.basename(excel_file_path))
                # os.remove(excel_file_path)
        col1,col2=st.columns([1,3])
        with col1:
            st.download_button("保存在一个文件中",open("课程表.xlsx","rb"),file_name="课程表.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            st.download_button("保存为多个文件",zip_buffer.getvalue(),file_name="课程表.zip",mime="application/zip")