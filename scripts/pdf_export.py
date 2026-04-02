"""
Playwright 将 Markdown 转为可打印 HTML 并导出 PDF，供 export-printable、generate-practice 等复用。
"""

from __future__ import annotations

from pathlib import Path


def printable_html_from_markdown(md_content: str) -> str:
    import markdown2

    html_body = markdown2.markdown(
        md_content,
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


def html_to_pdf(html_content: str, output_path: str) -> None:
    from playwright.sync_api import sync_playwright

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "2cm", "bottom": "2cm", "left": "2cm", "right": "2cm"},
        )
        browser.close()

    resolved = str(Path(output_path).resolve())
    print(f"✅ 已导出 PDF: {resolved}")
    print(f"OUTPUT_PATH={resolved}")
