from flask import Flask, render_template, request, redirect, session, send_from_directory, abort
from datetime import timedelta
import hashlib
import time
import sqlite3
import os
import secrets
import urllib.request
import urllib.error

app = Flask(__name__)
app.secret_key = "dev-key-2025"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ===== session 超时设置（修复 #5）=====
app.permanent_session_lifetime = timedelta(minutes=30)

# ===== 数据库初始化 =====
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "users.db")


def init_db():
    """初始化 SQLite 数据库"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        phone TEXT
    )""")
    # 添加 balance 列（如已存在则忽略）
    try:
        c.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # 列已存在
    # 插入默认用户（密码明文存储）
    c.execute("INSERT OR IGNORE INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)",
              ("admin", "admin123", "admin@example.com", "13800138000"))
    c.execute("INSERT OR IGNORE INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)",
              ("alice", "alice2025", "alice@example.com", "13900139001"))
    conn.commit()
    conn.close()
    # 创建上传目录
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    print("✅ 数据库初始化完成")


init_db()


def sha256(password):
    """返回 SHA256 哈希值"""
    return hashlib.sha256(password.encode()).hexdigest()


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ===== 登录频率限制（修复 #3）=====
LOGIN_ATTEMPTS = {}
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60


def check_rate_limit(ip):
    now = time.time()
    record = LOGIN_ATTEMPTS.get(ip)
    if record:
        if record["lockout_until"] and now < record["lockout_until"]:
            remaining = int(record["lockout_until"] - now)
            return False, f"登录过于频繁，请等待 {remaining} 秒后再试"
        if record["lockout_until"] and now >= record["lockout_until"]:
            del LOGIN_ATTEMPTS[ip]
    return True, ""


def record_failed_attempt(ip):
    now = time.time()
    record = LOGIN_ATTEMPTS.get(ip)
    if record:
        record["count"] += 1
        if record["count"] >= MAX_ATTEMPTS:
            record["lockout_until"] = now + LOCKOUT_SECONDS
    else:
        LOGIN_ATTEMPTS[ip] = {"count": 1, "lockout_until": None}


def reset_rate_limit(ip):
    LOGIN_ATTEMPTS.pop(ip, None)


# ===== CSRF 防护 =====
def generate_csrf_token():
    """生成并存储 CSRF Token"""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def validate_csrf():
    """验证 CSRF Token"""
    token = request.form.get("_csrf_token", "")
    stored = session.get("_csrf_token", "")
    if not token or not stored or token != stored:
        abort(403, "CSRF Token 无效")


@app.context_processor
def inject_csrf_token():
    """向模板注入 CSRF Token"""
    return dict(csrf_token=generate_csrf_token)


# ===== 用户数据库 - 内存字典 =====
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

    # 如果不在内存字典中，尝试从 SQLite 查询
    if not user and username:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            user = {
                "username": row["username"],
                "email": row["email"],
                "phone": row["phone"]
            }

    safe_user = {k: v for k, v in user.items() if k != "password"} if user else None
    # 获取搜索结果（如果有）
    search_results = session.pop("search_results", None)
    search_keyword = session.pop("search_keyword", None)
    return render_template("index.html", user=safe_user, search_results=search_results, search_keyword=search_keyword)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        client_ip = request.remote_addr or "unknown"

        ok, msg = check_rate_limit(client_ip)
        if not ok:
            return render_template("login.html", error=msg)

        # 先检查内存字典
        user = USERS.get(username)
        if user and user["password"] == sha256(password):
            reset_rate_limit(client_ip)
            session.permanent = True
            session["username"] = username
            safe_user = {k: v for k, v in user.items() if k != "password"}
            return render_template("index.html", user=safe_user)

        # 再检查 SQLite 数据库
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if row:
            db_password = row["password"]
            if db_password == password:
                reset_rate_limit(client_ip)
                session.permanent = True
                session["username"] = row["username"]
                return render_template("index.html", user={
                    "username": row["username"],
                    "email": row["email"],
                    "phone": row["phone"]
                })

        record_failed_attempt(client_ip)
        return render_template("login.html", error="用户名或密码错误")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """注册页面"""
    if request.method == "POST":
        validate_csrf()
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        email = request.form.get("email", "")
        phone = request.form.get("phone", "")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)",
                       (username, password, email, phone))
        conn.commit()
        conn.close()
        return render_template("login.html", message="注册成功，请登录")

    return render_template("register.html")


@app.route("/search")
def search():
    """搜索用户：通过 keyword 参数模糊查询"""
    keyword = request.args.get("keyword", "")
    if not keyword:
        return redirect("/")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username LIKE ? OR email LIKE ?",
                   (f"%{keyword}%", f"%{keyword}%"))
    rows = cursor.fetchall()
    conn.close()

    # 将结果存入 session 以便在首页展示
    results = [{"id": r["id"], "username": r["username"], "email": r["email"], "phone": r["phone"]} for r in rows]
    session["search_results"] = results
    session["search_keyword"] = keyword
    return redirect("/")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """头像上传页面"""
    if not session.get("username"):
        return redirect("/login")

    if request.method == "POST":
        validate_csrf()
        file = request.files.get("file")
        if not file or file.filename == "":
            return render_template("upload.html", error="请选择要上传的文件")

        # 修复1：过滤路径穿越，只保留文件名
        filename = os.path.basename(file.filename)
        if not filename:
            return render_template("upload.html", error="无效的文件名")

        # 修复2：限制仅允许图片类型（修复双扩展名绕过）
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            return render_template("upload.html", error=f"不支持的文件类型（{ext}），仅允许图片文件")
        # 检查文件名中是否包含非图片扩展名（双扩展名绕过）
        name_lower = filename.lower()
        for bad_ext in [".php", ".html", ".htm", ".js", ".py", ".asp", ".aspx", ".jsp", ".cgi", ".pl", ".sh"]:
            if bad_ext in name_lower.replace(ext, ""):
                return render_template("upload.html", error="文件名不合法")

        upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
        save_path = os.path.normpath(os.path.join(upload_dir, filename))
        # 修复1续：确保文件仍在 uploads 目录内
        if not save_path.startswith(os.path.normpath(upload_dir)):
            return render_template("upload.html", error="非法的文件路径")

        file.save(save_path)
        file_url = f"/static/uploads/{filename}"
        return render_template("upload.html", success=True, file_url=file_url, filename=filename)

    return render_template("upload.html")


@app.route("/profile")
def profile():
    """个人中心页面：需登录且只能查看自己的资料"""
    if not session.get("username"):
        return redirect("/login")

    login_username = session["username"]
    user_id = request.args.get("user_id", "")

    # 只允许查看自己的资料
    if user_id != login_username:
        return render_template("profile.html", error="无权查看其他用户的资料")

    # 先在内存字典中查找
    for u in USERS.values():
        if u["username"] == user_id or u.get("id") == user_id:
            return render_template("profile.html", user={
                "id": user_id,
                "username": u["username"],
                "email": u["email"],
                "phone": u["phone"],
                "balance": u["balance"]
            })

    # 再查 SQLite
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ? OR username = ?", (user_id, user_id))
    row = cursor.fetchone()
    conn.close()

    if row:
        return render_template("profile.html", user={
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "phone": row["phone"],
            "balance": row["balance"] or 0
        })

    return render_template("profile.html", error="用户不存在")


@app.route("/recharge", methods=["POST"])
def recharge():
    """充值接口：需登录且只能给自己充值"""
    if not session.get("username"):
        return redirect("/login")

    validate_csrf()
    login_username = session["username"]
    user_id = request.form.get("user_id", "")
    amount = request.form.get("amount", "0")

    # 只允许给自己充值
    if user_id != login_username:
        return redirect("/profile?user_id=" + login_username)

    try:
        amount = float(amount)
    except ValueError:
        amount = 0

    # 修复：不允许负金额和零金额
    if amount <= 0:
        return redirect("/profile?user_id=" + login_username)

    # 修复：设置单次充值上限
    if amount > 1000000:
        return redirect("/profile?user_id=" + login_username)

    # 先检查内存字典
    for u in USERS.values():
        if u["username"] == user_id or u.get("id") == user_id:
            u["balance"] = u["balance"] + amount
            return redirect(f"/profile?user_id={user_id}")

    # 再更新 SQLite
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE id = ? OR username = ?",
                   (amount, user_id, user_id))
    conn.commit()
    conn.close()

    return redirect(f"/profile?user_id={user_id}")


@app.route("/page")
def page():
    """动态页面加载（已修复路径穿越）"""
    name = request.args.get("name", "")

    pages_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages")
    filepath = os.path.normpath(os.path.join(pages_dir, name))

    # 修复：确保文件在 pages 目录内
    if not filepath.startswith(os.path.normpath(pages_dir)):
        return render_template("index.html", page_content="<p>页面不存在</p>")

    if os.path.isfile(filepath):
        with open(filepath, "r") as f:
            content = f.read()
        return render_template("index.html", page_content=content)

    # 尝试加 .html 后缀
    filepath_html = filepath + ".html"
    if os.path.isfile(filepath_html):
        with open(filepath_html, "r") as f:
            content = f.read()
        return render_template("index.html", page_content=content)

    return render_template("index.html", page_content="<p>页面不存在</p>")


@app.route("/change-password", methods=["POST"])
def change_password():
    """修改密码"""
    if not session.get("username"):
        return redirect("/login")

    validate_csrf()
    username = request.form.get("username", "")
    new_password = request.form.get("new_password", "")

    if not username or not new_password:
        return redirect("/profile?user_id=" + session["username"])

    # 更新内存字典中的密码
    if username in USERS:
        USERS[username]["password"] = sha256(new_password)

    # 更新 SQLite 中的密码
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
    conn.commit()
    conn.close()

    return redirect("/profile?user_id=" + username)


@app.route("/fetch-url", methods=["POST"])
def fetch_url():
    """URL 抓取功能（不限制协议和目标，存在 SSRF 风险）"""
    if not session.get("username"):
        return redirect("/login")

    login_username = session["username"]

    # 获取用户信息
    user = USERS.get(login_username)
    if not user:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (login_username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            user = {
                "username": row["username"],
                "email": row["email"],
                "phone": row["phone"]
            }
    safe_user = {k: v for k, v in user.items() if k != "password"} if user else None

    url = request.form.get("url", "")
    if not url:
        return render_template("index.html", user=safe_user, fetch_result="<p>请输入 URL</p>")

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            content = response.read().decode("utf-8", errors="replace")
            result = f"<p><strong>状态码:</strong> {status}</p><hr><pre>{content[:5000]}</pre>"
    except urllib.error.URLError as e:
        result = f"<p><strong>请求失败:</strong> {e.reason}</p>"
    except Exception as e:
        result = f"<p><strong>错误:</strong> {e}</p>"

    return render_template("index.html", user=safe_user, fetch_result=result)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
