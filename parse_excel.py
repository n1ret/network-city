from time import time
from json import dump, load
from os import PathLike, path
from numpy import nan
from datetime import datetime
import pickle

import pandas as pd

from backendtypes import DataBase
from backendtypes import Mark

DATA_FILE = 'data.json'


def parse_table(school_class: str, excel_table: PathLike | bytes, db: DataBase):
    """Parse excel table with marks

    Args:
        school_class (str): class num and letter like "10 Д"
        excel_table (PathLike | bytes): excel table
        db (DataBase): mysql database
    """
    sheets = pd.read_excel(excel_table, None, header=None)
    for lesson in sheets.keys():
        df = sheets.get(lesson, None)

        if len(df.columns) == 0:
            raise ValueError(f"No columns found on sheet {lesson}")

        end=0
        for row in df.index:
            if df[0][row]=="Тема урока":
                end=row-1
                break
        if end==0:
            raise ValueError("'Тема урока' not found")
        
        fullnames = [str(name).split(".", 1)[-1].strip() for name in df[0][1:end] if name is not nan]
        user_ids = db.convert_fullnames_to_user_ids(fullnames, school_class)

        users_marks = [[] for _ in range(len(fullnames))]
        marks = df.loc[:end, 1:]
        for _, column in marks.items():
            date = column[0]
            if not isinstance(date, datetime):
                raise TypeError(f"Firts row must contain datetime.datetime, founded: {type(date)}")
            for i, mark in enumerate(column[1:]):
                if mark is nan:
                    continue
                if str(mark).isdigit():
                    mark = int(mark)
                else:
                    mark = str(mark).upper()

                users_marks[i].append(Mark(int(date.timestamp()), mark))

        db.insert_or_update_lesson(
            user_ids, lesson, (pickle.dumps(marks_list) for marks_list in users_marks)
        )

    update_json(DATA_FILE)


def update_json(file_name):
    file_path = path.join(path.dirname(__file__), file_name)
    if path.isfile(file_path):
        with open(file_path) as f:
            data_json = load(f)
        if not isinstance(data_json, dict):
            data_json = {}
    else:
        data_json = {}

    data_json.update({
        'last_parse': time()
    })
    with open(file_path, 'w') as f:
        dump(
            data_json,
            f
        )


if __name__ == "__main__":
    from sys import argv
    if len(argv) < 3:
        print(
            'Must be call with format:\n'
            f'{path.split(__file__)[1]} xlsx_file school_class'
        )
        exit(-1)
    parse_table(argv[2], argv[1], DataBase())
