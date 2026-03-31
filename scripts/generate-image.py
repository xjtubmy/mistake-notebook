#!/usr/bin/env python3
"""
错题长图生成脚本（用于飞书/微信分享）

用法:
    python3 generate-image.py --student <学生名> --output <输出路径> [筛选条件]

依赖:
    pip install playwright  # 或使用 pyppeteer
    playwright install      # 安装浏览器
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime


def generate_html(mistakes: list, student: str, subject: str = None) -> str:
    """生成 HTML（长图用）"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
                line-height: 1.8;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                font-size: 24px;
                margin-bottom: 10px;
            }}
            .header .meta {{
                font-size: 14px;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px;
            }}
            .mistake {{
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 20px;
                background: #fafafa;
            }}
            .mistake:last-child {{
                margin-bottom: 0;
            }}
            .mistake-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #667eea;
            }}
            .mistake-title {{
                font-size: 18px;
                font-weight: bold;
                color: #667eea;
            }}
            .mistake-badge {{
                background: #ff6b6b;
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
            }}
            .section {{
                margin: 15px 0;
            }}
            .section-title {{
                font-size: 14px;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
            }}
            .section-title::before {{
                content: "📌";
                margin-right: 6px;
            }}
            .question {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                margin: 10px 0;
            }}
            .options {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .options li {{
                margin: 5px 0;
            }}
            .answer-box {{
                display: flex;
                gap: 20px;
                margin: 15px 0;
            }}
            .answer {{
                flex: 1;
                padding: 10px;
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
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }}
            .answer-value {{
                font-size: 16px;
                font-weight: bold;
            }}
            .key-points {{
                background: #fff9e6;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #ffc107;
            }}
            .key-points li {{
                margin: 5px 0;
                list-style: none;
            }}
            .key-points li::before {{
                content: "✓ ";
                color: #ffc107;
                font-weight: bold;
            }}
            .tips {{
                background: #e3f2fd;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #2196f3;
                margin: 15px 0;
            }}
            .tips-title {{
                font-weight: bold;
                color: #1976d2;
                margin-bottom: 8px;
            }}
            .mnemonic {{
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                font-style: italic;
                color: #555;
                margin: 15px 0;
                border: 2px dashed #667eea;
            }}
            .footer {{
                text-align: center;
                padding: 20px;
                color: #999;
                font-size: 12px;
                border-top: 1px solid #e0e0e0;
            }}
            .tag {{
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                margin: 2px;
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
        options = m.get('options', '')
        key_points = m.get('key_points', [])
        tips = m.get('tips', '')
        mnemonic = m.get('mnemonic', '')
        
        html += f"""
                <div class="mistake">
                    <div class="mistake-header">
                        <span class="mistake-title">错题 {i}：{kp}</span>
                        <span class="mistake-badge">待复习</span>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">题目</div>
                        <div class="question">{question}</div>
                        {f'<ul class="options">{options}</ul>' if options else ''}
                    </div>
                    
                    <div class="answer-box">
                        <div class="answer wrong">
                            <div class="answer-label">❌ 学生作答</div>
                            <div class="answer-value">{student_answer}</div>
                        </div>
                        <div class="answer correct">
                            <div class="answer-label">✅ 正确答案</div>
                            <div class="answer-value">{correct_answer}</div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <div class="section-title">核心考点</div>
                        <ul class="key-points">
                            {''.join(f'<li>{p}</li>' for p in key_points)}
                        </ul>
                    </div>
                    
                    {f'<div class="mnemonic">📿 {mnemonic}</div>' if mnemonic else ''}
                    
                    {f'<div class="tips"><div class="tips-title">💡 提示</div>{tips}</div>' if tips else ''}
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
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("错误：缺少 playwright 库")
        print("请运行：pip install playwright")
        print("然后运行：playwright install")
        sys.exit(1)
    
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
        page.set_viewport_size({"width": 800, "height": height})
        
        # 截图
        page.screenshot(path=output_path, full_page=True, type='png')
        
        browser.close()
    
    print(f"已生成长图：{output_path}")


def main():
    # 临时实现：从现有错题数据生成
    print("⚠️  长图生成功能需要完整实现数据加载")
    print("当前先创建脚本框架，后续完善...")
    
    # 示例输出
    print("\n用法示例：")
    print("python3 skills/mistake-notebook/scripts/generate-image.py \\")
    print("  --student 曲凌松 \\")
    print("  --subject physics \\")
    print("  --output data/mistake-notebook/students/曲凌松/exports/physics-share.png")


if __name__ == '__main__':
    main()
