from mysql import connector
import pickle
from dataclasses import dataclass, fields
from typing import List, Union, Optional, DefaultDict, get_args, Iterable, Set
import os
from dotenv import load_dotenv
from hashlib import md5

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")


class SqlModel:
    def __post_init__(self):
        for field in fields(self):
            val = getattr(self, field.name)
            if type(val) == bytes:
                setattr(self, field.name, pickle.loads(val))
            elif field.type == bool:
                setattr(self, field.name, bool(val))

    def fromsqlformat(self):
        self.__post_init__()
        return self

    def tosqlformat(self):
        for field in fields(self):
            if bytes in get_args(field.type):
                val = getattr(self, field.name)
                setattr(self, field.name, pickle.dumps(val))
        return self


@dataclass
class User(SqlModel):
    uid: int
    login: str
    password_hash: str
    is_teacher: bool
    classr: str
    fullname: str


@dataclass
class Mark:
    timestamp: int
    mark: Union[int, str]


@dataclass
class UserLesson(SqlModel):
    user_id: int
    lesson: str
    marks: Union[List[Mark], bytes]


@dataclass
class IndexPageContext:
    dates: List[str]
    lessons_names: List[str]
    marks: DefaultDict[str, DefaultDict[str, str]]
    user_id: int = 0
    classr: str = ""
    fullname: str = ""
    last_update: str = ""


@dataclass
class TeacherPageContext:
    classnames: List[str]
    user_id: int = 0
    fullname: str = ""
    last_update: str = ""
    classr: str = ""

def get_default_password(login: str) -> str:
    return md5(login.encode()).hexdigest()[:6]

def get_default_password_hash(login: str) -> str:
    password=get_default_password(login)
    hash=md5(password.encode()).hexdigest()
    return hash

def next_available_login(logins: Set[str], fullname: str) -> str:
    fname, lname = fullname.split()
    name = fname + lname[0]
    add = ""
    while name + add in logins:
        if add:
            add = str(int(add) + 1)
        else:
            add = "1"
    return name + add

class DataBase:
    def __init__(
        self, host="127.0.0.1", database="diary", user=db_user, password=db_password
    ) -> None:
        self.con = connector.connect(
            user=user, password=password, host=host, database=database
        )
        self.q = self.con.cursor()

        self.init_database()

    def close(self):
        self.con.close()

    def _commit(self):
        self.con.commit()

    def init_database(self):
        tables_file = os.path.join(os.path.dirname(__file__), "tables.sql")
        with open(tables_file) as f:
            tables = f.read()
        for _ in self.q.execute(tables, multi=True):
            ...
        self._commit()

    def _get_user(self):
        res = self.q.fetchone()
        if not (res):
            return None
        return User(*res)

    def get_user_by_logpas(self, login: str, password_hash: str) -> Optional[User]:
        """Get User object using login and password_hash

        Returns:
            Optional[User]: None if user not found, otherwise User object
        """
        self.q.execute(
            "SELECT * FROM users WHERE login = BINARY %s AND password_hash = %s",
            (login, password_hash),
        )
        return self._get_user()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get User object using unique user id

        Returns:
            Optional[User]: None if user not found, otherwise User object
        """
        self.q.execute("SELECT * FROM users WHERE uid = %s", (user_id,))
        return self._get_user()

    def get_user_lessons(self, user_id: int) -> List[UserLesson]:
        """Get list of UserLesson objects, containing info about lesson name and marks

        Returns:
            List[UserLesson]: List of UserLesson objects
        """
        self.q.execute("SELECT * FROM users_lesson WHERE user_id = %s", (user_id,))
        ans = []
        for userlessonraw in self.q.fetchall():
            userlesson = UserLesson(*userlessonraw)
            ans.append(userlesson)
        return ans

    def update_user_password(self, user_id: int, new_password: str):
        """Update user password_hash"""
        self.q.execute(
            "UPDATE users SET password_hash = %s WHERE uid = %s",
            (new_password, user_id),
        )
        self.con.commit()

    def get_users_by_class(self, classr) -> List[User]:
        self.q.execute("SELECT * FROM users WHERE class = %s AND is_teacher = 0", (classr,))
        ans = []
        for user in self.q.fetchall():
            ans.append(User(*user))
        ans.sort(key=lambda i: i.fullname)
        return ans

    def get_all_classes(self) -> List[str]:
        self.q.execute("SELECT distinct class FROM users")
        ans = []
        for classr in self.q.fetchall():
            if classr[0] == "":
                continue
            ans.append(classr[0])
        ans.sort(key=lambda i: (int(i.split()[0]), i.split()[1]))
        return ans

    def insert_or_update_user(
        self,
        fullname: str,
        school_class: str,
        login: str = "",
        password_hash: str = "",
        is_teacher: bool = False,
    ) -> int:
        """
        Raises:
            ValueError: Must be login and password_hash or no one of this

        Returns:
            int: inserted user id
        """
        if not all((login, password_hash)) and any((login, password_hash)):
            raise ValueError("Must be login and password_hash or no one of this")
        self.q.execute(
            """
            INSERT INTO users(fullname, class, login, password_hash, is_teacher)
            VALUES(%(0)s, %(1)s, %(2)s, %(3)s, %(4)s)
            ON DUPLICATE KEY UPDATE
            login=%(2)s, password_hash=%(3)s, is_teacher=%(4)s
            """,
            {
                str(i): param
                for i, param in enumerate(
                    (fullname, school_class, login, password_hash, is_teacher)
                )
            },
        )
        self._commit()
        self.q.execute("SELECT LAST_INSERT_ID()")
        return self.q.fetchone()[0]

    def get_used_logins(self):
        self.q.execute("SELECT login FROM users")
        return set([lgn for lgn, in self.q.fetchall()])

    def convert_fullnames_to_user_ids(
        self, user_fullnames: tuple[str], school_class: str
    ):
        user_ids = []
        used_logins = self.get_used_logins()
        for user_fullname in user_fullnames:
            self.q.execute(
                "SELECT uid FROM users WHERE fullname LIKE %s AND class = %s",
                (user_fullname, school_class),
            )
            user_id = self.q.fetchone()
            if user_id is None:
                login = next_available_login(used_logins, user_fullname)
                password_hash = get_default_password_hash(login)
                user_id = self.insert_or_update_user(
                    user_fullname, school_class, login=login,password_hash=password_hash
                )
            else:
                user_id = user_id[0]
            user_ids.append(user_id)
        return user_ids

    def insert_or_update_lesson(
        self, user_ids: tuple[int], lesson: str, users_marks: Iterable[bytes]
    ):
        self.q.executemany(
            (
                "INSERT INTO users_lesson(user_id, lesson, marks) VALUES(%s, %s, %s)"
                "ON DUPLICATE KEY UPDATE marks=VALUES(marks)"
            ),
            tuple(zip(user_ids, [lesson] * len(user_ids), users_marks)),
        )
        self._commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
