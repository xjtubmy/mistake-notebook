#!/usr/bin/env python3
"""
家长汇报简报生成脚本

用法:
    python3 parent-brief.py --student <学生名> [--week <周数>] [--output <输出路径>]

功能:
    - 生成简洁的家长汇报（适合发微信/飞书）
    - 包含本周错题、进步情况、学习建议
    - 格式简洁，适合手机阅读
"""

import argparse
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def load_recent_mistakes(student: str, days: int = 7) -> list:
    """加载最近 N 天的错题"""
    mistakes = []
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return mistakes
    
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    for mistake_file in base_path.rglob('mistake.md'):
        content = mistake_file.read_text(encoding='utf-8')
        
        # 解析 YAML Frontmatter
        fm = {}
        match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            for line in match.group(1).strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    fm[key.strip()] = value.strip()
        
        created = fm.get('created', '')
        if created >= cutoff_date:
            mistakes.append({
                'id': fm.get('id', 'unknown'),
                'subject': fm.get('subject', 'unknown'),
                'knowledge_point': fm.get('knowledge-point', '未知'),
                'error_type': fm.get('error-type', '未分类'),
                'created': created,
                'mastered': fm.get('mastered', 'false') == 'true',
            })
    
    return mistakes


def generate_parent_brief(student: str, mistakes: list, days: int = 7) -> str:
    """生成家长简报"""
    total = len(mistakes)
    mastered = sum(1 for m in mistakes if m['mastered'])
    by_subject = defaultdict(int)
    
    for m in mistakes:
        by_subject[m['subject']] += 1
    
    # 学科名称映射
    subject_names = {
        'math': '数学',
        'chinese': '语文',
        'english': '英语',
        'physics': '物理',
        'chemistry': '化学',
        'biology': '生物',
        'history': '历史',
        'geography': '地理',
        'politics': '政治',
    }
    
    brief = f"""📊 {student} 学习简报

📅 统计周期：最近{days}天
📝 生成时间：{datetime.now().strftime('%m/%d %H:%M')}

━━━━━━━━━━━━━━━━━━

📈 总体情况

• 新增错题：{total} 道
• 已掌握：{mastered} 道
• 待复习：{total - mastered} 道

"""
    
    if by_subject:
        brief += "━━━━━━━━━━━━━━━━━━\n\n"
        brief += "📚 学科分布\n\n"
        
        for subj, count in sorted(by_subject.items(), key=lambda x: -x[1]):
            subj_name = subject_names.get(subj, subj)
            bar = '🟩' * min(count, 5)  # 最多 5 个图标
            brief += f"{subj_name}：{bar} {count}道\n"
    
    brief += """
━━━━━━━━━━━━━━━━━━

💡 学习建议

"""
    
    if total == 0:
        brief += "✅ 最近没有新增错题，继续保持！\n"
    else:
        # 找出最多的学科
        top_subject = max(by_subject.items(), key=lambda x: x[1])
        subj_name = subject_names.get(top_subject[0], top_subject[0])
        
        brief += f"1️⃣ 重点科目：{subj_name}（{top_subject[1]}道错题）\n\n"
        
        if total - mastered > 0:
            brief += f"2️⃣ 及时复习：还有 {total - mastered} 道错题待复习\n\n"
        
        brief += "3️⃣ 建议：每天花 10 分钟回顾错题\n"
    
    brief += f"""
━━━━━━━━━━━━━━━━━━

📅 下周目标

• 减少新增错题
• 完成所有待复习错题的复习
• 建立错题本使用习惯

━━━━━━━━━━━━━━━━━━

生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}
mistake-notebook 错题管理系统
"""
    
    return brief


def main():
    parser = argparse.ArgumentParser(description='家长汇报简报')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--week', type=int, default=1, help='统计最近 N 周')
    parser.add_argument('--output', help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    days = args.week * 7
    
    print(f"正在生成 {args.student} 的学习简报（最近{days}天）...")
    
    # 加载错题
    mistakes = load_recent_mistakes(args.student, days)
    print(f"找到 {len(mistakes)} 道错题\n")
    
    # 生成简报
    brief = generate_parent_brief(args.student, mistakes, days)
    
    # 输出
    if args.output:
        output_path = args.output
    else:
        output_dir = Path(f'data/mistake-notebook/students/{args.student}/reports')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f'parent-brief-{datetime.now().strftime("%Y%m%d")}.md'
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(brief, encoding='utf-8')
    print(f"✅ 家长简报已保存：{output_path}")
    
    # 打印简报内容
    print("\n" + "="*40)
    print(brief)


if __name__ == '__main__':
    main()
