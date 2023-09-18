from time import time
from json import dump, load
from os import PathLike, path
from numpy import nan,float64
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
    sheets2 = pd.ExcelFile(excel_table).book.worksheets

    allids=set()
    relevant_lessons=[]
    for sheet in sheets2:
        if sheet.sheet_state=="hidden":
            continue

        lesson=sheet.title
        relevant_lessons.append(lesson)

        df = sheets.get(lesson, None)

        if len(df.columns) == 0:
            raise ValueError(f"No columns found on sheet {lesson}")
        
        df[0].replace('', nan, inplace=True)
        sc=0
        if type(df.loc[0][0])!=str:
            sc=1
        df[sc].replace('', nan, inplace=True)
        df.dropna(subset=[sc], how='all', inplace=True,ignore_index=True)
        df.dropna(axis=1, how='all', inplace=True)

        end=-1
        for row in df.index:
            try:
                if df[sc][row].lower().strip() in ("тема урока","д\з",):
                    end=row-1
                    break
            except:
                raise ValueError(f"Add '{df[sc][row]}' to exceptions list. Please, contact @btless")
        if end==-1:
            raise ValueError(f"'Тема урока' not found on sheet {lesson}")
        
        fullnames = [''.join([i for i in str(name) if not i.isdigit()]).strip().strip(".").strip() for name in df[0][sc+1:end]]
        
        if len(fullnames)==0:
            continue
        user_ids = db.convert_fullnames_to_user_ids(fullnames, school_class)

        for usid in user_ids:
            allids.add(usid)

        users_marks = [[] for _ in range(len(fullnames))]
        marks = df.loc[:end, sc+1:]
        for ind, (_, column) in enumerate(marks.items()):
            date = column[0]
            if date is nan:
                break
            if not isinstance(date, datetime):
                date=datetime().now().replace(day=date)
            for i, mark in enumerate(column[1:]):
                if i > len(fullnames)-1: break
                if mark is nan or mark is None or mark is pd.NaT:
                    continue
                if type(mark) == datetime:
                    mark = mark.day
                else:
                    if str(mark).isdigit():
                        mark = int(mark)
                    elif len(str(mark))<=3:
                        mark = str(mark).upper()

                users_marks[i].append(Mark(int(date.timestamp()), mark))

        db.insert_or_update_lesson(
            user_ids, lesson, (pickle.dumps(marks_list) for marks_list in users_marks)
        )
    db.delete_irrelevant_lessons(tuple(relevant_lessons),tuple(user_ids))
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
