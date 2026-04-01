# Requirements

## Python Dependencies

| Dependency | Purpose | Required |
|------------|---------|----------|
| `playwright` | PDF 导出与浏览器渲染 | Yes |
| `markdown2` | Markdown 渲染 | Yes |

## Browser Dependency

当前默认使用 Chromium：

```bash
playwright install chromium
```

## Install

```bash
pip install playwright markdown2 --break-system-packages
playwright install chromium
```

## Verify

```bash
python3 skills/mistake-notebook/scripts/check-deps.py
```

## Feature Mapping

| 功能 | 依赖 |
|------|------|
| 导出 Markdown | `markdown2` |
| 导出 PDF | `playwright` + `chromium` |
| 浏览器渲染相关功能 | `playwright` + `chromium` |

## Common Issues

### `pip install` 权限错误

```bash
pip install playwright markdown2 --break-system-packages
```

或使用虚拟环境：

```bash
python3 -m venv venv
source venv/bin/activate
pip install playwright markdown2
playwright install chromium
```

### `playwright install` 下载失败

```bash
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
playwright install chromium
```

### PDF 生成空白

```bash
playwright install chromium --force
python3 -c "from playwright.sync_api import sync_playwright; print('OK')"
```

## Notes

- 当前默认导出格式是 PDF
- 长图相关脚本仍可保留，但不是默认工作流
- 不再依赖 `wkhtmltopdf`
