#!/usr/bin/env python3
"""
错题本可打印文档生成脚本（Markdown + PDF）

用法:
    python3 export-printable.py --student <学生名> [--output <路径>] [筛选条件]

未指定 --output 时，写入 exports/，文件名为「日期+学科/全科」（中文日期）：
    {年}年{月}月{日}日-全科.pdf
    {年}年{月}月{日}日-数学.pdf（--subject math）
    {年}年{月}月{日}日-数学-单元2.pdf（带 --unit）
    可用 --date YYYY-MM-DD 指定文件名中的日期（默认今天）

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

# 添加项目根目录到路径以支持 scripts 模块导入
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts import output_naming as out_names  # noqa: E402
from scripts.core.pdf_engine import PDFEngine  # noqa: E402

# 创建 PDF 引擎实例
_pdf_engine = PDFEngine()


def load_mistakes(student: str, subject: str = None, unit: str = None) -> list:
    """加载学生错题（从 analysis.md 读取解析）"""
    mistakes = []
    
    # 尝试多个可能的数据目录
    possible_paths = [
        Path('/home/ubuntu/clawd/data/mistake-notebook/students'),
        Path(__file__).parent.parent.parent / 'data' / 'mistake-notebook' / 'students',
        Path.cwd() / 'data' / 'mistake-notebook' / 'students',
    ]
    
    base_path = None
    for p in possible_paths:
        if (p / student / 'mistakes').exists():
            base_path = p / student / 'mistakes'
            break
    
    if base_path is None:
        base_path = possible_paths[0] / student / 'mistakes'
    
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


def main():
    parser = argparse.ArgumentParser(description='错题本可打印文档生成')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument(
        '--output',
        default=None,
        help='输出文件路径；省略则按「日期+学科/全科」写入 exports/（见 output_naming）',
    )
    parser.add_argument('--subject', help='学科筛选')
    parser.add_argument('--unit', help='单元筛选')
    parser.add_argument('--format', choices=['md', 'pdf'], default='md', help='输出格式')
    parser.add_argument(
        '--date',
        metavar='YYYY-MM-DD',
        help='仅影响默认文件名中的日期（默认今天）',
    )
    
    args = parser.parse_args()
    ref_date = None
    if args.date:
        try:
            ref_date = datetime.strptime(args.date.strip(), '%Y-%m-%d')
        except ValueError:
            print(f"错误：--date 须为 YYYY-MM-DD，收到 {args.date!r}")
            sys.exit(1)
    output_path = args.output
    if not output_path:
        output_path = str(
            out_names.default_review_export_path(
                args.student, args.subject, args.unit, args.format, ref_date=ref_date
            )
        )
        print(f"未指定 --output，使用默认路径：{output_path}")
    
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
        styled_html = _pdf_engine.printable_html_from_markdown(md_content)
        _pdf_engine.html_to_pdf(styled_html, Path(output_path))
    else:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md_content, encoding='utf-8')
        out_names.print_output_path(out)
        print(f"已导出 Markdown: {out.resolve()}")
    
    print(f"共 {len(mistakes)} 道错题")


if __name__ == '__main__':
    main()
