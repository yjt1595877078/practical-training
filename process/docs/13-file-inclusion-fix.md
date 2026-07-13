# 步骤 13 — 文件包含漏洞修复

> **修复日期:** 2026-07-09  
> **修复方式:** 路径规范化 `normpath` + 前缀比对

---

## 修复详情

### 修复代码

```python
filepath = os.path.normpath(os.path.join(pages_dir, name))

# 确保文件在 pages 目录内
if not filepath.startswith(os.path.normpath(pages_dir)):
    return render_template("index.html", page_content="<p>页面不存在</p>")
```

`os.path.normpath` 会将 `../` 解析为真实的目录层级，例如：

```python
os.path.normpath("/pages/../app.py")  → "/app.py"
os.path.normpath("/pages/help.html")   → "/pages/help.html"
```

然后通过 `startswith` 判断文件是否在 `pages_dir` 范围内。

---

## 修复验证

| 测试 | Payload | 修复前 | 修复后 |
|------|---------|:------:|:------:|
| 读取源码 | `?name=../app.py` | ❌ 读取成功 | ✅ 拦截 |
| 下载数据库 | `?name=../data/users.db` | ❌ 读取成功 | ✅ 拦截 |
| 系统文件 | `?name=../../../../etc/passwd` | ❌ 读取成功 | ✅ 拦截 |
| 模板文件 | `?name=../templates/base.html` | ❌ 读取成功 | ✅ 拦截 |
| 正常访问 | `?name=help` | ✅ 正常 | ✅ 正常 |
| 带后缀 | `?name=help.html` | ✅ 正常 | ✅ 正常 |
