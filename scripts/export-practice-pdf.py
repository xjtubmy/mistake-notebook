#!/usr/bin/env python3
"""
举一反三练习题 PDF 导出脚本

用法:
    python3 export-practice-pdf.py --student <学生名> --knowledge <知识点> --output <输出路径>

功能:
    动态生成练习题并导出为 PDF
"""

import argparse
import sys
import re
import random
import base64
from pathlib import Path
from datetime import datetime


# 知识点→练习模板映射
PRACTICE_TEMPLATES = {
    '力的合成': {
        '基础': [
            {
                'question': '一个物体在水平向右 {f1}N 的拉力作用下向右做匀速直线运动，若撤去拉力，在撤去瞬间物体受到的摩擦力大小为______N，方向向______。',
                'answer': '{f1}N，方向向左（与运动方向相反）',
                'parse': '匀速直线运动→摩擦力=拉力，方向与运动方向相反'
            },
            {
                'question': '用 {f1}N 的水平力推着一个重 {g}N 的木箱在水平地面上做匀速直线运动，木箱受到的摩擦力大小为______N。',
                'answer': '{f1}',
                'parse': '水平方向二力平衡：摩擦力=推力'
            },
        ],
        '变式': [
            {
                'question': '一个木块在水平桌面上向右做匀速直线运动，受到水平向右 {f1}N 的拉力。若突然将拉力增大到 {f2}N，此时木块受到的合力为______N，方向向______。',
                'answer': '{diff}N，方向向右',
                'parse': '合力 = 新拉力 - 摩擦力 = {f2} - {f1} = {diff}N'
            },
            {
                'question': '物体在水平拉力 F 作用下做匀速直线运动，若拉力突然变为 2F，则物体将做______运动（选填"加速"、"减速"或"匀速"）。',
                'answer': '加速',
                'parse': '拉力>摩擦力，合力向前，物体加速'
            },
        ],
        '提升': [
            {
                'question': '如图所示，物体 A 在水平拉力 F 作用下向左做匀速直线运动。若突然撤去拉力 F，同时在物体上施加一个水平向右的力 F\' = F，则撤去瞬间物体受到的合力大小为（ ）',
                'options': 'A. 0  B. F  C. 2F  D. 无法确定',
                'answer': 'C（2F）',
                'parse': '摩擦力 f = F（向右），外加力 F\' = F（向右），合力 = 2F'
            },
            {
                'question': '木块在水平桌面上运动，受到水平拉力 F1 = {f1}N 向左，摩擦力 f = {f2}N 向右。若再施加一个水平向右的力 F2 = {f3}N，则木块受到的合力为______N，方向向______。',
                'answer': '{result}N，方向向{dir}',
                'parse': '合力 = |F1 - (f + F2)|，方向由较大力决定'
            },
        ],
    },
    '牛顿第一定律': {
        '基础': [
            {
                'question': '一切物体在没有受到外力作用时，总保持______状态或______状态。',
                'answer': '静止；匀速直线运动',
                'parse': '牛顿第一定律的内容'
            },
            {
                'question': '惯性是物体保持原有______的性质，惯性的大小只与物体的______有关。',
                'answer': '运动状态；质量',
                'parse': '惯性是性质，不是力；质量是惯性大小的唯一量度'
            },
        ],
        '变式': [
            {
                'question': '关于惯性，下列说法正确的是（ ）',
                'options': 'A. 静止的物体没有惯性  B. 速度越大惯性越大  C. 质量越大惯性越大  D. 月球上没有惯性',
                'answer': 'C',
                'parse': '惯性是物体的固有属性，只与质量有关，与速度、位置无关'
            },
        ],
        '提升': [
            {
                'question': '踢出去的足球在地面上继续滚动，这是因为足球具有______；足球最终停下来，是因为受到______的作用。',
                'answer': '惯性；摩擦力（阻力）',
                'parse': '惯性使足球保持运动，阻力使足球减速'
            },
        ],
    },
}


def generate_practice(knowledge_point: str, style: str = '混合', count: int = 5) -> list:
    """生成练习题"""
    templates = PRACTICE_TEMPLATES.get(knowledge_point, None)
    
    if not templates:
        return generate_generic_practice(style, count)
    
    practices = []
    
    if style == '混合':
        all_practices = []
        for s in ['基础', '变式', '提升']:
            all_practices.extend(templates.get(s, []))
        practices = random.sample(all_practices, min(count, len(all_practices)))
    else:
        style_practices = templates.get(style, [])
        practices = random.sample(style_practices, min(count, len(style_practices)))
    
    # 填充参数（随机生成数值）
    result = []
    for p in practices:
        practice = p.copy()
        # 随机生成力的数值
        f1 = random.choice([5, 10, 15, 20, 25, 30])
        f2 = f1 + random.choice([5, 10, 15])
        f3 = random.choice([5, 10, 15])
        diff = f2 - f1
        result_force = abs(f1 - (f2 + f3))
        direction = '右' if (f2 + f3) > f1 else '左'
        
        # 替换模板中的占位符
        for key in ['question', 'answer', 'parse', 'options']:
            if key in practice:
                practice[key] = practice[key].format(
                    f1=f1, f2=f2, f3=f3, diff=diff, 
                    result=result_force, dir=direction,
                    g=random.choice([50, 100, 150, 200])
                )
        result.append(practice)
    
    return result


def generate_generic_practice(style: str, count: int) -> list:
    """生成通用练习题"""
    return [
        {
            'question': f'【{style}题】请回顾本知识点的核心概念，并完成相关练习。',
            'answer': '参见教材',
            'parse': '建议复习课本相关内容'
        }
    ] * count


def generate_practice_html(practices: list, student: str, knowledge_point: str) -> str:
    """生成 HTML（用于 PDF）- 答案放在最后"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 2cm; }}
            body {{
                font-family: "SimSun", "Songti SC", serif;
                line-height: 1.8;
                font-size: 12pt;
                color: #333;
            }}
            h1 {{
                text-align: center;
                color: #667eea;
                font-size: 18pt;
                margin-bottom: 10px;
            }}
            h2 {{
                color: #667eea;
                font-size: 14pt;
                border-bottom: 2px solid #667eea;
                padding-bottom: 8px;
                margin-top: 30px;
            }}
            .meta {{
                text-align: center;
                color: #666;
                font-size: 10pt;
                margin-bottom: 30px;
            }}
            .practice {{
                margin: 25px 0;
                page-break-inside: avoid;
            }}
            .question {{
                font-weight: 500;
                margin-bottom: 15px;
                min-height: 80px;
            }}
            .options {{
                margin: 10px 0 10px 30px;
            }}
            .options li {{
                margin: 5px 0;
                list-style: upper-alpha;
            }}
            .answer-section {{
                page-break-before: always;
                margin-top: 50px;
            }}
            .answer-item {{
                background: #f5f5f5;
                padding: 15px;
                border-left: 4px solid #667eea;
                margin: 15px 0;
                font-size: 11pt;
            }}
            .answer-label {{
                font-weight: bold;
                color: #667eea;
            }}
            .answer {{
                color: #388e3c;
                font-weight: 500;
            }}
            .parse {{
                margin-top: 10px;
                color: #555;
            }}
            .record-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 30px 0;
            }}
            .record-table th, .record-table td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: center;
            }}
            .record-table th {{
                background-color: #f5f5f5;
            }}
            .tips {{
                background: #fff9e6;
                padding: 15px;
                border-left: 4px solid #ffc107;
                margin: 30px 0;
            }}
            .footer {{
                text-align: center;
                color: #999;
                font-size: 9pt;
                margin-top: 40px;
                border-top: 1px solid #ddd;
                padding-top: 15px;
            }}
            .page-break {{
                page-break-before: always;
            }}
        </style>
    </head>
    <body>
        <h1>📝 举一反三专项练习</h1>
        <div class="meta">
            <strong>学生</strong>：{student} &nbsp;•&nbsp; 
            <strong>知识点</strong>：{knowledge_point} &nbsp;•&nbsp; 
            <strong>数量</strong>：{len(practices)} 道 &nbsp;•&nbsp; 
            <strong>生成</strong>：{datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        
        <div class="tips">
            <strong>💡 使用建议：</strong>
            <ul>
                <li>独立完成后对照答案</li>
                <li>错题标记出来重点复习</li>
                <li>一周后重做巩固</li>
            </ul>
        </div>
        
        <h2>📋 练习题</h2>
    """
    
    for i, p in enumerate(practices, 1):
        html += f"""
        <div class="practice">
            <div class="question"><strong>第 {i} 题</strong>：{p['question']}</div>
            {f'<ul class="options">{p["options"]}</ul>' if 'options' in p else ''}
        </div>
        """
    
    # 练习记录表
    html += f"""
        <h2>📊 练习记录</h2>
        <table class="record-table">
            <tr>
                <th>日期</th>
                <th>正确率</th>
                <th>用时</th>
                <th>签名</th>
            </tr>
            <tr>
                <td>{datetime.now().strftime('%Y-%m-%d')}</td>
                <td>/ {len(practices)}</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td>（一周后）</td>
                <td>/ {len(practices)}</td>
                <td></td>
                <td></td>
            </tr>
        </table>
    """
    
    # 答案部分（分页）
    html += f"""
        <div class="answer-section">
            <h2>✅ 答案与解析</h2>
    """
    
    for i, p in enumerate(practices, 1):
        html += f"""
            <div class="answer-item">
                <div class="answer-label">第 {i} 题答案：</div>
                <div class="answer">{p['answer']}</div>
                <div class="parse"><strong>解析：</strong>{p['parse']}</div>
            </div>
        """
    
    html += f"""
        </div>
        
        <div class="footer">
            生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} · mistake-notebook 错题管理系统
        </div>
    </body>
    </html>
    """
    
    return html


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
    
    print(f"✅ 已导出 PDF: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='举一反三练习题 PDF 导出')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--knowledge', required=True, help='知识点')
    parser.add_argument('--count', type=int, default=5, help='题目数量')
    parser.add_argument('--style', choices=['基础', '变式', '提升', '混合'], default='混合', help='题目风格')
    parser.add_argument('--output', required=True, help='输出文件路径')
    
    args = parser.parse_args()
    
    print(f"正在为 {args.student} 生成《{args.knowledge}》练习题...")
    print(f"风格：{args.style} | 数量：{args.count}")
    
    # 生成练习题
    practices = generate_practice(args.knowledge, args.style, args.count)
    
    # 生成 HTML
    html_content = generate_practice_html(practices, args.student, args.knowledge)
    
    # 导出 PDF
    html_to_pdf(html_content, args.output)
    
    print(f"共 {len(practices)} 道题目")


if __name__ == '__main__':
    main()
