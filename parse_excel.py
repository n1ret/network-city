from time import time
from json import dump, load
from os import PathLike, path
from numpy import nan
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import pickle

import pandas as pd

from sql import DataBase

DATA_FILE = 'data.json'


@dataclass
class Mark:
    timestamp: int
    mark: Optional[int]


def parse_table(excel_table: PathLike | bytes, db: DataBase):
    """Parse excel table with marks

    Args:
        excel_table (PathLike | bytes): excel table
    """
    sheets = pd.read_excel(excel_table, None, header=None)
    for lesson in sheets.keys():
        ...
    lesson = 'Русский яз'
    df = sheets.get(lesson, None)

    if len(df.columns) == 0:
        raise ValueError(f"No columns found on sheet {lesson}")
    if len(df.index) < 40:
        raise ValueError(f"Not all raws on sheet {lesson}")

    fullnames = [name for name in df[0][1:39] if name is not nan]
    user_ids = db.convert_fullnames_to_user_ids(fullnames)

    users_marks = [[] for _ in range(len(fullnames))]
    marks = df.loc[:38, 1:]
    for _, column in marks.items():
        date = column[0]
        if not isinstance(date, datetime):
            raise TypeError(f"Firts raw must contain datetime.datetime, founded: {type(date)}")
        for i, mark in enumerate(column[1:]):
            if mark is not nan:
                users_marks[i] = Mark(int(date.timestamp()), mark)

    db.insert_or_update_lesson(
        user_ids, lesson, (pickle.dumps(marks_list) for marks_list in users_marks)
    )

    update_json(DATA_FILE)


def update_json(file_name):
    if path.isfile(file_name):
        with open(file_name) as f:
            data_json = load(f)
        if not isinstance(data_json, dict):
            data_json = {}
    else:
        data_json = {}

    data_json.update({
        'last_parse': time()
    })
    with open(file_name, 'w') as f:
        dump(
            data_json,
            f
        )
