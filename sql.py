from typing import Iterable

from mysql import connector


class DataBase:
    def __init__(self, host='127.0.0.1', database='', user='root', password='') -> None:
        self.host = host
        self.database = database
        self.user = user
        self.password = password

        self.init_database()

    def connect(self, with_database=False):
        kwargs = {}
        if with_database:
            kwargs['database'] = self.database
        return connector.connect(
            user=self.user, password=self.password,
            host=self.host, **kwargs
        )

    def init_database(self):
        tables = """
        CREATE TABLE IF NOT EXISTS users (
            uid mediumint unsigned AUTO_INCREMENT,
            login varchar(128),
            password_hash varchar(32),
            fullname varchar(128),
            class varchar(4),
            is_teacher bool DEFAULT 0,

            PRIMARY KEY (uid),
            UNIQUE (fullname)
        );
        CREATE TABLE IF NOT EXISTS users_lesson (
            user_id mediumint unsigned,
            lesson varchar(64),
            marks blob
        )
        """
        with self.connect() as connection, connection.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} DEFAULT CHARACTER SET 'utf8'")
            connection.database = self.database
            for _ in cur.execute(tables, multi=True): ...

    def insert_or_update_user(
        self, fullname: str, login: str = '', password_hash: str = '',
        school_class: str = '', is_teacher: bool = False
    ) -> int:
        """
        Raises:
            ValueError: Must be login and password_hash or no one of this

        Returns:
            int: inserted user id
        """
        if (
            not all((login, password_hash)) and
            any((login, password_hash))
        ):
            raise ValueError("Must be login and password_hash or no one of this")
        with self.connect(with_database=True) as connection, connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users(fullname, login, password_hash, is_teacher, class)
                VALUES(%(0)s, %(1)s, %(2)s, %(3)s, %(4)s)
                ON DUPLICATE KEY UPDATE
                login=%(1)s, password_hash=%(2)s, is_teacher=%(3)s, class=%(4)s
                """,
                {str(i): param for i, param in enumerate(
                    (fullname, login, password_hash, is_teacher, school_class)
                )}
            )
            cur.execute("SELECT LAST_INSERT_ID()")
            return cur.fetchone()[0]

    def convert_fullnames_to_user_ids(self, user_fullnames: tuple[str]):
        user_ids = []
        with self.connect(with_database=True) as connection, connection.cursor() as cur:
            for user_fullname in user_fullnames:
                cur.execute(
                    "SELECT uid FROM users WHERE fullname LIKE %s",
                    user_fullname
                )
                user_id = cur.fetchone()
                if user_id is None:
                    user_id = self.insert_or_update_user(user_fullname)
                user_ids.append(user_id[0])
        return user_ids

    def insert_or_update_lesson(self, user_ids: tuple[int], lesson: str, users_marks: Iterable[bytes]):
        with self.connect(with_database=True) as connection, connection.cursor() as cur:
            cur.executemany(
                "INSERT INTO users_lesson(user_id, lesson, marks) VALUES(%s, %s, %s)",
                zip(user_ids, [lesson]*len(user_ids), users_marks)
            )
