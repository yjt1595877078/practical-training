# 步骤 18 — SSRF 漏洞修复

> **修复日期:** 2026-07-14  
> **修复方式:** 协议限制 + 内网 IP 过滤

---

## 修复详情

### 修复 1：协议限制

只允许 `http://` 和 `https://` 协议，禁止 `file://` 等危险协议。

```python
parsed = urllib.parse.urlparse(url)
if parsed.scheme not in ("http", "https"):
    return render_template("index.html", user=safe_user, fetch_result="<p>不支持的协议</p>")
```

### 修复 2：内网 IP 过滤

阻止访问本地回环地址和内网保留地址段。

```python
# 阻止 localhost/127.0.0.1
if hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
    return render_template("index.html", user=safe_user, fetch_result="<p>不允许访问内网地址</p>")

# DNS 解析后检查 IP 段
ip = socket.gethostbyname(hostname)
if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172.16.") ...:
    return render_template("index.html", user=safe_user, fetch_result="<p>不允许访问内网地址</p>")
```

---

## 修复验证

| 攻击向量 | Payload | 修复前 | 修复后 |
|----------|---------|:------:|:------:|
| 本地文件读取 | `file:///etc/passwd` | ❌ | ✅ 拦截 |
| 内网自身服务 | `http://127.0.0.1:5000/` | ❌ | ✅ 拦截 |
| 内网端口探测 | `http://127.0.0.1:22/` | ❌ | ✅ 拦截 |
| localhost 绕过 | `http://localhost:5000/` | ❌ | ✅ 拦截 |
| 内网 192.168.x.x | `http://192.168.10.130:5000/` | ❌ | ✅ 拦截 |
| 内网 10.x.x.x | `http://10.0.0.1/` | ❌ | ✅ 拦截 |
| 外网正常访问 | `http://example.com` | ✅ | ✅ 正常 |
