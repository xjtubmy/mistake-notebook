#!/usr/bin/env python3
"""
错题分析报告生成脚本

用法:
    python3 analyze.py --student <学生名> [--subject <学科>] [--output <输出路径>]

功能:
    - 扫描所有错题的 YAML Frontmatter
    - 生成多维度统计分析报告
    - 输出 Markdown 格式（Obsidian 兼容）
"""

import argparse
import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

try:
    import yaml
except ImportError:
    print("警告：缺少 pyyaml 库，尝试使用简易解析")
    yaml = None


def parse_frontmatter(content: str) -> dict:
    """解析 YAML Frontmatter（支持多行列表）"""
    if yaml:
        try:
            match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1))
        except:
            pass
    
    # 简易解析（不依赖 yaml 库）
    data = {}
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        lines = match.group(1).strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # 处理列表（多行格式）
                if value == '' and i + 1 < len(lines) and lines[i+1].strip().startswith('-'):
                    value = []
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith('-'):
                        item = lines[i].strip().lstrip('-').strip()
                        value.append(item)
                        i += 1
                    data[key] = value
                    continue
                
                # 处理单行列表 [a, b, c]
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip() for v in value[1:-1].split(',')]
                data[key] = value
            i += 1
    return data


def scan_mistakes(student: str, subject: str = None) -> list:
    """扫描所有错题"""
    mistakes = []
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return mistakes
    
    # 查找所有 mistake.md 文件
    for mistake_file in base_path.rglob('mistake.md'):
        content = mistake_file.read_text(encoding='utf-8')
        frontmatter = parse_frontmatter(content)
        
        if not frontmatter:
            continue
        
        # 学科筛选
        if subject and frontmatter.get('subject') != subject:
            continue
        
        mistakes.append({
            'path': mistake_file,
            'frontmatter': frontmatter,
            'content': content
        })
    
    return mistakes


def generate_report(student: str, mistakes: list, subject: str = None) -> str:
    """生成分析报告"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 统计数据
    total = len(mistakes)
    by_subject = defaultdict(int)
    by_error_type = defaultdict(int)
    by_knowledge_point = defaultdict(int)
    by_unit = defaultdict(int)
    by_status = defaultdict(int)
    by_difficulty = defaultdict(int)
    due_reviews = []  # 待复习
    
    for m in mistakes:
        fm = m['frontmatter']
        by_subject[fm.get('subject', 'unknown')] += 1
        by_error_type[fm.get('error-type', '未分类')] += 1
        by_knowledge_point[fm.get('knowledge-point', '未分类')] += 1
        
        unit_key = f"{fm.get('grade', '')}-{fm.get('semester', '')}-{fm.get('unit', '')}"
        by_unit[unit_key] += 1
        
        by_status[fm.get('status', 'unknown')] += 1
        by_difficulty[fm.get('difficulty', '⭐')] += 1
        
        # 检查是否需要复习
        due_date = fm.get('due-date', '')
        if due_date:
            due_date_str = str(due_date) if not isinstance(due_date, str) else due_date
            if due_date_str <= now[:10] and fm.get('mastered') != True:
                due_reviews.append({
                    'id': fm.get('id', 'unknown'),
                    'knowledge_point': fm.get('knowledge-point', ''),
                    'due_date': due_date_str,
                    'review_round': fm.get('review-round', 0),
                    'path': m['path']
                })
    
    # 生成报告
    report = f"""---
type: analysis-report
student: {student}
subject: {subject if subject else 'all'}
generated: {now}
---

# 📊 错题分析报告

**学生**：[[../profile|{student}]]  
**生成时间**：{now}  
**筛选条件**：{subject if subject else '全部学科'}

---

## 📈 总体统计

| 指标 | 数值 |
|------|------|
| 错题总数 | {total} |
| 待复习 | {by_status.get('待复习', 0)} |
| 复习中 | {by_status.get('复习中', 0)} |
| 已掌握 | {by_status.get('已掌握', 0)} |

---

## 📚 按学科分布

| 学科 | 错题数 | 占比 |
|------|--------|------|
"""
    
    for subj, count in sorted(by_subject.items(), key=lambda x: -x[1]):
        pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
        report += f"| {subj} | {count} | {pct} |\n"
    
    report += f"""
---

## ❌ 错误类型分布

| 错误类型 | 数量 | 占比 |
|---------|------|------|
"""
    
    for err_type, count in sorted(by_error_type.items(), key=lambda x: -x[1]):
        pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
        report += f"| {err_type} | {count} | {pct} |\n"
    
    report += f"""
---

## 🎯 知识点 TOP10

| 知识点 | 错题数 |
|--------|--------|
"""
    
    for kp, count in sorted(by_knowledge_point.items(), key=lambda x: -x[1])[:10]:
        report += f"| {kp} | {count} |\n"
    
    # 今日待复习
    report += f"""
---

## ⏰ 今日待复习 ({len(due_reviews)} 道)

"""
    
    if due_reviews:
        report += """| 错题 ID | 知识点 | 复习轮次 | 到期日期 | 链接 |
|--------|--------|---------|---------|------|
"""
        for r in due_reviews[:20]:  # 最多显示 20 道
            rel_path = r['path'].relative_to(Path(f'mistake-notebook/students/{student}'))
            report += f"| {r['id']} | {r['knowledge_point']} | 第{int(r['review_round'])+1}轮 | {r['due_date']} | [[{rel_path}]] |\n"
    else:
        report += "🎉 暂无待复习的错题！\n"
    
    # 难度分布
    report += f"""
---

## ⭐ 难度分布

| 难度 | 数量 |
|------|------|
"""
    
    for diff in ['⭐⭐⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐', '⭐⭐', '⭐']:
        if by_difficulty.get(diff, 0) > 0:
            report += f"| {diff} | {by_difficulty[diff]} |\n"
    
    report += f"""
---

## 📁 按单元分布

| 单元 | 错题数 |
|------|--------|
"""
    
    for unit, count in sorted(by_unit.items(), key=lambda x: -x[1]):
        report += f"| {unit} | {count} |\n"
    
    report += f"""
---

## 🔗 快速链接

- [[../profile|返回学生主页]]
- {f'[[./{subject}/README|返回 {subject} 学科]]' if subject else ''}
- [[./README|返回错题总览]]

---

**报告生成时间**：{now}
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description='错题分析报告生成')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--subject', help='学科筛选（可选）')
    parser.add_argument('--output', help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    # 扫描错题
    print(f"正在扫描 {args.student} 的错题...")
    mistakes = scan_mistakes(args.student, args.subject)
    print(f"找到 {len(mistakes)} 道错题")
    
    if not mistakes:
        print("未找到错题数据")
        return
    
    # 生成报告
    report = generate_report(args.student, mistakes, args.subject)
    
    # 输出
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(report, encoding='utf-8')
        print(f"报告已保存：{args.output}")
    else:
        # 默认保存到 reports 目录
        output_dir = Path(f'data/mistake-notebook/students/{args.student}/reports')
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        subject_suffix = f'-{args.subject}' if args.subject else ''
        output_path = output_dir / f'analysis-{timestamp}{subject_suffix}.md'
        output_path.write_text(report, encoding='utf-8')
        print(f"报告已保存：{output_path}")


if __name__ == '__main__':
    main()
