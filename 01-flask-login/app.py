from flask import Flask, render_template, request, redirect, session
from datetime import timedelta
import hashlib
import time

app = Flask(__name__)
app.secret_key = "dev-key-2025"

# ===== session 超时设置（修复 #5）=====
app.permanent_session_lifetime = timedelta(minutes=30)


def sha256(password):
    """返回 SHA256 哈希值"""
    return hashlib.sha256(password.encode()).hexdigest()


# ===== 登录频率限制（修复 #3）=====
LOGIN_ATTEMPTS = {}  # key: IP, value: {"count": int, "lockout_until": float}
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60


def check_rate_limit(ip):
    """检查 IP 是否被锁定"""
    now = time.time()
    record = LOGIN_ATTEMPTS.get(ip)
    if record:
        if record["lockout_until"] and now < record["lockout_until"]:
            remaining = int(record["lockout_until"] - now)
            return False, f"登录过于频繁，请等待 {remaining} 秒后再试"
        if record["lockout_until"] and now >= record["lockout_until"]:
            # 锁定时间已过，重置
            del LOGIN_ATTEMPTS[ip]
    return True, ""


def record_failed_attempt(ip):
    """记录一次失败尝试"""
    now = time.time()
    record = LOGIN_ATTEMPTS.get(ip)
    if record:
        record["count"] += 1
        if record["count"] >= MAX_ATTEMPTS:
            record["lockout_until"] = now + LOCKOUT_SECONDS
    else:
        LOGIN_ATTEMPTS[ip] = {"count": 1, "lockout_until": None}


def reset_rate_limit(ip):
    """登录成功后清除记录"""
    LOGIN_ATTEMPTS.pop(ip, None)


# ===== 用户数据库 - 密码已做 SHA256 哈希（修复 #1）=====
USERS = {
    "admin": {
        "username": "admin",
        "password": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
        "role": "admin",
        "email": "admin@example.com",
        "phone": "13800138000",
        "balance": 99999
    },
    "alice": {
        "username": "alice",
        "password": "f9353d7664a88f84150c0289351539ee2f5b86c897110f482e4cd5afec3b277a",
        "role": "user",
        "email": "alice@example.com",
        "phone": "13900139001",
        "balance": 100
    }
}


@app.route("/")
def index():
    """首页：若已登录则显示用户信息，否则提示未登录"""
    username = session.get("username")
    user = USERS.get(username) if username else None
    # 移除密码字段，避免泄露到前端
    safe_user = {k: v for k, v in user.items() if k != "password"} if user else None
    return render_template("index.html", user=safe_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    """登录页面：GET 显示表单，POST 验证身份"""
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        client_ip = request.remote_addr or "unknown"

        # 频率限制检查
        ok, msg = check_rate_limit(client_ip)
        if not ok:
            return render_template("login.html", error=msg)

        # 校验用户名是否存在
        user = USERS.get(username)
        if not user:
            record_failed_attempt(client_ip)
            return render_template("login.html", error="用户名不存在")

        # 使用哈希比对密码
        if user["password"] != sha256(password):
            record_failed_attempt(client_ip)
            return render_template("login.html", error="密码错误")

        # 登录成功
        reset_rate_limit(client_ip)
        session.permanent = True  # 启用 session 超时
        session["username"] = username
        # 不将密码传递到模板
        safe_user = {k: v for k, v in user.items() if k != "password"}
        return render_template("index.html", user=safe_user)

    return render_template("login.html")


@app.route("/logout")
def logout():
    """登出：清除 session 并重定向到首页"""
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
