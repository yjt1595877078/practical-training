# 步骤 10 — 业务逻辑及越权漏洞修复

> **修复日期:** 2026-07-09  
> **修复方式:** 登录校验 + 身份验证 + 金额校验 + 双扩展名过滤

---

## 修复清单

| # | 漏洞 | 修复方式 |
|---|------|----------|
| 1 | 无需登录访问个人中心 | `/profile` 增加 session 登录校验 |
| 2 | 水平越权查看他人资料 | 比对 `user_id` 与当前登录用户 |
| 3 | 水平越权给他人充值 | 比对 `user_id` 与当前登录用户 |
| 4 | 垂直越权普通用户看管理员 | 身份校验统一处理，拒绝跨用户访问 |
| 5 | 负金额充值套现 | 增加 `amount > 0` 校验 |
| 6 | 余额无下限 | 通过禁止负金额充值天然防护 |
| 7 | 充值无上限 | 增加单次上限 1,000,000 |
| 8 | 用户 ID 可枚举 | 未登录直接跳转，不暴露用户是否存在 |
| 9 | 双扩展名绕过 `test.php.png` | 检查文件名中是否包含非图片扩展名 |

---

## 修复详情

### 修复 1-4：登录校验 + 身份验证

```python
@app.route("/profile")
def profile():
    if not session.get("username"):
        return redirect("/login")

    login_username = session["username"]
    user_id = request.args.get("user_id", "")

    if user_id != login_username:
        return render_template("profile.html", error="无权查看其他用户的资料")
```

### 修复 5-7：充值校验

```python
@app.route("/recharge", methods=["POST"])
def recharge():
    if not session.get("username"):
        return redirect("/login")

    if user_id != login_username:
        return redirect("/profile?user_id=" + login_username)

    if amount <= 0:
        return redirect("/profile?user_id=" + login_username)

    if amount > 1000000:
        return redirect("/profile?user_id=" + login_username)
```

### 修复 9：双扩展名过滤

```python
name_lower = filename.lower()
for bad_ext in [".php", ".html", ".htm", ".js", ".py", ".asp", ".aspx", ".jsp"]:
    if bad_ext in name_lower.replace(ext, ""):
        return render_template("upload.html", error="文件名不合法")
```

---

## 修复验证

| 测试项 | 修复前 | 修复后 |
|--------|:------:|:------:|
| 未登录访问 `/profile` | ❌ 可查看 | ✅ 跳转登录页 |
| admin 查看 alice 资料 | ❌ 越权成功 | ✅ 提示无权查看 |
| 普通用户查看 admin 资料 | ❌ 越权成功 | ✅ 提示无权查看 |
| 负金额充值 `amount=-100` | ❌ 余额被扣 | ✅ 拒绝充值 |
| 给他人充值 | ❌ 越权成功 | ✅ 拒绝充值 |
| 超大金额充值 | ❌ 成功 | ✅ 拒绝超限充值 |
| 双扩展名 `test.php.png` | ❌ 可上传 | ✅ 已拦截 |
| 自己正常充值 | ✅ 正常 | ✅ 正常 |
