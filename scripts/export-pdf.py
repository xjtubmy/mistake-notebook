#!/usr/bin/env python3
"""
错题本导出脚本（PDF/HTML/Markdown）

用法:
    python3 export-pdf.py --student <学生名> --output <输出路径> [筛选条件]

依赖:
    pip install markdown2 pdfkit

注意:
    PDF 导出需要 wkhtmltopdf:
    - Ubuntu: sudo apt-get install wkhtmltopdf
    - macOS: brew install wkhtmltopdf
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

try:
    import markdown2
    MARKDOWN2_AVAILABLE = True
except ImportError:
    MARKDOWN2_AVAILABLE = False


def load_mistakes(student: str, subject: str = None, knowledge_point: str = None) -> list:
    """
    加载学生错题

    Returns:
        错题列表，每项包含：{'path': ..., 'metadata': {...}}
    """
    mistakes = []
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        print(f"提示：未找到学生数据目录：{base_path}")
        return mistakes

    # 遍历所有 mistake.md 文件
    for mistake_file in base_path.rglob('mistake.md'):
        # 解析元数据（从路径中提取）
        # 路径结构：data/mistake-notebook/students/{student}/mistakes/{subject}/{stage}/{grade}/{semester}/{unit}/{id}/mistake.md
        parts = mistake_file.parts
        try:
            subj_idx = parts.index('mistakes') + 1
            subject_from_path = parts[subj_idx] if subj_idx < len(parts) else 'unknown'
        except:
            subject_from_path = 'unknown'
        
        # 从父目录获取知识点（unit 目录名）
        knowledge_point_from_path = mistake_file.parent.parent.name
        
        metadata = {
            'path': mistake_file.parent,  # 返回错题目录
            'mistake_file': mistake_file,
            'subject': subject_from_path,
            'knowledge_point': knowledge_point_from_path,
        }

        # 筛选
        if subject and metadata['subject'] != subject:
            continue
        if knowledge_point and metadata['knowledge_point'] != knowledge_point:
            continue

        mistakes.append(metadata)

    return mistakes


def generate_markdown(mistakes: list, student: str, subject: str = None) -> str:
    """生成 Markdown 格式（可打印版）"""
    content = f"""# 📓 {student} 的错题本

**学科**：{subject if subject else '全部'}  
**导出时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}  
**错题数量**：{len(mistakes)} 道

---

"""

    for i, mistake in enumerate(mistakes, 1):
        mistake_file = mistake.get('mistake_file') or mistake['path'] / 'mistake.md'
        analysis_file = mistake['path'] / 'analysis.md'
        
        # 读取错题元数据
        if mistake_file.exists():
            md_content = mistake_file.read_text(encoding='utf-8')
            # 提取知识点（从 YAML Frontmatter）
            import re
            kp_match = re.search(r'knowledge-point:\s*(.+)', md_content)
            knowledge_point = kp_match.group(1).strip() if kp_match else mistake['knowledge_point']
            
            content += f"""## 错题 {i}：{knowledge_point}

"""
        else:
            content += f"""## 错题 {i}：{mistake['knowledge_point']}

"""
        
        # 添加分析卡片内容
        if analysis_file.exists():
            content += analysis_file.read_text(encoding='utf-8')
        else:
            content += "*暂无分析卡片*\n"
        
        content += f"""
---

"""

    content += f"""
## 📝 使用说明

1. **打印建议**：A4 纸张，双面打印
2. **复习方法**：
   - 盖住答案，独立重做
   - 对照解析，理解思路
   - 完成举一反三练习
3. **掌握标准**：
   - ✅ 能独立正确解答
   - ✅ 能讲解解题思路
   - ✅ 能识别类似题目

**下次复习时间**：{datetime.now().strftime('%Y-%m-%d')} + 1 天（第 1 轮）

---

*本资料由 mistake-notebook 自动生成*
"""

    return content


def export_pdf(student: str, output: str, subject: str = None, knowledge_point: str = None):
    """导出 PDF"""
    mistakes = load_mistakes(student, subject, knowledge_point)

    if not mistakes:
        print("警告：未找到符合条件的错题")
        return

    # 生成 Markdown
    md_content = generate_markdown(mistakes, student)

    # 转换为 HTML
    html_content = markdown2.markdown(md_content, extras=['tables', 'fenced-code-blocks'])

    # 添加样式
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: "SimSun", serif; line-height: 1.8; padding: 40px; }}
            h1 {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            h2 {{ color: #333; border-left: 4px solid #4CAF50; padding-left: 10px; }}
            .metadata {{ color: #666; font-size: 0.9em; }}
            pre {{ background: #f5f5f5; padding: 10px; border-radius: 4px; }}
        </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """

    # 导出 PDF
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    pdfkit.from_string(styled_html, output)

    print(f"已导出 PDF: {output}")
    print(f"共 {len(mistakes)} 道错题")


def main():
    parser = argparse.ArgumentParser(description='错题本导出')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--subject', help='学科筛选')
    parser.add_argument('--knowledge-point', help='知识点筛选')
    parser.add_argument('--format', choices=['pdf', 'md'], default='md', help='输出格式（默认 md）')

    args = parser.parse_args()

    if args.format == 'pdf':
        if not PDFKIT_AVAILABLE or not MARKDOWN2_AVAILABLE:
            print("错误：PDF 导出需要依赖库")
            print("请运行：pip install markdown2 pdfkit")
            print("并安装 wkhtmltopdf: sudo apt-get install wkhtmltopdf")
            print("\n或者使用 Markdown 格式（无需依赖）：--format md")
            sys.exit(1)
        export_pdf(args.student, args.output, args.subject, args.knowledge_point)
    elif args.format == 'md':
        mistakes = load_mistakes(args.student, args.subject, args.knowledge_point)
        md_content = generate_markdown(mistakes, args.student, args.subject)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(md_content, encoding='utf-8')
        print(f"已导出 Markdown: {args.output}")
        print(f"共 {len(mistakes)} 道错题")


if __name__ == '__main__':
    main()
