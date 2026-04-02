#!/usr/bin/env python3
"""
举一反三练习生成脚本

用法:
    python3 generate-practice.py --student <学生名> --knowledge <知识点> [--count <数量>] [--style <风格>] [--md-only]

功能:
    - 基于错题知识点动态生成相似题
    - 每次生成不同的题目（避免固化）
    - 支持多种风格（基础/变式/提升）
    - 默认同时生成 Markdown 与同名的 PDF（Playwright）；可用 --md-only 跳过 PDF
"""

import argparse
import sys
import random
from pathlib import Path
from datetime import datetime

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import output_naming as out_names
import pdf_export


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
    # 可扩展更多知识点...
}


def generate_practice(knowledge_point: str, style: str = '混合', count: int = 3) -> list:
    """生成练习题"""
    templates = PRACTICE_TEMPLATES.get(knowledge_point, None)
    
    if not templates:
        # 通用模板（如果没有特定知识点模板）
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


def build_practice_markdown(practices: list, student: str, knowledge_point: str) -> str:
    """组装练习 Markdown 正文。"""
    content = f"""# 📝 举一反三练习

**学生**：{student}  
**知识点**：{knowledge_point}  
**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}  
**题目数量**：{len(practices)} 道

---

## 练习题

"""

    for i, p in enumerate(practices, 1):
        content += f"""### 第 {i} 题

{p['question']}

"""
        if 'options' in p:
            content += f"{p['options']}\n\n"

        content += f"""<details>
<summary>点击查看答案与解析</summary>

**答案**：{p['answer']}

**解析**：{p['parse']}

</details>

---

"""

    content += f"""
## 📊 练习记录

| 日期 | 正确率 | 用时 | 签名 |
|------|--------|------|------|
| {datetime.now().strftime('%Y-%m-%d')} | /{len(practices)} | | |

---

## 💡 使用建议

1. **独立完成后对答案**：不要边做边看答案
2. **错题标记**：做错的题目标记出来，重点复习
3. **定期重做**：同一份练习可以间隔一周重做

---

*本练习由 mistake-notebook 动态生成 · 每次生成题目可能不同*
"""
    return content


def save_practice_md(content: str, output_path: str) -> None:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content, encoding='utf-8')
    print(f"已生成练习 Markdown：{output_path}")


def main():
    parser = argparse.ArgumentParser(description='举一反三练习生成')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--knowledge', required=True, help='知识点')
    parser.add_argument('--count', type=int, default=3, help='题目数量（默认 3）')
    parser.add_argument('--style', choices=['基础', '变式', '提升', '混合'], default='混合', help='题目风格')
    parser.add_argument('--output', help='Markdown 输出路径（可选）；PDF 为同路径 .pdf')
    parser.add_argument(
        '--md-only',
        action='store_true',
        help='只生成 Markdown，不导出 PDF',
    )
    
    args = parser.parse_args()
    
    print(f"正在为 {args.student} 生成《{args.knowledge}》练习题...")
    print(f"风格：{args.style} | 数量：{args.count}")
    
    practices = generate_practice(args.knowledge, args.style, args.count)
    
    if args.output:
        md_path = args.output
    else:
        md_path = str(out_names.default_practice_path(args.student, args.knowledge))

    content = build_practice_markdown(practices, args.student, args.knowledge)
    save_practice_md(content, md_path)
    md_p = Path(md_path)

    if args.md_only:
        out_names.print_output_path(md_p)
    else:
        out_names.print_output_path(md_p, "OUTPUT_PATH_MD")
        pdf_path = str(md_p.with_suffix(".pdf"))
        try:
            html = pdf_export.printable_html_from_markdown(content)
            pdf_export.html_to_pdf(html, pdf_path)
        except Exception as e:
            print(f"⚠️ PDF 未生成（已保留 Markdown）: {e}")
            out_names.print_output_path(md_p)


if __name__ == '__main__':
    main()
