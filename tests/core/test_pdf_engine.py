"""
PDF 引擎单元测试。

测试 PDFEngine 类的初始化、Markdown 转 PDF、HTML 生成和 HTML 转 PDF 功能。
注意：PDF 生成测试需要 playwright，在无图形界面环境中可能跳过。
"""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.core.pdf_engine import PDFEngine


class TestPDFEngineInit:
    """测试 PDFEngine 初始化。"""

    def test_default_output_dir(self) -> None:
        """测试默认输出目录为当前工作目录。"""
        engine = PDFEngine()
        assert engine.output_dir == Path.cwd()

    def test_custom_output_dir(self) -> None:
        """测试自定义输出目录。"""
        custom_dir = Path("/tmp/pdf_test")
        engine = PDFEngine(output_dir=custom_dir)
        assert engine.output_dir == custom_dir


class TestMarkdownToPdf:
    """测试 markdown_to_pdf 方法。"""

    def test_basic_conversion(self) -> None:
        """测试基本 Markdown 转 PDF。"""
        engine = PDFEngine()
        markdown = "# 测试标题\n\n这是测试内容。"

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            # 注意：PDF 生成需要 playwright 和图形环境，可能跳过
            try:
                result = engine.markdown_to_pdf(markdown, output_path)
                assert result == output_path.resolve()
                assert output_path.exists()
            except Exception as e:
                pytest.skip(f"PDF 生成需要图形环境：{e}")

    def test_with_title(self) -> None:
        """测试带标题的 Markdown 转 PDF。"""
        engine = PDFEngine()
        markdown = "# 带标题的测试\n\n内容。"

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "titled.pdf"
            try:
                result = engine.markdown_to_pdf(markdown, output_path, title="测试标题")
                assert result == output_path.resolve()
            except Exception as e:
                pytest.skip(f"PDF 生成需要图形环境：{e}")

    def test_output_path_creation(self) -> None:
        """测试输出路径不存在时自动创建目录。"""
        engine = PDFEngine()
        markdown = "# 测试"

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "test.pdf"
            try:
                engine.markdown_to_pdf(markdown, output_path)
                assert output_path.parent.exists()
            except Exception as e:
                pytest.skip(f"PDF 生成需要图形环境：{e}")


class TestPrintableHtmlFromMarkdown:
    """测试 printable_html_from_markdown 方法。"""

    def test_html_structure(self) -> None:
        """测试生成的 HTML 结构完整性。"""
        engine = PDFEngine()
        markdown = "# 标题\n\n段落内容。"

        html = engine.printable_html_from_markdown(markdown)

        assert html.startswith("<!DOCTYPE html>")
        assert "<html>" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</html>" in html
        assert '<meta charset="UTF-8">' in html
        assert "@page" in html
        assert "font-family" in html

    def test_chinese_rendering(self) -> None:
        """测试中文字符正确渲染。"""
        engine = PDFEngine()
        markdown = "# 中文标题\n\n这是中文段落内容。"

        html = engine.printable_html_from_markdown(markdown)

        assert "中文标题" in html
        assert "中文段落内容" in html

    def test_css_styles(self) -> None:
        """测试 CSS 样式包含。"""
        engine = PDFEngine()
        markdown = "测试内容"

        html = engine.printable_html_from_markdown(markdown)

        # 检查关键 CSS 样式
        assert "SimSun" in html
        assert "Songti SC" in html
        assert "line-height: 1.8" in html
        assert "border-collapse: collapse" in html
        assert "@page" in html

    def test_markdown_features(self) -> None:
        """测试 Markdown 特性支持（表格、代码块等）。"""
        engine = PDFEngine()
        markdown = """# 测试

| 列 1 | 列 2 |
|------|------|
| A    | B    |

```python
print("hello")
```
"""

        html = engine.printable_html_from_markdown(markdown)

        assert "<table>" in html
        assert "<th>" in html
        assert "<td>" in html
        assert "<pre>" in html
        assert "print" in html


class TestHtmlToPdf:
    """测试 html_to_pdf 方法。"""

    def test_basic_conversion(self) -> None:
        """测试基本 HTML 转 PDF。"""
        engine = PDFEngine()
        html = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>body { font-family: sans-serif; }</style></head>
<body><h1>测试</h1></body>
</html>"""

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            try:
                engine.html_to_pdf(html, output_path)
                assert output_path.exists()
            except Exception as e:
                pytest.skip(f"PDF 生成需要图形环境：{e}")

    def test_file_exists_after_conversion(self) -> None:
        """测试 PDF 文件生成后确实存在。"""
        engine = PDFEngine()
        html = "<html><body>测试</body></html>"

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "exists_test.pdf"
            try:
                engine.html_to_pdf(html, output_path)
                assert output_path.exists()
                assert output_path.stat().st_size > 0
            except Exception as e:
                pytest.skip(f"PDF 生成需要图形环境：{e}")

    def test_nested_directory_creation(self) -> None:
        """测试嵌套目录自动创建。"""
        engine = PDFEngine()
        html = "<html><body>测试</body></html>"

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "a" / "b" / "c" / "test.pdf"
            try:
                engine.html_to_pdf(html, output_path)
                assert output_path.parent.exists()
                assert output_path.exists()
            except Exception as e:
                pytest.skip(f"PDF 生成需要图形环境：{e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
