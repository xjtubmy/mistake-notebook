"""
PDF 模板定义 - 包含 CSS 样式和 HTML 模板结构。

提供增强的 CSS 模板，支持：
- 中文字体（Noto Sans SC 优先，降级到系统字体）
- 专业配色方案
- 表格样式（边框、斑马纹）
- 页眉页脚（页码、标题）
"""

from __future__ import annotations

# 专业配色方案
COLORS = {
    "primary": "#2c5282",      # 深蓝 - 主色调
    "secondary": "#38a169",    # 绿色 - 强调色
    "accent": "#dd6b20",       # 橙色 - 点缀色
    "text_primary": "#1a202c", # 深灰 - 主要文字
    "text_secondary": "#4a5568",  # 中灰 - 次要文字
    "border": "#e2e8f0",       # 浅灰 - 边框
    "bg_light": "#f7fafc",     # 极浅灰 - 背景
    "bg_header": "#edf2f7",    # 浅灰 - 表头
    "bg_zebra": "#ffffff",     # 白色 - 斑马纹
    "bg_zebra_alt": "#f8fafc", # 极浅蓝 - 斑马纹交替
}

# 中文字体栈 - 优先使用 Noto Sans SC，降级到系统字体
FONT_STACK = """
    "Noto Sans SC", 
    "Source Han Sans SC", 
    "PingFang SC", 
    "Microsoft YaHei", 
    "Hiragino Sans GB", 
    "WenQuanYi Micro Hei", 
    sans-serif
"""

# 衬线字体栈（用于标题）
SERIF_FONT_STACK = """
    "Noto Serif SC", 
    "Source Han Serif SC", 
    "Songti SC", 
    "SimSun", 
    "STSong", 
    serif
"""


def get_enhanced_css() -> str:
    """
    获取增强的 CSS 样式模板。

    包含：
    - 中文字体支持（Noto Sans SC 优先）
    - 专业配色方案
    - 表格样式（边框、斑马纹、悬停效果）
    - 页眉页脚样式
    - 代码块、引用、细节框样式
    - 打印优化

    Returns:
        完整的 CSS 样式字符串。
    """
    return f"""
/* ========== 页面设置 ========== */
@page {{
    size: A4;
    margin: 2cm 2.5cm 2.5cm 2.5cm;  /* 上、右、下、左 */
    
    @top-center {{
        content: "错题本";
        font-size: 9pt;
        color: {COLORS["text_secondary"]};
    }}
    
    @bottom-center {{
        content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
        font-size: 9pt;
        color: {COLORS["text_secondary"]};
    }}
}}

/* ========== 基础样式 ========== */
* {{
    box-sizing: border-box;
}}

body {{
    font-family: {FONT_STACK};
    line-height: 1.8;
    font-size: 11pt;
    color: {COLORS["text_primary"]};
    background: white;
    margin: 0;
    padding: 0;
}}

/* ========== 标题样式 ========== */
h1 {{
    text-align: center;
    color: {COLORS["primary"]};
    font-size: 20pt;
    font-weight: bold;
    margin: 0 0 1.5em 0;
    padding-bottom: 0.8em;
    border-bottom: 3px solid {COLORS["primary"]};
    page-break-after: avoid;
}}

h2 {{
    color: {COLORS["primary"]};
    font-size: 16pt;
    font-weight: bold;
    margin: 1.5em 0 0.8em 0;
    padding: 0.3em 0 0.3em 0.8em;
    border-left: 5px solid {COLORS["secondary"]};
    background: {COLORS["bg_light"]};
    page-break-after: avoid;
}}

h3 {{
    color: {COLORS["text_primary"]};
    font-size: 13pt;
    font-weight: bold;
    margin: 1.2em 0 0.5em 0;
    page-break-after: avoid;
}}

h4 {{
    color: {COLORS["text_secondary"]};
    font-size: 11pt;
    font-weight: bold;
    margin: 1em 0 0.3em 0;
}}

/* ========== 段落与文本 ========== */
p {{
    margin: 0.6em 0;
    text-align: justify;
}}

strong {{
    font-weight: bold;
    color: {COLORS["primary"]};
}}

em {{
    font-style: italic;
}}

/* ========== 表格样式 ========== */
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    font-size: 10pt;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}}

thead {{
    background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["primary"]}dd 100%);
    color: white;
}}

th {{
    border: 1px solid {COLORS["primary"]};
    padding: 12px 10px;
    text-align: left;
    font-weight: bold;
    font-size: 10pt;
}}

tbody tr {{
    background-color: {COLORS["bg_zebra"]};
    transition: background-color 0.2s;
}}

tbody tr:nth-child(even) {{
    background-color: {COLORS["bg_zebra_alt"]};
}}

tbody tr:hover {{
    background-color: {COLORS["bg_light"]};
}}

td {{
    border: 1px solid {COLORS["border"]};
    padding: 10px;
    vertical-align: top;
    line-height: 1.6;
}}

/* 表格第一列加粗 */
td:first-child {{
    font-weight: bold;
    color: {COLORS["text_primary"]};
}}

/* ========== 图片样式 ========== */
img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}}

/* ========== 代码块样式 ========== */
pre {{
    background: {COLORS["bg_light"]};
    border: 1px solid {COLORS["border"]};
    border-left: 4px solid {COLORS["accent"]};
    padding: 12px 15px;
    border-radius: 4px;
    font-size: 9pt;
    font-family: "Fira Code", "Cascadia Code", "Consolas", monospace;
    overflow-x: auto;
    margin: 1em 0;
    line-height: 1.5;
}}

code {{
    font-family: "Fira Code", "Cascadia Code", "Consolas", monospace;
    font-size: 9pt;
    background: {COLORS["bg_light"]};
    padding: 2px 6px;
    border-radius: 3px;
    color: {COLORS["accent"]};
}}

pre code {{
    background: transparent;
    padding: 0;
    color: inherit;
}}

/* ========== 引用样式 ========== */
blockquote {{
    border-left: 5px solid {COLORS["secondary"]};
    padding: 0.8em 1.2em;
    margin: 1em 0;
    background: {COLORS["bg_light"]};
    color: {COLORS["text_secondary"]};
    font-style: italic;
    border-radius: 0 4px 4px 0;
}}

/* ========== 细节框（可折叠） ========== */
details {{
    margin: 0.8em 0;
    padding: 0.6em 1em;
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    background: white;
}}

summary {{
    cursor: pointer;
    font-weight: bold;
    color: {COLORS["primary"]};
    padding: 0.3em 0;
    outline: none;
}}

summary:hover {{
    color: {COLORS["secondary"]};
}}

details[open] {{
    border-color: {COLORS["secondary"]};
    background: {COLORS["bg_light"]};
}}

/* ========== 列表样式 ========== */
ul, ol {{
    margin: 0.8em 0;
    padding-left: 2em;
}}

li {{
    margin: 0.4em 0;
    line-height: 1.7;
}}

ul li {{
    list-style-type: disc;
}}

ol li {{
    list-style-type: decimal;
}}

/* ========== 链接样式 ========== */
a {{
    color: {COLORS["primary"]};
    text-decoration: none;
    border-bottom: 1px dotted {COLORS["primary"]};
}}

a:hover {{
    color: {COLORS["secondary"]};
    border-bottom-color: {COLORS["secondary"]};
}}

/* ========== 打印优化 ========== */
@media print {{
    body {{
        font-size: 10pt;
    }}
    
    h1 {{ font-size: 18pt; }}
    h2 {{ font-size: 14pt; }}
    h3 {{ font-size: 12pt; }}
    
    /* 避免在元素内部断页 */
    h1, h2, h3, h4, h5, h6 {{
        page-break-after: avoid;
    }}
    
    table, img, pre, blockquote {{
        page-break-inside: avoid;
    }}
    
    /* 移除悬停效果 */
    tbody tr:hover {{
        background-color: inherit;
    }}
}}

/* ========== 辅助类 ========== */
.text-center {{ text-align: center; }}
.text-right {{ text-align: right; }}
.text-muted {{ color: {COLORS["text_secondary"]}; }}
.mt-1 {{ margin-top: 0.5em; }}
.mt-2 {{ margin-top: 1em; }}
.mb-1 {{ margin-bottom: 0.5em; }}
.mb-2 {{ margin-bottom: 1em; }}
"""


def get_html_template(title: str = "", content: str = "") -> str:
    """
    获取完整的 HTML 文档模板。

    Args:
        title: 文档标题。
        content: HTML 正文内容。

    Returns:
        完整的 HTML 文档字符串。
    """
    css = get_enhanced_css()
    
    page_title = title if title else "错题本"
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <style>
        {css}
    </style>
</head>
<body>
    {content}
</body>
</html>
"""
