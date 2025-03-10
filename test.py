import pandas as pd

# 输入数据
settings = {
    "rules": {
        "priority": '{"数学":[1, 2], "英语":[3, 4], "物理":[5, 6], "化学":[2, 5]}'
    }
}

# 初始化课程表
class Schedule:
    def __init__(self, days=5, periods=7):
        self.days = days
        self.periods = periods
        self.schedule = pd.DataFrame([[None for _ in range(periods)] for _ in range(days)],
                                    index=[f"第{i+1}天" for i in range(days)],
                                    columns=[f"第{j+1}节" for j in range(periods)])

    def add_course(self, course, period):
        day, period = period // self.periods, period % self.periods
        if self.schedule.iloc[day, period] is None:
            self.schedule.iloc[day, period] = course
            return True
        return False

# 解析优先级规则
priority_rules = eval(settings["rules"]["priority"].replace("null", "None"))

# 创建排课实例
schedule = Schedule()

# 将优先级高的课程优先安排
for course, periods in sorted(priority_rules.items(), key=lambda x: len(x[1])):
    for period in periods:
        if schedule.add_course(course, period):
            break

# 调整课程表以适应所有课程
courses_to_add = list(set(priority_rules.keys()) - set(schedule.schedule.values.flatten()))
for course in courses_to_add:
    added = False
    for day in range(schedule.days):
        for period in range(schedule.periods):
            if schedule.add_course(course, day * schedule.periods + period):
                added = True
                break
        if added:
            continue

# 输出课程表
print(schedule.schedule)
