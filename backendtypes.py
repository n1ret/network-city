from mysql import connector
import pickle
from dataclasses import dataclass, fields
from typing import List, Union, Optional, DefaultDict, get_args
import utils


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
    mark: int


@dataclass
class UserLesson(SqlModel):
    user_id: int
    lesson: str
    marks: Union[List[Mark], bytes]


@dataclass
class IndexPageContext:
    dates: List[str]
    lessons_names: List[str]
    marks: DefaultDict[DefaultDict[str]]
    user_id: int = 0
    fullname: str = ""
    last_update: str = ""


class DataBase:
    def __init__(self, host="127.0.0.1", database="", user="root", password="") -> None:
        self.con = connector.connect(
            user=user, password=password, host=host, database=database
        )
        self.q = self.con.cursor()

    def close(self):
        self.con.close()

    def _commit(self):
        self.con.commit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_user(
        self, login: str = "none", password_hash: str = "none", uid: int = -1
    ):
        self.q.execute(
            "SELECT * FROM users WHERE (login = %s AND password_hash = %s) OR uid = %s",
            (login, password_hash, uid),
        )
        res = self.q.fetchone()
        if not (res):
            return None
        return User(*res)

    def get_user_by_logpas(self, login: str, password_hash: str) -> Optional[User]:
        """Get User object using login and password_hash

        Returns:
            Optional[User]: None if user not found, otherwise User object
        """
        return self._get_user(login, password_hash)

    def get_user_by_id(self, user_id: int) -> User:
        """Get User object using unique user id

        Returns:
            User: User object
        """
        return self._get_user(uid=user_id)

    def get_user_lessons(self, user_id: int) -> List[UserLesson]:
        """Get list of UserLesson objects, containing info about lesson name and marks

        Returns:
            List[UserLesson]: List of UserLesson objects
        """
        self.q.execute("SELECT * FROM users_lessons WHERE user_id = %s", (user_id,))
        ans = []
        for userlessonraw in self.q.fetchall():
            userlesson = UserLesson(*userlessonraw)
            ans.append(userlesson)
        return ans
