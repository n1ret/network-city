import json
import time
from datetime import datetime, timezone, timedelta
from typing import List, Union
import backendtypes as btypes
from collections import defaultdict
import os
from hashlib import md5

def get_md5(*args) -> str:
    s="".join(map(str,args))
    return md5(s.encode()).hexdigest()

def parse_timestamp(timestamp: Union[float, int], fmt: str = "%d.%m"):
    t = datetime.fromtimestamp(timestamp, timezone(timedelta(hours=5)))
    return t.strftime(fmt)


def get_last_parse_timestamp(fmt: str = "%d.%m %H:%M") -> str:
    with open(os.path.join(os.path.dirname(__file__), "data.json")) as f:
        data = json.loads(f.read())
    return parse_timestamp(data["last_parse"], fmt)


def get_context(lessons: List[btypes.UserLesson]) -> btypes.IndexPageContext:
    dates = set()
    lessons_names = set()
    marks = defaultdict(lambda: defaultdict(str))  # marks[lesson_name][date]
    for lesson in lessons:
        lessons_names.add(lesson.lesson)
        for mark in lesson.marks:
            date = parse_timestamp(mark.timestamp)
            dates.add(date)
            marks[lesson.lesson][date] = mark.mark
    return btypes.IndexPageContext(dates, lessons_names, marks)
