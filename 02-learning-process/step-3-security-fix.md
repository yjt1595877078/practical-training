# 步骤 3 — 安全修复

## 修复清单

### 修复 1：删除 HTML 泄露注释

**文件:** `templates/login.html`

```diff
- <!-- 调试信息 - 默认管理员账号 用户名: admin 密码: admin123 -->
{% extends "base.html" %}
```

同时 `templates/index.html` 中的相同注释也一并删除。

### 修复 2：首页不再显示密码

**文件:** `templates/index.html`

```diff
<ul class="info-list">
    <li class="info-item">
        <span class="info-label">用户名</span>
        <span class="info-value">{{ user['username'] }}</span>
    </li>
-   <li class="info-item">
-       <span class="info-label">密码</span>
-       <span class="info-value">{{ user['password'] }}</span>
-   </li>
    ...
</ul>
```

### 修复 3：后端过滤密码字段

**文件:** `app.py`

```python
# 首页路由
safe_user = {k: v for k, v in user.items() if k != "password"} if user else None
return render_template("index.html", user=safe_user)

# 登录路由
session["username"] = username
safe_user = {k: v for k, v in user.items() if k != "password"}
return render_template("index.html", user=safe_user)
```

## 验证结果

修复后通过以下方式验证：
1. 查看登录页 HTML 源代码 — ✅ 无账号密码泄露
2. 登录后查看首页 — ✅ 密码不再显示
3. 查看后端传给模板的数据 — ✅ 不包含 password 字段
