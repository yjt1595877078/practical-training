# 步骤 6 — SQL 注入漏洞修复

> **修复日期:** 2026-07-08  
> **修复方式:** 将 f-string 拼接改为参数化查询

---

## 修复概述

将所有直接拼接用户输入的 SQL 查询改为使用 `?` 占位符的参数化查询，从根源上杜绝 SQL 注入。

---

## 修复详情

### 修复 1：搜索功能

**修复前：**

```python
sql = f"SELECT * FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
cursor.execute(sql)
```

**修复后：**

```python
cursor.execute("SELECT * FROM users WHERE username LIKE ? OR email LIKE ?",
               (f"%{keyword}%", f"%{keyword}%"))
```

用户输入中的特殊字符（`'`、`"`、`--` 等）会被 SQLite 驱动自动转义，仅作为数据传递，不会改变 SQL 语句结构。

---

### 修复 2：注册功能

**修复前：**

```python
sql = f"INSERT INTO users (username, password, email, phone) VALUES ('{username}', '{password}', '{email}', '{phone}')"
cursor.execute(sql)
```

**修复后：**

```python
cursor.execute("INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)",
               (username, password, email, phone))
```

---

### 修复 3：登录功能

**修复前：**

```python
sql = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(sql)
```

**修复后：**

```python
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

---

### 修复 4：首页查询

**修复前：**

```python
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

**修复后：**

```python
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```

---

## 修复验证

| 测试项 | 修复前 | 修复后 |
|--------|--------|--------|
| 正常搜索 `keyword=admin` | ✅ 正常 | ✅ 正常 |
| `' OR '1'='1` 注入 | ❌ 泄露全部用户 | ✅ 仅搜索字面字符串，无结果 |
| `' UNION SELECT 1,2,3,4,5--` 注入 | ❌ 插入虚假数据 | ✅ 仅搜索字面字符串，无结果 |
| 注册时传入 `x'$y` | ❌ 可注入 SQL | ✅ 作为普通用户名存入数据库 |
| `' UNION SELECT id,username,password,email,phone FROM users--` | ❌ 提取全表数据 | ✅ 仅搜索字面字符串，无结果 |

---

## 修复原理

参数化查询将 **SQL 逻辑** 与 **用户数据** 分离：

```python
# 错误：SQL 逻辑和数据混在一起
sql = f"SELECT * FROM users WHERE username = '{user_input}'"

# 正确：SQL 逻辑用 ? 占位，数据单独传入
cursor.execute("SELECT * FROM users WHERE username = ?", (user_input,))
```

数据库驱动（sqlite3）内部对 `?` 对应的值进行转义处理，确保用户输入中的任何字符都不会被解析为 SQL 关键字或运算符。
