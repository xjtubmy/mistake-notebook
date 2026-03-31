# mistake-notebook 依赖说明

## 📦 依赖列表

### 核心依赖（必需）

| 依赖 | 版本 | 用途 | 是否必需 |
|------|------|------|---------|
| `playwright` | ≥1.50 | 长图生成 + PDF 导出 | ✅ 必需 |
| `markdown2` | ≥2.0 | Markdown 渲染 | ✅ 必需 |

### 浏览器（Playwright 自动安装）

| 浏览器 | 用途 | 安装命令 |
|--------|------|---------|
| **Chromium** | 长图生成 + PDF 导出 | `playwright install chromium` |

### 系统依赖

**无需任何系统依赖！** 🎉

Playwright 会自动下载浏览器，无需手动安装 wkhtmltopdf 或其他工具。

---

## 🚀 快速安装

### 一键安装（推荐）

```bash
# 安装 Python 依赖
pip install playwright markdown2 --break-system-packages

# 安装浏览器
playwright install chromium
```

### 验证安装

```bash
# 运行依赖检查
python3 skills/mistake-notebook/scripts/check-deps.py
```

输出示例：
```
============================================================
🔍 mistake-notebook 依赖检查
============================================================

📦 Python 依赖:
----------------------------------------
✅ playwright: 已安装
✅ markdown2: 已安装

🌐 浏览器:
----------------------------------------
✅ chromium: 已安装

============================================================
📊 检查结果总结
============================================================

✅ 所有功能可用：
   • 录入错题
   • 自动分类
   • 分析报告
   • 复习提醒
   • 错题检索
   • 长图分享
   • PDF 打印

✅ 所有依赖已安装，可以开始使用！

============================================================
```

---

## 📊 功能依赖对照表

| 功能 | 需要的依赖 |
|------|-----------|
| 录入错题 | 无 |
| 自动分类 | 无 |
| 分析报告 | 无 |
| 复习提醒 | 无 |
| 错题检索 | 无 |
| 导出 Markdown | `markdown2` |
| 导出 PDF | `playwright` + `chromium` |
| 生成长图 | `playwright` + `chromium` |
| 分享（长图/PDF） | `playwright` + `chromium` |

---

## ⚠️ 常见问题

### Q1: `pip install` 提示权限错误

**解决**：
```bash
# 使用 --break-system-packages 参数
pip install playwright markdown2 --break-system-packages

# 或使用虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install playwright markdown2
playwright install chromium
```

### Q2: `playwright install` 下载失败

**解决**：
```bash
# 使用国内镜像
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium
```

### Q3: 长图/PDF 生成空白

**解决**：
```bash
# 重新安装浏览器
playwright install chromium --force

# 检查依赖
python3 -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### Q4: 之前安装了 pdfkit/wkhtmltopdf，需要卸载吗？

**回答**：不需要！
- 已安装的可以保留，不影响使用
- mistake-notebook 已改用 Playwright，不再依赖 pdfkit/wkhtmltopdf
- 如占用空间，可手动卸载：
  ```bash
  pip uninstall pdfkit
  sudo apt-get remove wkhtmltopdf  # 可选
  ```

---

## 🔗 相关链接

- [Playwright 官方文档](https://playwright.dev/python/)
- [markdown2 GitHub](https://github.com/trentm/python-markdown2)

---

**最后更新**：2026-03-31
