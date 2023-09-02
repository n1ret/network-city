import json
import time
from datetime import datetime
from typing import List, Union
import backendtypes as types
from collections import defaultdict


def parse_timestamp(timestamp: Union[float, int], fmt: str = "%d.%m"):
    t = datetime.fromtimestamp(timestamp)
    return t.strftime(fmt)


def get_last_parse_timestamp(fmt: str = "%d.%m %H:%M") -> str:
    with open("data.json") as f:
        data = json.loads(f.read())
    return parse_timestamp(data["last_parse"], fmt)


def get_context(lessons: List[types.UserLesson]) -> types.IndexPageContext:
    dates = set()
    lessons_names = set()
    marks = defaultdict(lambda: defaultdict(str))  # marks[lesson_name][date]
    for lesson in lessons:
        lessons_names.add(lesson.lesson)
        for mark in lesson.marks:
            date = parse_timestamp(mark.timestamp)
            dates.add(date)
            marks[lesson.lesson][date] = mark.mark
    return types.IndexPageContext(dates, lessons_names, marks)
