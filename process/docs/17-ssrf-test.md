# 步骤 17 — URL 抓取功能 + SSRF 漏洞

> **新增功能:** URL 抓取 `/fetch-url`  
> **漏洞类型:** 服务端请求伪造（SSRF）

---

## 一、新增功能

| 路由 | 方法 | 说明 |
|------|:----:|------|
| `/fetch-url` | POST | 抓取用户提交的 URL，不限制协议和目标 |

### 修改的文件

| 文件 | 说明 |
|------|------|
| `app.py` | 新增 `/fetch-url` 路由 + `urllib` 导入 |
| `templates/index.html` | 新增 URL 输入框、抓取按钮、结果展示区 |

---

## 二、SSRF 漏洞详情

### 漏洞代码

```python
url = request.form.get("url", "")
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as response:
    ...
```

用户输入的 URL 直接传给 `urlopen()`，无任何协议限制或目标过滤。

### 漏洞利用

```bash
# 1. 正常抓取外部网站
url=http://example.com           → ✅ 状态码 200

# 2. SSRF: 读取本地文件
url=file:///etc/passwd           → ✅ 读取系统文件

# 3. SSRF: 访问内网服务
url=http://127.0.0.1:5000/       → ✅ 访问自身 Web 服务

# 4. SSRF: 探测内网
url=http://10.0.0.1/
url=http://192.168.1.1/
```

### 测试结果

| 测试 | Payload | 结果 |
|------|---------|:----:|
| 外部网站 | `http://example.com` | ✅ 正常抓取 |
| file 协议 | `file:///etc/passwd` | ✅ 读取本地文件 |
| 内网访问 | `http://127.0.0.1:5000/` | ✅ 可访问自身服务 |
| 未登录保护 | — | ✅ 跳转登录页 |
