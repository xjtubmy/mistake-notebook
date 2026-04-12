"""
PDF 生成引擎 - 将 Markdown 转换为可打印的 PDF 文档。

提供 PDFEngine 类，封装 Markdown 转 HTML、HTML 转 PDF 的核心功能，
供 export-printable、generate-practice 等 CLI 命令复用。
"""

from __future__ import annotations

import markdown2
from pathlib import Path
from typing import Optional, cast

from playwright.sync_api import sync_playwright

from .pdf_templates import get_enhanced_css, get_html_template


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

    def printable_html_from_markdown(
        self, markdown: str, title: str = "", base_dir: Optional[Path] = None
    ) -> str:
        """
        将 Markdown 内容转换为可打印的 HTML。

        使用 markdown2 库解析 Markdown，并应用增强的 CSS 样式模板，
        包括中文字体（Noto Sans SC）、专业配色、表格样式和页眉页脚。
        支持将本地图片路径转换为 file:// URL 以便 Playwright 加载。

        Args:
            markdown: Markdown 格式的文本内容。
            title: 文档标题（可选），用于页眉显示。
            base_dir: 基础目录路径，用于解析相对路径的图片（可选）。

        Returns:
            完整的 HTML 文档字符串，包含增强的 CSS 样式。
        """
        html_body = cast(
            str,
            markdown2.markdown(
                markdown,
                extras=["tables", "fenced-code-blocks", "emoji", "markdown-in-html"],
            ),
        )
        
        # 处理本地图片路径，转换为 file:// URL 以便 Playwright 加载
        if base_dir:
            import re
            base_dir_resolved = str(base_dir.resolve())
            
            def replace_img_path(match: re.Match[str]) -> str:
                img_tag = match.group(0)
                # 提取 src 属性
                src_match = re.search(r'src="([^"]+)"', img_tag)
                if src_match:
                    src = src_match.group(1)
                    # 如果是相对路径且文件存在，转换为 file:// URL
                    if not src.startswith(('http://', 'https://', 'file://', 'data:')):
                        img_path = Path(src)
                        if not img_path.is_absolute():
                            img_path = base_dir / src
                        if img_path.exists():
                            file_url = img_path.resolve().as_uri()
                            return img_tag.replace(f'src="{src}"', f'src="{file_url}"')
                return img_tag
            
            html_body = re.sub(r'<img[^>]+>', replace_img_path, html_body)
        
        return get_html_template(title=title, content=html_body)

    def markdown_to_pdf(
        self,
        markdown_content: str,
        output_path: Path,
        title: str = "",
        base_dir: Optional[Path] = None,
    ) -> Path:
        """
        将 Markdown 内容直接转换为 PDF 文件。

        先将 Markdown 转换为 HTML，然后使用 Playwright 渲染并导出 PDF。

        Args:
            markdown_content: Markdown 格式的文本内容。
            output_path: PDF 输出文件路径。
            title: 文档标题（可选），用于日志输出。
            base_dir: 基础目录路径，用于解析相对路径的图片（可选）。

        Returns:
            生成的 PDF 文件的绝对路径。
        """
        html_content = self.printable_html_from_markdown(
            markdown_content, title=title, base_dir=base_dir
        )
        self.html_to_pdf(html_content, output_path)
        return output_path.resolve()

    def html_to_pdf(self, html: str, output_path: Path) -> None:
        """
        将 HTML 内容转换为 PDF 文件。

        使用 Playwright 的 Chromium 浏览器渲染 HTML，并导出为 A4 格式的 PDF。
        
        优化项：
        - 禁用 GPU、沙箱以提升性能
        - 使用 networkidle 确保资源加载完成
        - 禁用不必要的浏览器功能

        Args:
            html: HTML 文档字符串。
            output_path: PDF 输出文件路径。
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            # 优化：禁用 GPU、沙箱，使用 headless 模式提升性能
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--disable-setuid-sandbox",
                    "--no-sandbox",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                ]
            )
            # 优化：创建页面时禁用不必要的功能
            page = browser.new_page(
                viewport={"width": 1200, "height": 800},
                device_scale_factor=1,
                is_mobile=False,
                has_touch=False,
            )
            # 优化：禁用图片、字体加载以加速（如果不需要）
            # 但这里我们需要渲染完整内容，所以保持默认
            page.set_content(html, wait_until="networkidle", timeout=30000)
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "2cm", "bottom": "2cm", "left": "2cm", "right": "2cm"},
                prefer_css_page_size=True,
            )
            browser.close()

        resolved = str(output_path.resolve())
        print(f"✅ 已导出 PDF: {resolved}")
        print(f"OUTPUT_PATH={resolved}")
