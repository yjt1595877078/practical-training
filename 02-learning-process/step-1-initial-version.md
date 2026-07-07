# 步骤 1 — 初始版本（带漏洞）

## 项目结构

```
01-flask-login/
├── app.py               # Flask 主应用
├── templates/
│   ├── base.html        # 基础模板
│   ├── index.html       # 首页
│   └── login.html       # 登录页
└── static/
    └── css/
        └── style.css    # 样式文件
```

## 用户数据库

两个预置用户，密码以**明文**存储在 `USERS` 字典中：

| 用户名 | 密码 | 角色 | 邮箱 | 手机 | 余额 |
|--------|------|------|------|------|------|
| admin | admin123 | admin | admin@example.com | 13800138000 | 99999 |
| alice | alice2025 | user | alice@example.com | 13900139001 | 100 |

## 路由设计

- `GET /` — 首页，根据 session 显示用户信息或未登录提示
- `GET/POST /login` — 登录页，POST 时明文比对密码
- `GET /logout` — 登出，清除 session

## 安全缺陷（已知）

- ✅ 密码明文存储在代码中
- ✅ 登录页 HTML 注释泄露默认账号密码
- ✅ 登录后首页展示密码字段
- ✅ 后端将完整 user 字典（含密码）传递给模板

---

*完整代码见 [01-flask-login](./) 目录*
