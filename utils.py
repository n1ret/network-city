import json
from datetime import datetime, timezone, timedelta
from typing import List, Union
from backendtypes import IndexPageContext, UserLesson
from collections import defaultdict
import os
from hashlib import md5
from parse_schedule import parse


def get_md5(*args) -> str:
    s = "".join(map(str, args))
    return md5(s.encode()).hexdigest()


def parse_timestamp(timestamp: Union[float, int], fmt: str = "%d.%m"):
    t = datetime.fromtimestamp(timestamp, timezone(timedelta(hours=5)))
    return t.strftime(fmt)


def get_last_parse_timestamp(fmt: str = "%d.%m %H:%M") -> str:
    with open(os.path.join(os.path.dirname(__file__), "data.json")) as f:
        data = json.loads(f.read())
    return parse_timestamp(data["last_parse"], fmt)

def get_schedule_filename(date: datetime):
    return date.strftime("%d.%m.%Y.xlsx")

def get_today_tomorrow():
    today=datetime.now(tz=timezone(timedelta(hours=5)))
    if today.weekday()<4:
        tomorrow=today+timedelta(days=1)
        skipped_to="Завтра"
    else:
        days_ahead=7-today.weekday()
        tomorrow=today+timedelta(days=days_ahead)
        skipped_to="Понедельник"
    ans=[get_schedule_filename(today),get_schedule_filename(tomorrow)]
    for i,j in enumerate(ans):
        cpath=os.path.join(os.path.dirname(__file__), f"schedule/{j}")
        if not os.path.exists(cpath):
            ans[i]=""
        else:
            ans[i]=os.path.join(os.path.dirname(__file__), f"schedule/{j}")
    return ans, skipped_to


def get_context(lessons: List[UserLesson], classr="", with_schedule=True) -> IndexPageContext:
    dates = set()
    lessons_names = set()
    marks = defaultdict(lambda: defaultdict(str))  # marks[lesson_name][date]
    for lesson in lessons:
        cmarks=[]
        lessons_names.add(lesson.lesson)
        for mark in lesson.marks:
            date = parse_timestamp(mark.timestamp)
            dates.add(date)
            if marks[lesson.lesson][date]=="":
                marks[lesson.lesson][date] = str(mark.mark)
            else:
                marks[lesson.lesson][date] += " "+str(mark.mark)
            if type(mark.mark)==int:
                cmarks.append(mark.mark)
        if len(cmarks) == 0:
            marks[lesson.lesson]["Ср. Балл"] = ""
        else:
            avg = sum(cmarks) / len(cmarks)
            marks[lesson.lesson]["Ср. Балл"] = "{:.2f}".format(avg)
    lessons_names = sorted(list(lessons_names))
    dates = list(dates)
    dates.sort(key=lambda date: datetime.strptime(date, "%d.%m"))
    dates.append("Ср. Балл")

    schedules=[]

    if with_schedule:
        sched_date,skipped_to=get_today_tomorrow()
        for sched_date in sched_dates:
            schedules.append(parse(classr, sched_date))
    else:
        schedules=[None,None]

    return IndexPageContext(dates, lessons_names, marks,schedules[0],schedules[1],classr,skipped_to)
