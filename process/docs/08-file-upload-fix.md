# 步骤 8 — 文件上传漏洞修复

> **修复日期:** 2026-07-09  
> **修复方式:** 文件名过滤 + 类型白名单 + 路径安全检查

---

## 修复概述

针对文件上传功能的三个高危漏洞进行修复，限制仅允许图片类型上传，杜绝路径穿越和恶意文件上传。

---

## 修复详情

### 修复 1：路径穿越

**问题：** 上传 `../../../evil.txt` 可逃逸到 `uploads/` 目录之外

**修复：** 使用 `os.path.basename()` 只取文件名，丢弃路径部分；再用 `os.path.normpath()` + 前缀比对确保文件在 uploads 目录内。

```python
# 修复前
file.save(os.path.join(upload_dir, filename))

# 修复后
filename = os.path.basename(file.filename)
save_path = os.path.normpath(os.path.join(upload_dir, filename))
if not save_path.startswith(os.path.normpath(upload_dir)):
    return render_template("upload.html", error="非法的文件路径")
file.save(save_path)
```

---

### 修复 2：任意文件上传（类型限制）

**问题：** `.html`、`.php`、`.py`、`.js` 等任意文件均可上传

**修复：** 建立图片扩展名白名单，仅允许图片文件上传。

```python
allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
ext = os.path.splitext(filename)[1].lower()
if ext not in allowed_extensions:
    return render_template("upload.html", error=f"不支持的文件类型（{ext}），仅允许图片文件")
```

---

### 修复 3：持久化 XSS

**问题：** 上传含 `<script>` 的 HTML 文件后可直接访问执行

**修复：** 通过限制仅允许图片类型上传，从源头阻断 HTML/JS 文件的上传。

---

## 修复验证

| 测试项 | 修复前 | 修复后 |
|--------|:------:|:------:|
| `../../../evil.txt` 路径穿越 | ❌ 逃逸到上级目录 | ✅ 截断路径，仅保留文件名 |
| `.html` 文件上传 | ❌ 上传成功 | ✅ 被拒绝 |
| `.php` 文件上传 | ❌ 上传成功 | ✅ 被拒绝 |
| `.py` 文件上传 | ❌ 上传成功 | ✅ 被拒绝 |
| `.js` 文件上传 | ❌ 上传成功 | ✅ 被拒绝 |
| `.png` 正常图片上传 | ✅ 正常 | ✅ 正常 |

---

## 修复代码汇总

```python
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if not session.get("username"):
        return redirect("/login")

    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            return render_template("upload.html", error="请选择要上传的文件")

        # 修复1：过滤路径穿越
        filename = os.path.basename(file.filename)
        if not filename:
            return render_template("upload.html", error="无效的文件名")

        # 修复2：限制仅允许图片类型
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            return render_template("upload.html", error=f"不支持的文件类型")

        upload_dir = os.path.join(..., "static", "uploads")
        save_path = os.path.normpath(os.path.join(upload_dir, filename))
        if not save_path.startswith(os.path.normpath(upload_dir)):
            return render_template("upload.html", error="非法的文件路径")

        file.save(save_path)
        return render_template("upload.html", success=True, ...)
```
