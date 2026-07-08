# 步骤 3 — 安全修复

## 修复列表

| # | 漏洞 | 修复方式 | 层面 |
|---|------|----------|------|
| 1 | HTML 注释泄露账号密码 | 删除注释 | 前端 |
| 2 | 首页展示密码字段 | 移除密码行 | 前端 |
| 3 | 后端密码明文传到模板 | 过滤 password 字段 | 后端 |
| 4 | 数据库明文存储密码 | 改用 SHA256 哈希 | 后端 |
| 5 | 无登录频率限制 | 5 次失败锁定 60 秒 | 后端 |
| 6 | Session 永不过期 | 设置 30 分钟超时 | 后端 |

---

## 修复 1：删除 HTML 泄露注释

**文件:** `templates/login.html`、`templates/index.html`

```diff
- <!-- 调试信息 - 默认管理员账号 用户名: admin 密码: admin123 -->
{% extends "base.html" %}
```

## 修复 2：首页不再显示密码

**文件:** `templates/index.html`

```diff
<ul class="info-list">
    ...
-   <li class="info-item">
-       <span class="info-label">密码</span>
-       <span class="info-value">{{ user['password'] }}</span>
-   </li>
    ...
</ul>
```

## 修复 3：后端过滤密码字段

**文件:** `app.py`

```python
# 传递到模板前过滤掉 password 字段
safe_user = {k: v for k, v in user.items() if k != "password"} if user else None
return render_template("index.html", user=safe_user)
```

## 修复 4：密码加密存储

**问题:** 数据库中密码以明文存储，源码泄露即全部暴露。

**修复:** 在 `app.py` 顶部定义哈希函数：

```python
import hashlib

def sha256(password):
    return hashlib.sha256(password.encode()).hexdigest()
```

将 `USERS` 字典中的密码替换为哈希值：

```python
USERS = {
    "admin": {
        "password": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
        # ...
    },
    "alice": {
        "password": "f9353d7664a88f84150c0289351539ee2f5b86c897110f482e4cd5afec3b277a",
        # ...
    }
}
```

登录比对改用哈希：

```python
if user["password"] != sha256(password):
    return render_template("login.html", error="密码错误")
```

## 修复 5：登录频率限制

**问题:** 攻击者可无限次暴力破解密码。

**修复:** 在 `app.py` 中添加限频逻辑：

```python
from datetime import timedelta
import time

LOGIN_ATTEMPTS = {}  # key: IP, value: {"count": int, "lockout_until": float}
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
```

在登录路由中使用：

```python
client_ip = request.remote_addr or "unknown"
ok, msg = check_rate_limit(client_ip)
if not ok:
    return render_template("login.html", error=msg)

# 验证失败后记录
record_failed_attempt(client_ip)

# 验证成功后清除
reset_rate_limit(client_ip)
```

## 修复 6：Session 超时

**问题:** 用户登录后 session 永不过期，存在会话劫持风险。

**修复:**

```python
from datetime import timedelta

app.permanent_session_lifetime = timedelta(minutes=30)
```

登录时启用永久 session：

```python
session.permanent = True
session["username"] = username
```

---

## 验证结果

| 验证项 | 结果 |
|--------|------|
| 查看登录页 HTML 源码 → 无账号密码泄露 | ✅ |
| 登录后查看首页 → 密码不再显示 | ✅ |
| 查看 `app.py` → 密码已哈希，无法逆向 | ✅ |
| 连续输错 5 次密码 → 锁定 60 秒 | ✅ |
| 30 分钟后 session → 自动过期需重新登录 | ✅ |
