# 导入必要的模块
import streamlit as st, menu, pandas as pd, random, copy, tomllib, zipfile, os, json
from io import BytesIO
# noinspection PyUnresolvedReferences
from menu import generate_time, days

class Teacher:
    """
    教师类，用于管理教师的课程时间
    """
    def __init__(self, name):
        """
        初始化教师对象

        :param name: 教师姓名
        """
        self.name = name
        self.lessons_time = []  # 记录教师已占用的课程时间

    def add_lesson_time(self, day, lesson, week):
        """
        添加教师的课程时间

        :param day: 星期几
        :param lesson: 课程节次
        :param week: 单周/双周/全周
        """
        self.lessons_time.append((day, lesson, week))

    def is_busy(self, day, lesson, week="all"):
        """
        检查教师在特定时间是否有课

        :param day: 星期几
        :param lesson: 课程节次
        :param week: 单周/双周/全周
        :return: 是否有课
        """
        return (day, lesson, week) in self.lessons_time

def add_lesson(class_: str, day: int, lesson: int, subject: str, week="all", mode="replace", remove=True) -> bool:
    """
    为指定班级的课程表添加课程

    :param class_: 班级名称
    :param day: 星期几
    :param lesson: 课程节次
    :param subject: 学科
    :param week: 单周/双周/全周
    :param mode: 添加模式（替换/追加）
    :param remove: 是否从可选课程中移除
    :return: 是否成功添加课程
    """
    global table, teachers, class_subjects, special_subjects

    # 处理星期索引
    day-=1
    # 周类型映射
    week_map = {"single": "单 ", "double": "双 ", "all": ""}

    # 获取该课程的任课教师
    teacher = dict_lessons[class_][subject + " - 任课老师"]

    # 检查教师是否有空，以及课程是否在可选课程中
    if teachers[teacher].is_busy(day, lesson) or subject not in class_subjects:
        return False

    # 获取课程时间描述
    time = generate_time(lesson)

    # 根据模式添加课程
    if mode == "replace":
        table[day][time] = week_map[week] + subject
    else:
        table[day][time] += "\n" + week_map[week] + subject

    # 如果设置显示教师，则添加教师姓名
    if settings["show_teachers"]:
        table[day][time] += "\n（%s）" % teacher

    # 记录教师课程时间
    teachers[teacher].add_lesson_time(day, lesson, week)

    # 从可选课程中移除（如果需要）
    if subject in class_subjects and remove:
        class_subjects.remove(subject)

    return True

if __name__ == '__main__':
    # 调用菜单函数
    menu.menu()

    # 设置页面标题
    st.title("生成")

    # 读取配置文件
    with open("settings.toml", "br") as f:
        settings = tomllib.load(f)

        # 检查是否已配置课程信息
        if "lessons_info" not in settings:
            st.error("请先在设置中配置课程信息")
            st.stop()

        # 解析课程信息
        lessons = json.loads(settings["lessons_info"])
        dict_lessons = {}
        for i in range(len(lessons)):
            dict_lessons[lessons[i]["班级"]] = lessons[i]

        # 创建课程表基础样式
        pd_lessons = pd.DataFrame(lessons)
        table_style = []

        for day in range(5):
            table_style.append({"星期": days[day+1]})
            for time in range(1, settings["morning_class_num"] + 1):
                table_style[day].update({f"上午第{time}节": "info"})
            for time in range(1, settings["afternoon_class_num"] + 1):
                table_style[day].update({f"下午第{time}节": "info"})

        subjects = settings["subjects_info"]
        settings["rules"]["priority"] = json.loads(settings["rules"]["priority"])

    # 初始化教师字典
    class_tables = {}
    teachers = {lessons[class_][subject + " - 任课老师"]: Teacher(lessons[class_][subject + " - 任课老师"])
                for class_ in range(len(lessons)) for subject in subjects}

    # 生成课程表按钮
    if st.button("生成课程表"):
        for class_ in dict_lessons:
            continue_loop = True
            old_teachers = copy.deepcopy(teachers)

            # 尝试生成课程表，如果失败则重试
            while continue_loop:
                continue_loop = False
                teachers = copy.deepcopy(old_teachers)
                table = copy.deepcopy(table_style)
                class_subjects = []
                special_subjects = []

                # 处理课程信息
                for subject in subjects:
                    if not dict_lessons[class_][subject + " - 课时"] is None:
                        if subject.endswith("(0.5)") or subject.endswith("（0.5）"):
                            special_subjects.append(subject)
                        elif subject in settings["rules"]["must_include"]:
                            for i in range(int(float(dict_lessons[class_][subject + " - 课时"])) - 5):
                                class_subjects.append(subject)
                        else:
                            for i in range(int(float(dict_lessons[class_][subject + " - 课时"]))):
                                class_subjects.append(subject)

                # 处理0.5课时科目
                if len(special_subjects) > 0:
                    class_subjects.append(special_subjects)

                # 处理优先级配置
                for subject in settings["rules"]["priority"]:
                    if not subject["enabled"]:
                        continue
                    for priority in range(1, len(subject) - 2):
                        day = eval(subject[str(priority)])[0]
                        lesson = eval(subject[str(priority)])[1]
                        if day and lesson:
                            add_lesson(class_, day, lesson, subject["subject"])

                class_subjects
                st.table(pd.DataFrame(table).transpose())  # debug
                # 生成课程表
                for day in range(1,6):
                    must_lessons = []

                    # 处理每天必须包含的课程
                    for must_include in settings["rules"]["must_include"]:
                        must_lesson = random.choice(list(set(range(1, settings["morning_class_num"] + settings["afternoon_class_num"] + 1)) - set(must_lessons)))
                        successful = add_lesson(class_, day, must_lesson, must_include, remove=False)
                        while not successful:
                            must_lesson = random.choice(list(set(range(1, settings["morning_class_num"] + settings["afternoon_class_num"] + 1)) - set(must_lessons)))
                            successful = add_lesson(class_, day, must_lesson, must_include, remove=False)
                        must_lessons.append(must_lesson)


                    # 填充剩余课程
                    for lesson in range(1, settings["morning_class_num"] + settings["afternoon_class_num"] + 1):
                        if lesson in must_lessons or lesson=="info":
                            continue

                        class_subjects
                        st.table(pd.DataFrame(table).transpose())  # debug
                        subject = random.choice(class_subjects)

                        # 处理0.5课时科目
                        if type(subject) == list:
                            successful = (add_lesson(class_, day, lesson, subject[0], "single") and
                                          add_lesson(class_, day, lesson, subject[1], "double", "append")) or \
                                         (add_lesson(class_, day, lesson, subject[0], "double") and
                                          add_lesson(class_, day, lesson, subject[1], "single", "append"))
                            if successful:
                                class_subjects.remove(subject)
                        else:
                            successful = add_lesson(class_, day, lesson, subject)

                        # 如果添加失败，重试
                        tries = 0
                        while not successful:
                            subject = random.choice(class_subjects)
                            if type(subject) == list:
                                successful = (add_lesson(class_, day, lesson, subject[0], "single") and
                                              add_lesson(class_, day, lesson, subject[1], "double", "append")) or \
                                             (add_lesson(class_, day, lesson, subject[0], "double") and
                                              add_lesson(class_, day, lesson, subject[1], "single", "append"))
                                if successful:
                                    class_subjects.remove(subject)
                            else:
                                successful = add_lesson(class_, day, lesson, subject)

                            tries += 1
                            if tries >= 100:
                                continue_loop = True
                                break

                        if continue_loop:
                            break

                    if continue_loop:
                        break

            # 显示课程表
            st.subheader(class_ + "课程表")
            if settings["transpose"]:
                table = pd.DataFrame(table)
                st.dataframe(table, hide_index=True)
            else:
                table = pd.DataFrame(table).transpose()
                st.dataframe(table)

            class_tables[class_] = table

        # 保存课程表
        if not os.path.exists("output"):
            os.mkdir("output")

        # 保存到Excel文件
        with pd.ExcelWriter("课程表.xlsx") as writer:
            for class_, table in class_tables.items():
                table.to_excel(writer, sheet_name=class_, index=not settings["transpose"])
                table.to_excel(f"output/{class_}.xlsx", index=not settings["transpose"])

        # 压缩课程表文件
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for class_, table in class_tables.items():
                excel_file_path = f"output/{class_}.xlsx"
                zipf.write(excel_file_path, arcname=os.path.basename(excel_file_path))

        # 提供下载按钮
        col1, col2 = st.columns([1, 3])
        with col1:
            st.download_button(
                "保存在一个文件中",
                open("课程表.xlsx", "rb"),
                file_name="课程表.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            st.download_button(
                "保存为多个文件",
                zip_buffer.getvalue(),
                file_name="课程表.zip",
                mime="application/zip"
            )