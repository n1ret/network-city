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
from mysql.connector import connect
import os
from dotenv import load_dotenv
import backendtypes as types
import utils
import sys

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = Flask(
    "diary",
    static_folder=os.path.join(sys.path, "static"),
    template_folder=os.path.join(sys.path, "templates"),
)
app.secret_key = os.environ.get("SECRET_KEY")

app.debug = bool(os.environ.get("DEBUG_MODE"))
if app.debug:
    app.templates_auto_reload = True


@app.before_request
def make_session_permanent():
    session.permanent = True
    if "is_logged" not in session:
        session["is_logged"] = False
        session.modified = True
    else:
        if session["is_logged"]:
            with types.DataBase() as db:
                usr=db.get_user_by_id(session["user_id"])
            if not(usr):
                return redirect("/logout")
            if usr.password_hash!=session["password_hash"]:
                return redirect("/logout")


@app.route("/api/login", methods=["POST"])
def api_login():
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

    with types.DataBase() as db:
        usr = db.get_user_by_logpas(req["login"], req["paswd"])
    if not (usr):
        return jsonify({"ok": False, "error": "Неверный логин или пароль"})

    session["is_logged"] = True
    session["user_id"] = usr.uid
    session["password_hash"] = usr.password_hash
    session.modified = True
    return jsonify({"ok": True, "error": ""})

@app.route("/api/change_pass")
def api_change_pass():
    req = request.json
    if "user_id" not in req or "old" not in req or "new" not in req:
        return make_response(
            jsonify({"ok": False, "error": "Ошибка в параметрах запроса"}), 400
        )
    
    for pas in (req["old"],req["new"]):
        match = re.match(
            r"([a-fA-F\d]{32})", pas
        )  # check if password is valid md5 string
        if not (match) or match.group(0) != pas:
            return make_response(
                jsonify({"ok": False, "error": "Некорректный пароль"}), 400
            )
    
    with types.DataBase() as db:
        usr=db.get_user_by_id(req["user_id"])
    
    if not (usr):
        return jsonify({"ok": False, "error": "Пользователь не найден"})
    
    if usr.password_hash!=req["old"]:
        return jsonify({"ok": False, "error":"Неверный пароль"})
    
    with types.DataBase() as db:
        db.update_user_password(req["user_id"], req["new"])
    
    return jsonify({"ok":True,"error":""})


@app.route("/")
def main():
    if session.get("is_logged"):
        with types.DataBase() as db:
            usr = db.get_user_by_id(session.get("user_id"))
            if not (usr):
                return redirect("/logout")
            lessons = db.get_user_lessons(usr.uid)

        ctx = utils.get_context(lessons)
        ctx.fullname = usr.fullname
        ctx.user_id = usr.uid
        ctx.last_update = utils.get_last_parse_timestamp()

        return render_template("index.html", ctx=ctx)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if app.debug:
    app.run(host="0.0.0.0", port=8800)
