CREATE TABLE IF NOT EXISTS users (
    uid mediumint unsigned AUTO_INCREMENT,
    login varchar(128),
    password_hash varchar(32),
    fullname varchar(128),
    class varchar(4),
    is_teacher bool DEFAULT 0,

    PRIMARY KEY (uid),
    UNIQUE KEY (fullname, class)
);
CREATE TABLE IF NOT EXISTS users_lesson (
    user_id mediumint unsigned,
    lesson varchar(64),
    marks blob
);