# 步骤 16 — CSRF 漏洞修复

> **修复日期:** 2026-07-14  
> **修复方式:** 添加 CSRF Token 生成与验证机制

---

## 一、修复内容

### 后端：CSRF Token 生成与验证

在 `app.py` 中新增：

```python
import secrets

def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]

def validate_csrf():
    token = request.form.get("_csrf_token", "")
    stored = session.get("_csrf_token", "")
    if not token or not stored or token != stored:
        abort(403, "CSRF Token 无效")
```

所有 POST 路由均添加 `validate_csrf()` 调用，确保表单提交必须携带有效 Token。

### 前端：所有表单添加隐藏字段

```html
<input type="hidden" name="_csrf_token" value="{{ csrf_token() }}">
```

| 模板 | 表单 |
|------|------|
| `login.html` | 登录表单 |
| `register.html` | 注册表单 |
| `upload.html` | 上传表单 |
| `profile.html` | 充值表单 + 修改密码表单 |

---

## 二、修复验证

| 测试项 | 结果 |
|--------|:----:|
| 带 CSRF Token 登录 | ✅ 成功 |
| 带 CSRF Token 修改密码 | ✅ 成功 |
| 不带 CSRF Token 提交 | ✅ 返回 403 拦截 |
| 登录页面含 CSRF Token | ✅ 页面已包含 |
| 个人中心表单含 CSRF Token | ✅ 页面已包含 |

---

## 三、影响范围

受影响的 5 个 POST 接口全部完成修复：

| 路由 | 方法 | CSRF 状态 |
|------|:----:|:--------:|
| `/login` | POST | ✅ 已修复 |
| `/register` | POST | ✅ 已修复 |
| `/upload` | POST | ✅ 已修复 |
| `/recharge` | POST | ✅ 已修复 |
| `/change-password` | POST | ✅ 已修复 |
