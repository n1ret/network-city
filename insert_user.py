from backendtypes import DataBase, get_default_password_hash, get_default_password, next_available_login
import argparse

parser = argparse.ArgumentParser(prog="python3 insert_user.py")

parser.add_argument("fullname", nargs=2)
parser.add_argument("school_class", nargs='?', default="")
parser.add_argument("-t", "--teacher", action="store_true")

args = parser.parse_args()

fullname = ' '.join(args.fullname)

with DataBase() as db:
    used_logins = db.get_used_logins()
    login = next_available_login(used_logins, fullname)
    password_hash = get_default_password_hash(login)
    uid = db.insert_or_update_user(
        fullname, args.school_class, login, password_hash, args.teacher
    )

print(f"Created user #{uid}\n Fullname: {fullname}\n Login: {login}\n Password: {get_default_password(login)}")