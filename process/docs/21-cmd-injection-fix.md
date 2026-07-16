# 步骤 21 — 命令注入漏洞修复

> **修复日期:** 2026-07-14  
> **修复方式:** 输入校验 + 禁用 shell=True

---

## 修复详情

### 修复 1：输入字符校验

只允许字母、数字、点号和短横线，过滤所有特殊字符。

```python
import re
if not re.match(r'^[a-zA-Z0-9\.\-]+$', ip):
    return render_template("ping.html", output="输入包含非法字符")
```

### 修复 2：禁用 shell=True

改用列表传参方式执行 ping 命令，避免 shell 解释器介入。

```python
# 修复前（存在注入）
cmd = f"ping -c 3 {ip}"
output = subprocess.check_output(cmd, shell=True, ...)

# 修复后（安全）
output = subprocess.check_output(["ping", "-c", "3", ip], ...)
```

---

## 修复验证

| 注入手法 | Payload | 修复前 | 修复后 |
|----------|---------|:------:|:------:|
| 分号注入 | `8.8.8.8;id` | ❌ | ✅ 拦截 |
| 管道注入 | `127.0.0.1\|ls` | ❌ | ✅ 拦截 |
| 逻辑与注入 | `127.0.0.1&&id` | ❌ | ✅ 拦截 |
| 反引号注入 | `` 127.0.0.1\`whoami\` `` | ❌ | ✅ 拦截 |
| 文件读取 | `127.0.0.1;cat /etc/passwd` | ❌ | ✅ 拦截 |
| 子命令注入 | `127.0.0.1$(id)` | ❌ | ✅ 拦截 |
| 正常 Ping IP | `8.8.8.8` | ✅ | ✅ 正常 |
| 正常 Ping 域名 | `example.com` | ✅ | ✅ 正常 |
