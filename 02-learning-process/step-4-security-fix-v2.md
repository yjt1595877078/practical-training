# 步骤 4 — 安全修复（二）：密码加密 + 登录限频 + Session 超时

## 修复 #1：密码加密存储

**问题:** `USERS` 字典中密码以明文存储，任何人看到源码即可获取用户凭据。

**修复:** 使用 `hashlib.sha256` 对密码进行哈希处理后存储。

```python
def sha256(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

登录时不再用 `==` 比较明文，而是比较哈希值：

```python
if user["password"] != sha256(password):
    return render_template("login.html", error="密码错误")
```

## 修复 #3：登录频率限制

**问题:** 无登录频率限制，攻击者可无限次暴力破解密码。

**修复:** 按 IP 地址记录失败次数，5 次失败后锁定 60 秒。

```python
LOGIN_ATTEMPTS = {}  # key: IP, value: {"count": int, "lockout_until": float}
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60
```

登录时先检查频率限制：

```python
ok, msg = check_rate_limit(client_ip)
if not ok:
    return render_template("login.html", error=msg)
```

## 修复 #5：Session 超时

**问题:** 登录后 session 永不过期，离开电脑后他人可继续使用。

**修复:** 设置 session 有效期 30 分钟。

```python
from datetime import timedelta

app.permanent_session_lifetime = timedelta(minutes=30)
```

登录时启用永久 session：

```python
session.permanent = True
session["username"] = username
```

## 验证

1. ✅ 查看 `app.py` 源码 — 密码已变成哈希值，无法逆向获取明文
2. ✅ 连续输错 5 次密码 — 提示等待，锁定期间无法继续尝试
3. ✅ 登录 30 分钟后 session 自动过期 — 需重新登录
