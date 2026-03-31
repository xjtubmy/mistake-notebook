#!/usr/bin/env python3
"""
错题分享脚本 - 统一生成长图（含完整解析）

用法:
    python3 share.py --student <学生名> --output <输出路径> [筛选条件]

说明:
    从 analysis.md 读取完整解析，生成长图适合飞书/微信分享复习
"""

import argparse
import sys
import re
from pathlib import Path
from datetime import datetime


def load_mistakes_for_share(student: str, subject: str = None, limit: int = 5) -> list:
    """加载错题（从 analysis.md 读取完整解析）"""
    mistakes = []
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return mistakes
    
    for analysis_file in base_path.rglob('analysis.md'):
        if len(mistakes) >= limit:
            break
        
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
        
        # 获取对应的 mistake.md 文件
        mistake_file = analysis_file.parent / 'mistake.md'
        mistake_content = ""
        if mistake_file.exists():
            mistake_content = mistake_file.read_text(encoding='utf-8')
        
        # 从 mistake.md 提取题目和答案
        question_match = re.search(r'## 📖 题目\s*\n(.*?)(?=## |---|$)', mistake_content, re.DOTALL)
        if not question_match:
            question_match = re.search(r'## 题目\s*\n(.*?)(?=## |---|$)', mistake_content, re.DOTALL)
        question = question_match.group(1).strip() if question_match else ''
        
        # 提取选项（从题目文本中）
        options = []
        for line in question.split('\n'):
            if re.match(r'^- [A-D]\.', line):
                options.append(line.lstrip('- ').strip())
        
        # 从 mistake.md 提取答案
        student_answer_match = re.search(r'\*\*学生作答\*\*：(.+)', mistake_content)
        correct_answer_match = re.search(r'\*\*正确答案\*\*：(.+)', mistake_content)
        student_answer = student_answer_match.group(1).strip() if student_answer_match else '未作答'
        correct_answer = correct_answer_match.group(1).strip() if correct_answer_match else '未知'
        
        # 从 analysis.md 提取核心考点
        key_points = []
        kp_match = re.search(r'## 🎯 核心考点\s*\n(.*?)(?=## |---|$)', content, re.DOTALL)
        if kp_match:
            for line in kp_match.group(1).strip().split('\n'):
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
            mnemonic = mnemonic.replace('\n', ' ')
        
        # 从 analysis.md 提取解题步骤
        steps = []
        steps_match = re.search(r'## 🧠 解题三步法\s*\n```\s*\n(.+?)```', content, re.DOTALL)
        if steps_match:
            steps_text = steps_match.group(1).strip()
            for line in steps_text.split('\n'):
                line = line.strip()
                if line:
                    steps.append(line)
        
        # 从 analysis.md 提取易错点
        error_points = []
        error_match = re.search(r'## ⚠️ 易错点警示\s*\n\|(.+?)\|', content, re.DOTALL)
        if error_match:
            table_content = error_match.group(1).strip()
            for line in table_content.split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        wrong = parts[0].strip().strip('"')
                        correct = parts[1].strip().strip('"')
                        if wrong and correct:
                            error_points.append({'wrong': wrong, 'correct': correct})
        
        mistakes.append({
            'id': fm.get('parent', analysis_file.parent.name),
            'knowledge_point': fm.get('knowledge-point', '未知'),
            'subject': fm.get('subject', 'unknown'),
            'question': question,
            'options': options,
            'student_answer': student_answer,
            'correct_answer': correct_answer,
            'key_points': key_points,
            'mnemonic': mnemonic,
            'steps': steps,
            'error_points': error_points,
        })
    
    return mistakes


def generate_html(mistakes: list, student: str, subject: str = None) -> str:
    """生成 HTML（长图用，含完整解析）"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
            }}
            .container {{
                max-width: 700px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 24px 20px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 22px;
                margin-bottom: 8px;
                font-weight: 600;
            }}
            .header .meta {{
                font-size: 13px;
                opacity: 0.9;
            }}
            .content {{
                padding: 24px 20px;
            }}
            .mistake {{
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 24px;
                background: #fafafa;
            }}
            .mistake:last-child {{
                margin-bottom: 0;
            }}
            .mistake-header {{
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 2px solid #667eea;
            }}
            .mistake-title {{
                font-size: 17px;
                font-weight: 600;
                color: #667eea;
            }}
            .section {{
                margin: 16px 0;
            }}
            .section-title {{
                font-size: 13px;
                font-weight: 600;
                color: #667eea;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .question {{
                background: white;
                padding: 14px;
                border-radius: 8px;
                border-left: 3px solid #667eea;
                margin: 8px 0;
                font-size: 14px;
                line-height: 1.7;
            }}
            .options {{
                margin: 12px 0 12px 16px;
            }}
            .options li {{
                margin: 6px 0;
                list-style: none;
                font-size: 14px;
            }}
            .options li::before {{
                content: "• ";
                color: #667eea;
                font-weight: bold;
            }}
            .answer-box {{
                display: flex;
                gap: 12px;
                margin: 16px 0;
            }}
            .answer {{
                flex: 1;
                padding: 12px;
                border-radius: 8px;
                text-align: center;
            }}
            .answer.wrong {{
                background: #ffe0e0;
                border: 2px solid #ff6b6b;
            }}
            .answer.correct {{
                background: #e0ffe0;
                border: 2px solid #4caf50;
            }}
            .answer-label {{
                font-size: 11px;
                color: #666;
                margin-bottom: 4px;
            }}
            .answer-value {{
                font-size: 15px;
                font-weight: 600;
            }}
            .answer-value.wrong {{ color: #d32f2f; }}
            .answer-value.correct {{ color: #388e3c; }}
            .key-points {{
                background: #fff9e6;
                padding: 14px;
                border-radius: 8px;
                border-left: 3px solid #ffc107;
            }}
            .key-points li {{
                margin: 6px 0;
                list-style: none;
                font-size: 14px;
            }}
            .key-points li::before {{
                content: "✓ ";
                color: #ffc107;
                font-weight: bold;
            }}
            .steps {{
                background: #e8f5e9;
                padding: 14px;
                border-radius: 8px;
                border-left: 3px solid #4caf50;
                font-size: 13px;
                line-height: 1.8;
                white-space: pre-line;
            }}
            .error-points {{
                background: #ffebee;
                padding: 14px;
                border-radius: 8px;
                border-left: 3px solid #f44336;
            }}
            .error-point {{
                margin: 8px 0;
                font-size: 13px;
            }}
            .error-point::before {{
                content: "⚠️ ";
            }}
            .error-wrong {{
                color: #d32f2f;
                text-decoration: line-through;
                font-size: 12px;
            }}
            .error-correct {{
                color: #388e3c;
                font-weight: 500;
            }}
            .mnemonic {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 14px;
                border-radius: 8px;
                text-align: center;
                font-style: italic;
                color: #555;
                margin: 16px 0;
                border: 2px dashed #667eea;
                font-size: 14px;
                line-height: 1.6;
            }}
            .footer {{
                text-align: center;
                padding: 16px;
                color: #999;
                font-size: 11px;
                border-top: 1px solid #e0e0e0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📓 {student} 的错题本</h1>
                <div class="meta">
                    <span>学科：{subject if subject else '全部'}</span> • 
                    <span>数量：{len(mistakes)} 道</span> • 
                    <span>生成：{datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
                </div>
            </div>
            
            <div class="content">
    """
    
    for i, m in enumerate(mistakes, 1):
        kp = m.get('knowledge_point', '未知')
        student_answer = m.get('student_answer', '未作答')
        correct_answer = m.get('correct_answer', '未知')
        question = m.get('question', '')
        options = m.get('options', [])
        key_points = m.get('key_points', [])
        mnemonic = m.get('mnemonic', '')
        steps = m.get('steps', [])
        error_points = m.get('error_points', [])
        
        # 清理题目中的 markdown
        question_clean = re.sub(r'^#+\s*', '', question)
        question_clean = re.sub(r'\*\*(.+?)\*\*', r'\1', question_clean)
        question_clean = re.sub(r'`(.+?)`', r'\1', question_clean)
        
        html += f"""
                <div class="mistake">
                    <div class="mistake-header">
                        <div class="mistake-title">错题 {i}：{kp}</div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">题目</div>
                        <div class="question">{question_clean}</div>
                        {"".join(f'<div class="options"><li>{opt}</li></div>' for opt in options) if options else ''}
                    </div>
                    
                    <div class="answer-box">
                        <div class="answer wrong">
                            <div class="answer-label">❌ 学生作答</div>
                            <div class="answer-value wrong">{student_answer}</div>
                        </div>
                        <div class="answer correct">
                            <div class="answer-label">✅ 正确答案</div>
                            <div class="answer-value correct">{correct_answer}</div>
                        </div>
                    </div>
                    
                    {f'''
                    <div class="section">
                        <div class="section-title">核心考点</div>
                        <ul class="key-points">
                            {"".join(f'<li>{p}</li>' for p in key_points)}
                        </ul>
                    </div>
                    ''' if key_points else ''}
                    
                    {f'''
                    <div class="section">
                        <div class="section-title">解题思路</div>
                        <div class="steps">{"\n".join(steps)}</div>
                    </div>
                    ''' if steps else ''}
                    
                    {f'''
                    <div class="section">
                        <div class="section-title">易错点</div>
                        <div class="error-points">
                            {"".join(f'<div class="error-point"><span class="error-wrong">{ep["wrong"]}</span><br>→ <span class="error-correct">{ep["correct"]}</span></div>' for ep in error_points)}
                        </div>
                    </div>
                    ''' if error_points else ''}
                    
                    {f'<div class="mnemonic">📿 {mnemonic}</div>' if mnemonic else ''}
                </div>
        """
    
    html += f"""
            </div>
            
            <div class="footer">
                生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} · mistake-notebook
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def html_to_image(html_content: str, output_path: str):
    """HTML 转图片（使用 Playwright）"""
    from playwright.sync_api import sync_playwright
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # 设置视口宽度（手机宽度）
        page.set_viewport_size({"width": 800, "height": 600})
        
        # 加载 HTML
        page.set_content(html_content, wait_until='networkidle')
        
        # 获取完整页面高度
        height = page.evaluate("document.documentElement.scrollHeight")
        
        # 调整视口高度
        page.set_viewport_size({"width": 800, "height": height + 40})
        
        # 截图
        page.screenshot(path=output_path, full_page=True, type='png')
        
        browser.close()
    
    print(f"✅ 已生成长图：{output_path}")


def main():
    parser = argparse.ArgumentParser(description='错题分享 - 生成长图（含解析）')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--subject', help='学科筛选')
    parser.add_argument('--limit', type=int, default=5, help='错题数量限制')
    parser.add_argument('--output', help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    print(f"📱 生成长图（含完整解析）...")
    print(f"📚 学生：{args.student}")
    print(f"📖 学科：{args.subject if args.subject else '全部'}")
    print()
    
    # 加载错题（从 analysis.md）
    mistakes = load_mistakes_for_share(args.student, args.subject, args.limit)
    print(f"📋 找到 {len(mistakes)} 道错题\n")
    
    if not mistakes:
        print("⚠️  未找到错题")
        return
    
    # 生成 HTML
    html_content = generate_html(mistakes, args.student, args.subject)
    
    # 生成图片
    if args.output:
        output_path = args.output
    else:
        output_dir = Path(f'data/mistake-notebook/students/{args.student}/exports')
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        output_path = output_dir / f'{timestamp}-share.png'
    
    html_to_image(html_content, str(output_path))
    
    print(f"\n📝 使用建议：")
    print(f"   • 长图包含完整解析，可直接用于复习")
    print(f"   • 如需打印完整版，请运行：")
    print(f"     python3 skills/mistake-notebook/scripts/export-printable.py \\")
    print(f"       --student {args.student} --output exports/print.pdf --format pdf")


if __name__ == '__main__':
    main()
