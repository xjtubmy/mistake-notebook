#!/usr/bin/env python3
"""
薄弱知识点分析脚本

用法:
    python3 weak-points.py --student <学生名> [--top <数量>] [--output <输出路径>]

功能:
    - 分析所有错题，找出最薄弱的知识点 TOP N
    - 给出针对性学习建议
    - 生成分析报告
"""

import argparse
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def analyze_weak_points(student: str, top_n: int = 5) -> dict:
    """分析薄弱知识点"""
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    knowledge_points = defaultdict(list)
    
    if not base_path.exists():
        return knowledge_points
    
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
        
        kp = fm.get('knowledge-point', '未知')
        subject = fm.get('subject', 'unknown')
        error_type = fm.get('error-type', '未分类')
        created = fm.get('created', '')
        
        knowledge_points[kp].append({
            'subject': subject,
            'error_type': error_type,
            'created': created,
        })
    
    return knowledge_points


def generate_weak_points_report(student: str, knowledge_points: dict, top_n: int = 5) -> str:
    """生成薄弱知识点报告"""
    # 按错题数量排序
    sorted_kp = sorted(knowledge_points.items(), key=lambda x: -len(x[1]))[:top_n]
    
    report = f"""---
type: weak-points-report
student: {student}
generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 🎯 薄弱知识点分析报告

**学生**：{student}  
**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}  
**分析错题数**：{sum(len(v) for v in knowledge_points.values())} 道

---

## 📊 薄弱知识点 TOP {top_n}

| 排名 | 知识点 | 错题数 | 涉及学科 | 建议 |
|------|--------|--------|---------|------|
"""
    
    for i, (kp, mistakes) in enumerate(sorted_kp, 1):
        subjects = set(m['subject'] for m in mistakes)
        subject_str = ', '.join(subjects)
        
        # 根据错题数给出建议
        if len(mistakes) >= 5:
            suggestion = "🔴 立即专项突破"
        elif len(mistakes) >= 3:
            suggestion = "🟠 重点加强练习"
        else:
            suggestion = "🟡 正常复习巩固"
        
        report += f"| {i} | {kp} | {len(mistakes)} | {subject_str} | {suggestion} |\n"
    
    report += f"""
---

## 💡 详细分析

"""
    
    for i, (kp, mistakes) in enumerate(sorted_kp, 1):
        report += f"""### {i}. {kp}

**错题数量**：{len(mistakes)} 道

**涉及学科**：{', '.join(set(m['subject'] for m in mistakes))}

**错误类型分布**：
"""
        error_types = defaultdict(int)
        for m in mistakes:
            error_types[m['error_type']] += 1
        
        for err_type, count in sorted(error_types.items(), key=lambda x: -x[1]):
            report += f"- {err_type}：{count} 道\n"
        
        # 给出针对性建议
        report += f"""
**学习建议**：
"""
        if '概念不清' in error_types:
            report += "- 📖 回归课本，重新学习相关概念定义\n"
        if '计算错误' in error_types:
            report += "- ✏️ 每天 5 分钟计算练习，养成验算习惯\n"
        if '审题错误' in error_types:
            report += "- 🔍 读题时圈画关键词，读完复述题意\n"
        if '受力分析错误' in error_types or '逻辑错误' in error_types:
            report += "- 🧠 画图辅助理解，建立解题模板\n"
        
        report += f"""
**推荐练习**：
- 找 5-10 道同类题目集中练习
- 整理该知识点的解题思路模板
- 一周后重做这些错题

---

"""
    
    report += f"""
## 📅 突破计划

| 周次 | 目标 | 完成标记 |
|------|------|---------|
| 第 1 周 | 攻克第 1 名知识点 | [ ] |
| 第 2 周 | 攻克第 2 名知识点 | [ ] |
| 第 3 周 | 攻克第 3 名知识点 | [ ] |
| 第 4 周 | 巩固复习 | [ ] |

---

**生成于**：{datetime.now().strftime('%Y-%m-%d %H:%M')} · mistake-notebook
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description='薄弱知识点分析')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--top', type=int, default=5, help='显示前 N 个薄弱知识点')
    parser.add_argument('--output', help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    print(f"正在分析 {args.student} 的薄弱知识点...")
    
    # 分析
    knowledge_points = analyze_weak_points(args.student, args.top)
    
    if not knowledge_points:
        print("⚠️  未找到错题数据")
        return
    
    total_mistakes = sum(len(v) for v in knowledge_points.values())
    print(f"共分析 {total_mistakes} 道错题，涉及 {len(knowledge_points)} 个知识点\n")
    
    # 生成报告
    report = generate_weak_points_report(args.student, knowledge_points, args.top)
    
    # 输出
    if args.output:
        output_path = args.output
    else:
        output_dir = Path(f'data/mistake-notebook/students/{args.student}/reports')
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f'weak-points-report.md'
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(report, encoding='utf-8')
    print(f"✅ 薄弱知识点报告已保存：{output_path}")
    
    # 打印摘要
    print(f"\n📊 薄弱知识点 TOP 3:")
    sorted_kp = sorted(knowledge_points.items(), key=lambda x: -len(x[1]))[:3]
    for i, (kp, mistakes) in enumerate(sorted_kp, 1):
        print(f"  {i}. {kp}：{len(mistakes)} 道错题")


if __name__ == '__main__':
    main()
