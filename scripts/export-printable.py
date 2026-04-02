#!/usr/bin/env python3
"""
错题本可打印文档生成脚本（Markdown + PDF）

用法:
    python3 export-printable.py --student <学生名> [--output <路径>] [筛选条件]

未指定 --output 时，写入固定约定路径（便于飞书/cron 每次读同一文件），文件名为中文：
    data/mistake-notebook/students/<学生>/exports/最新-全部.pdf|md
    有 --subject 时：最新-<学科>.pdf（常见英文学科码会转为「物理」「数学」等）
    另有 --unit 时：最新-<学科>-单元<单元>.pdf

支持:
    - Markdown 格式
    - PDF 格式（使用 Playwright，图片 base64 嵌入）
"""

import argparse
import sys
import re
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional


def load_mistakes(student: str, subject: str = None, unit: str = None) -> list:
    """加载学生错题（从 analysis.md 读取解析）"""
    mistakes = []
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return mistakes

    for analysis_file in base_path.rglob('analysis.md'):
        content = analysis_file.read_text(encoding='utf-8')
        
        # 解析 YAML Frontmatter
        fm = {}
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            for line in match.group(1).strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    fm[key.strip()] = value.strip()
        
        # 学科筛选
        if subject and fm.get('subject') != subject:
            continue
        
        # 单元筛选
        if unit and fm.get('unit') != unit:
            continue
        
        # 获取对应的 mistake.md 文件
        mistake_file = analysis_file.parent / 'mistake.md'
        mistake_content = ""
        if mistake_file.exists():
            mistake_content = mistake_file.read_text(encoding='utf-8')
        
        # 获取图片（转 base64 用于 PDF）
        mistake_dir = analysis_file.parent
        image_base64 = None
        image_path = None
        for ext in ['webp', 'jpg', 'png']:
            img = mistake_dir / f'image.{ext}'
            if img.exists():
                image_path = img.resolve()
                with open(img, 'rb') as f:
                    image_data = f.read()
                    image_base64 = base64.b64encode(image_data).decode('utf-8')
                break
        
        # 从 mistake.md 提取题目
        question_match = re.search(r'## 📖 题目\s*\n(.*?)(?=## |---|$)', mistake_content, re.DOTALL)
        if not question_match:
            question_match = re.search(r'## 题目\s*\n(.*?)(?=## |---|$)', mistake_content, re.DOTALL)
        question = question_match.group(1).strip() if question_match else ''
        
        # 提取选项（单独处理，避免重复）
        options = []
        question_lines = question.split('\n')
        for line in question_lines:
            if re.match(r'^- [A-D]\.', line):
                options.append(line.strip())
        
        # 从 mistake.md 提取答案
        student_answer_match = re.search(r'\*\*学生作答\*\*：(.+)', mistake_content)
        correct_answer_match = re.search(r'\*\*正确答案\*\*：(.+)', mistake_content)
        student_answer = student_answer_match.group(1).strip() if student_answer_match else '未作答'
        correct_answer = correct_answer_match.group(1).strip() if correct_answer_match else '未知'
        
        # 从 analysis.md 提取核心考点
        key_points = []
        kp_match = re.search(r'## 🎯 核心考点\s*\n(.*?)(?=## |---|$)', content, re.DOTALL)
        if kp_match:
            kp_content = kp_match.group(1).strip()
            for line in kp_content.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or re.match(r'^\d+\.', line) or line.startswith('✓')):
                    clean = re.sub(r'^[-\d.✓]+\s*', '', line).strip()
                    clean = re.sub(r'\*\*', '', clean)
                    if clean and len(clean) < 150:
                        key_points.append(clean)
        
        # 从 analysis.md 提取记忆口诀
        mnemonic = ''
        mnemonic_match = re.search(r'## 📿 记忆口诀\s*\n>\s*\*\*(.+?)\*\*', content, re.DOTALL)
        if not mnemonic_match:
            mnemonic_match = re.search(r'## 📿 记忆口诀\s*\n>\s*(.+?)(?:\n\n|\n---|$)', content, re.DOTALL)
        if mnemonic_match:
            mnemonic = mnemonic_match.group(1).strip()
            mnemonic = re.sub(r'\*\*', '', mnemonic)
            mnemonic = mnemonic.replace('\n', ' ').strip()
        
        mistakes.append({
            'path': mistake_dir,
            'mistake_file': mistake_file,
            'analysis_file': analysis_file,
            'image_path': image_path,
            'image_base64': image_base64,
            'frontmatter': fm,
            'knowledge_point': fm.get('knowledge-point', '未知'),
            'subject': fm.get('subject', 'unknown'),
            'question': question,
            'options': options,
            'student_answer': student_answer,
            'correct_answer': correct_answer,
            'key_points': key_points,
            'mnemonic': mnemonic,
        })

    return mistakes


def _slug_segment(s: Optional[str]) -> str:
    """文件名段：保留中英文等可见字符，去掉路径非法字符。"""
    if not s:
        return ''
    t = str(s).strip()
    t = re.sub(r'[\s/\\:*?"<>|]+', '-', t)
    t = re.sub(r'-+', '-', t).strip('-')
    return (t[:100] if t else '')


# frontmatter 中学科常为英文码，默认文件名用中文更利于飞书展示
_SUBJECT_ZH = {
    'physics': '物理',
    'math': '数学',
    'mathematics': '数学',
    'chinese': '语文',
    'english': '英语',
    'chemistry': '化学',
    'biology': '生物',
    'history': '历史',
    'geography': '地理',
    'politics': '政治',
    'morality': '道法',
    'science': '科学',
    'it': '信息技术',
    'pe': '体育',
    'art': '美术',
    'music': '音乐',
}


def _subject_label_for_filename(subject: str) -> str:
    s = str(subject).strip()
    if not s:
        return '学科'
    z = _SUBJECT_ZH.get(s.lower())
    if z:
        return z
    return _slug_segment(s) or '学科'


def default_output_path(student: str, subject: Optional[str], unit: Optional[str], fmt: str) -> Path:
    """
    稳定默认路径，供飞书等自动化重复读取（每次覆盖同一文件）。
    文件名使用中文（最新-…），便于渠道与本地浏览识别。
    """
    base = Path(f'data/mistake-notebook/students/{student}/exports')
    ext = 'pdf' if fmt == 'pdf' else 'md'
    parts = []
    if subject:
        parts.append(_subject_label_for_filename(subject))
    if unit:
        u = _slug_segment(unit) or str(unit).strip() or '未知'
        parts.append(f'单元{u}')
    stem = '最新-全部' if not parts else '最新-' + '-'.join(parts)
    return base / f'{stem}.{ext}'


def generate_printable_md(mistakes: list, student: str, subject: str = None) -> str:
    """生成可打印 Markdown（精简版）"""
    content = f"""# 📓 {student} 的错题本

**学科**：{subject if subject else '全部'}  
**导出时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}  
**错题数量**：{len(mistakes)} 道

---

"""

    for i, m in enumerate(mistakes, 1):
        kp = m['knowledge_point']
        
        content += f"""## 错题 {i}：{kp}

"""
        
        # 添加图片（使用 base64 确保 PDF 能显示）
        if m.get('image_base64'):
            ext = m['image_path'].suffix.lstrip('.') if m['image_path'] else 'png'
            content += f"![原题](data:image/{ext};base64,{m['image_base64']})\n\n"
        
        # 添加题目
        content += f"""### 📖 题目

{m['question']}

"""
        
        # 添加选项（如果题目中已包含选项，不再重复添加）
        # 检查题目中是否已有选项
        has_options_in_question = bool(re.search(r'^- [A-D]\.', m['question'], re.MULTILINE))
        if not has_options_in_question and m['options']:
            content += "\n".join(m['options']) + "\n\n"
        
        content += f"""**学生作答**：{m['student_answer']}  
**正确答案**：{m['correct_answer']}

---

"""
        
        # 添加核心考点
        if m['key_points']:
            content += f"""### 🎯 核心考点

"""
            for p in m['key_points']:
                content += f"- {p}\n"
            content += "\n---\n\n"
        
        # 添加记忆口诀
        if m['mnemonic']:
            content += f"""### 📿 记忆口诀

> {m['mnemonic']}

---

"""
        
        # 添加复习记录表
        content += f"""### 📊 复习记录

| 轮次 | 日期 | 用时 | 掌握情况 |
|------|------|------|---------|
| 第 1 轮 | 2026-04-01 | | 😐 模糊 / 🙂 掌握 / 🤩 熟练 |
| 第 2 轮 | 2026-04-04 | | 😐 模糊 / 🙂 掌握 / 🤩 熟练 |
| 第 3 轮 | 2026-04-11 | | 😐 模糊 / 🙂 掌握 / 🤩 熟练 |
| 第 4 轮 | 2026-04-26 | | 😐 模糊 / 🙂 掌握 / 🤩 熟练 |
| 第 5 轮 | 2026-05-26 | | 😐 模糊 / 🙂 掌握 / 🤩 熟练 |

---

"""

    content += f"""
---

*生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} · mistake-notebook*
"""

    return content


def html_to_pdf(html_content: str, output_path: str):
    """HTML 转 PDF（使用 Playwright）"""
    from playwright.sync_api import sync_playwright
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # 加载 HTML
        page.set_content(html_content, wait_until='networkidle')
        
        # 生成 PDF（A4 尺寸）
        page.pdf(
            path=output_path,
            format='A4',
            print_background=True,
            margin={'top': '2cm', 'bottom': '2cm', 'left': '2cm', 'right': '2cm'}
        )
        
        browser.close()
    
    resolved = str(Path(output_path).resolve())
    print(f"✅ 已导出 PDF: {resolved}")
    print(f"OUTPUT_PATH={resolved}")


def main():
    parser = argparse.ArgumentParser(description='错题本可打印文档生成')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument(
        '--output',
        default=None,
        help='输出文件路径；省略则写入 exports/最新-全部 或 最新-<学科>… .pdf|md（中文文件名，稳定路径，便于飞书）',
    )
    parser.add_argument('--subject', help='学科筛选')
    parser.add_argument('--unit', help='单元筛选')
    parser.add_argument('--format', choices=['md', 'pdf'], default='md', help='输出格式')
    
    args = parser.parse_args()
    output_path = args.output
    if not output_path:
        output_path = str(default_output_path(args.student, args.subject, args.unit, args.format))
        print(f"未指定 --output，使用稳定默认路径：{output_path}")
    
    # 加载错题
    print(f"正在加载 {args.student} 的错题...")
    mistakes = load_mistakes(args.student, args.subject, args.unit)
    print(f"找到 {len(mistakes)} 道错题")
    
    if not mistakes:
        print("警告：未找到符合条件的错题")
        return
    
    # 生成 Markdown
    md_content = generate_printable_md(mistakes, args.student, args.subject)
    
    if args.format == 'pdf':
        # 生成 HTML（带打印样式）
        import markdown2
        html_content = markdown2.markdown(md_content, extras=['tables', 'fenced-code-blocks', 'emoji'])
        
        # 添加打印样式
        styled_html = f"""
        <!DOCTYPE html>
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
            </style>
        </head>
        <body>
        {html_content}
        </body>
        </html>
        """
        
        # 转换为 PDF
        html_to_pdf(styled_html, output_path)
    else:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md_content, encoding='utf-8')
        resolved = str(out.resolve())
        print(f"已导出 Markdown: {resolved}")
        print(f"OUTPUT_PATH={resolved}")
    
    print(f"共 {len(mistakes)} 道错题")


if __name__ == '__main__':
    main()
