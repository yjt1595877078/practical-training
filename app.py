from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "dev-key-2025"

# 用户数据库 - 明文密码
USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "email": "admin@example.com",
        "phone": "13800138000",
        "balance": 99999
    },
    "alice": {
        "username": "alice",
        "password": "alice2025",
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

        # 校验用户名是否存在
        user = USERS.get(username)
        if not user:
            return render_template("login.html", error="用户名不存在")

        # 明文比对密码
        if user["password"] != password:
            return render_template("login.html", error="密码错误")

        # 登录成功，存入 session 并跳转首页
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
