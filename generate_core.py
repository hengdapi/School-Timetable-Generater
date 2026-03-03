import random,time
import traceback
from locals import *
from PyQt5.QtCore import QThread,pyqtSignal

def check(clas: Class,time: Time,subject: Subject) -> bool:
    try:
        logging.debug(f"检查能否在 {clas.name} 的 {time} 安排 {subject}")
        if subject.get_teacher(clas).is_busy(time):
            logging.debug(f"{subject} 的任课老师 {subject.get_teacher(clas).name} 在 {time} 有课")
            return False

        for rule in rules:
            # 不能排在指定时间
            if rule.type==Rule_type.avoid_time:
                # 支持只写节次（如"上午第4节"）
                if rule.subject==subject and time==rule.time:
                    logging.debug(f"{clas.name} 不能在 {time} 排 {subject}")
                    return False
            # 同一时间最多排几节课
            elif rule.type==Rule_type.set_num:
                if rule.subject==subject and subject.get_time_num(time)>=int(rule.number):
                    logging.debug(f"{clas.name} 同一时间 最多排 {rule.number} 节课")
                    return False
            # 学科不能与另一学科同一时间
            elif rule.type==Rule_type.avoid_subject:
                if subject==rule.subjectA and rule.subjectB.timetable.get(time):
                    logging.debug(f"已经在 {time} 安排了会引起冲突的 {rule.subjectB}")
                    return False
                if subject==rule.subjectB and rule.subjectA.timetable.get(time):
                    logging.debug(f"已经在 {time} 安排了会引起冲突的 {rule.subjectA}")
                    return False
            # 老师不能与另一老师同一时间有课
            elif rule.type==Rule_type.avoid_teacher:
                teacher=subject.get_teacher(clas)
                teacherA = rule.teacherA
                teacherB = rule.teacherB
                if teacher==teacherA and teacherB.timetable.get(time):
                    logging.debug(f"{clas.name} {subject} 的教师 {teacherA.name} 和 {teacherB.name} 在 {time} 会冲突")
                    return False
                elif teacher==teacherB and teacherA.timetable.get(time):
                    logging.debug(f"{clas.name} {subject} 的教师 {teacherB.name} 和 {teacherA.name} 在 {time} 会冲突")
                    return False
        logging.debug("可以安排")
        return True
    except:
        e=traceback.format_exc()
        logging.error(f"检查时出错：\n{e}")
        return False

class Generate_thread(QThread):
    finished_signal=pyqtSignal()  # 生成成功
    progress_signal=pyqtSignal(tuple)  # 进度信息

    def __init__(self,parent=None):
        super().__init__(parent)
        self.last_progress_time=0  # 记录上次发送进度的时间
        self.progress_interval=0.8  # 进度更新间隔（秒）

    def run(self):
        # 执行耗时的课程表生成逻辑
        try:
            results.__init__()
            logging.info("开始生成课程表...")
            # 1. 固定时间优先分配
            logging.debug("填充固定时间")
            for lesson in set_lessons:
                for clas in results.class_lst:
                    clas.add_lesson(lesson[0],lesson[1])

            # 2. 自动分配剩余课程
            logging.debug("开始dfs分配剩余课程")
            self.finish=False
            self.dfs(results.class_lst[0],Time(1,1))
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表时错误：\n{e}")
        self.finish=True
        self.finished_signal.emit()

    def should_emit_progress(self):
        """判断是否应该发送进度信号"""
        current_time=time.time()
        if current_time-self.last_progress_time>=self.progress_interval:
            self.last_progress_time=current_time
            return True
        return False

    def dfs(self,clas: Class,curr_time: Time):
        try:
            if self.finish:
                return
            if self.should_emit_progress():
                self.progress_signal.emit((clas,curr_time))
            last=False
            next_time=curr_time.all_week
            if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                if results.class_names[-1]==clas.name:
                    last=True
            elif curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                next_time.day+=1
                next_time.lesson=1
            else:
                next_time.lesson+=1
            logging.debug(f"计算下一时间：{next_time}")

            if not clas.get_lessons(curr_time):
                if curr_time in priority_subjects:
                    curr_priority=priority_subjects[curr_time]
                else:
                    curr_priority=[]
                logging.debug(f"当前优先课程：{[i.name for i in curr_priority]}")

                curr_subjects=set(clas.left_subjects)
                if curr_time.half:
                    curr_subjects&=half_subjects
                curr_subjects=list(curr_subjects)
                random.shuffle(curr_subjects)
                for subject in curr_subjects:
                    if subject in curr_priority:
                        curr_subjects.remove(subject)
                        curr_subjects.insert(0,subject)

                logging.debug(f"当前课程：{[i.name for i in curr_subjects]}")

                for subject in curr_subjects:
                    if subject in half_subjects and check(clas, curr_time.sin_week, subject):
                        clas.add_lesson(curr_time.sin_week,subject)
                        for subject2 in half_subjects&set(clas.left_subjects):
                            if check(clas, curr_time.dou_week, subject2):
                                clas.add_lesson(curr_time.dou_week,subject2)
                                if not last:
                                    if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                                        self.dfs(results.class_lst[results.class_names.index(clas.name)+1],Time(1,1))
                                    else:
                                        self.dfs(clas,next_time)
                                    if self.finish:
                                        return
                                    clas.remove_lesson(curr_time.dou_week,subject2)
                        clas.remove_lesson(curr_time.sin_week,subject)
                    elif subject not in half_subjects and check(clas, curr_time, subject):
                        add_continue=False
                        if subject in continue_subjects:
                            if clas.left_subjects.count(subject)==2 and (curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value or curr_time.lesson==cfg.morning_class_num.value):
                                continue
                            if clas.left_subjects.count(subject)==2:
                                plan=True
                            elif clas.left_subjects.count(subject)>2:
                                plan=random.choice([True,False])
                            else:
                                plan=False
                            if curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                                plan=False
                            if plan:
                                if check(clas,next_time,subject):
                                    clas.add_lesson(next_time,subject.to_continue_lesson())
                                    add_continue=True
                                else:
                                    continue
                        if add_continue:
                            clas.add_lesson(curr_time,subject.to_continue_lesson())
                        else:
                            clas.add_lesson(curr_time,subject)
                        if not last:
                            if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                                self.dfs(results.class_lst[results.class_names.index(clas.name)+1],Time(1,1))
                            else:
                                self.dfs(clas,next_time)
                            if self.finish:
                                return
                            clas.remove_lesson(curr_time,subject)
                            if add_continue:
                                clas.remove_lesson(next_time,subject)
            else:
                logging.debug(f"{curr_time}已存在课程")
                if not last:
                    if curr_time.day==5 and curr_time.lesson==cfg.morning_class_num.value+cfg.afternoon_class_num.value:
                        self.dfs(results.class_lst[results.class_names.index(clas.name)+1],Time(1,1))
                    else:
                        self.dfs(clas,next_time)
            if last and bool(clas.get_lessons(curr_time)):
                self.finish=True
        except:
            e=traceback.format_exc()
            logging.critical(f"生成课程表出错：\n{e}")

def generate_timetable(window):
    generate_thread=Generate_thread()
    generate_thread.finished_signal.connect(window.on_generation_finished)
    generate_thread.progress_signal.connect(window.on_progress_update)
    generate_thread.start()