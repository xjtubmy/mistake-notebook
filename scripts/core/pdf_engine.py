"""
PDF 生成引擎 - 将 Markdown 转换为可打印的 PDF 文档。

提供 PDFEngine 类，封装 Markdown 转 HTML、HTML 转 PDF 的核心功能，
供 export-printable、generate-practice 等 CLI 命令复用。
"""

from __future__ import annotations

import markdown2
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright


class PDFEngine:
    """
    PDF 生成引擎。

    将 Markdown 内容转换为可打印的 PDF 文档，支持 A4 纸张格式、
    中文字体渲染和自定义边距。

    Attributes:
        output_dir: 默认输出目录，用于存储生成的 PDF 文件。
    """

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """
        初始化 PDF 引擎。

        Args:
            output_dir: 默认输出目录。如果为 None，则使用当前工作目录。
        """
        self.output_dir = output_dir or Path.cwd()

    def printable_html_from_markdown(self, markdown: str) -> str:
        """
        将 Markdown 内容转换为可打印的 HTML。

        使用 markdown2 库解析 Markdown，并添加适合打印的 CSS 样式，
        包括中文字体、A4 页面设置和表格/代码块样式。

        Args:
            markdown: Markdown 格式的文本内容。

        Returns:
            完整的 HTML 文档字符串，包含内联 CSS 样式。
        """
        html_body = markdown2.markdown(
            markdown,
            extras=["tables", "fenced-code-blocks", "emoji", "markdown-in-html"],
        )
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: A4; margin: 2cm; }}
        body {{ font-family: "SimSun", "Songti SC", serif; line-height: 1.8; font-size: 12pt; }}
        h1 {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; font-size: 18pt; }}
        h2 {{ color: #333; border-left: 4px solid #4CAF50; padding-left: 10px; font-size: 14pt; page-break-after: avoid; }}
        h3 {{ color: #555; font-size: 12pt; }}
        img {{ max-width: 100%; height: auto; display: block; margin: 10px auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        pre {{ background: #f5f5f5; padding: 10px; border-radius: 4px; font-size: 10pt; }}
        blockquote {{ border-left: 4px solid #4CAF50; padding-left: 15px; margin: 10px 0; color: #555; }}
        details {{ margin: 0.8em 0; padding: 0.5em 1em; border: 1px solid #ddd; border-radius: 4px; }}
        summary {{ cursor: pointer; font-weight: bold; }}
    </style>
</head>
<body>
{html_body}
</body>
</html>
"""

    def markdown_to_pdf(
        self, markdown_content: str, output_path: Path, title: str = ""
    ) -> Path:
        """
        将 Markdown 内容直接转换为 PDF 文件。

        先将 Markdown 转换为 HTML，然后使用 Playwright 渲染并导出 PDF。

        Args:
            markdown_content: Markdown 格式的文本内容。
            output_path: PDF 输出文件路径。
            title: 文档标题（可选），用于日志输出。

        Returns:
            生成的 PDF 文件的绝对路径。
        """
        html_content = self.printable_html_from_markdown(markdown_content)
        self.html_to_pdf(html_content, output_path)
        return output_path.resolve()

    def html_to_pdf(self, html: str, output_path: Path) -> None:
        """
        将 HTML 内容转换为 PDF 文件。

        使用 Playwright 的 Chromium 浏览器渲染 HTML，并导出为 A4 格式的 PDF。

        Args:
            html: HTML 文档字符串。
            output_path: PDF 输出文件路径。
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "2cm", "bottom": "2cm", "left": "2cm", "right": "2cm"},
            )
            browser.close()

        resolved = str(output_path.resolve())
        print(f"✅ 已导出 PDF: {resolved}")
        print(f"OUTPUT_PATH={resolved}")
