#!/usr/bin/env python3
"""
月度错题总结报告生成脚本

用法:
    python3 monthly-report.py --student <学生名> --month <年月> [--subject <学科>] [--output <输出路径>]

功能:
    - 统计指定月份的错题数量、学科分布
    - 分析错误类型、知识点掌握情况
    - 生成月度学习报告（Markdown 格式）
"""

import argparse
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 添加项目根目录到路径以支持 scripts 模块导入
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts import output_naming as out_names


def load_mistakes_by_month(student: str, year_month: str) -> dict:
    """按月份加载错题"""
    mistakes_by_month = defaultdict(list)
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return mistakes_by_month
    
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
        
        # 提取创建日期
        created = fm.get('created', '')
        if not created.startswith(year_month):
            continue
        
        mistakes_by_month[created[:7]].append({
            'id': fm.get('id', 'unknown'),
            'subject': fm.get('subject', 'unknown'),
            'knowledge_point': fm.get('knowledge-point', '未知'),
            'error_type': fm.get('error-type', '未分类'),
            'created': created,
            'difficulty': fm.get('difficulty', '⭐'),
        })
    
    return mistakes_by_month


def generate_monthly_report(student: str, year_month: str, mistakes: list) -> str:
    """生成月度报告"""
    # 统计
    total = len(mistakes)
    by_subject = defaultdict(int)
    by_error_type = defaultdict(int)
    by_knowledge_point = defaultdict(int)
    by_difficulty = defaultdict(int)
    
    for m in mistakes:
        by_subject[m['subject']] += 1
        by_error_type[m['error_type']] += 1
        by_knowledge_point[m['knowledge_point']] += 1
        by_difficulty[m['difficulty']] += 1
    
    # 生成报告
    report = f"""---
type: monthly-report
student: {student}
month: {year_month}
generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 📊 {year_month} 月度错题总结报告

**学生**：{student}  
**月份**：{year_month}  
**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📈 总体统计

| 指标 | 数值 |
|------|------|
| 错题总数 | {total} |
| 涉及学科 | {len(by_subject)} |
| 平均每日错题 | {total/30:.1f} |

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

## 🎯 知识点掌握情况

| 知识点 | 错题数 | 掌握建议 |
|--------|--------|---------|
"""
    
    for kp, count in sorted(by_knowledge_point.items(), key=lambda x: -x[1])[:10]:
        suggestion = "重点复习" if count >= 3 else ("加强练习" if count >= 2 else "正常")
        report += f"| {kp} | {count} | {suggestion} |\n"
    
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

## 💡 学习建议

### 重点突破
"""
    
    # 找出最薄弱的知识点
    top_weak = sorted(by_knowledge_point.items(), key=lambda x: -x[1])[:3]
    if top_weak:
        report += "\n"
        for kp, count in top_weak:
            report += f"- **{kp}**：{count} 道错题，建议专项练习\n"
    
    report += f"""
### 错误类型改进
"""
    
    # 找出最多的错误类型
    top_error = sorted(by_error_type.items(), key=lambda x: -x[1])[:2]
    if top_error:
        report += "\n"
        for err_type, count in top_error:
            if '审题' in err_type:
                report += f"- **{err_type}**：建议读题时圈画关键词\n"
            elif '计算' in err_type:
                report += f"- **{err_type}**：建议每天 5 分钟计算练习\n"
            elif '概念' in err_type:
                report += f"- **{err_type}**：建议回归课本，重新学习概念\n"
            else:
                report += f"- **{err_type}**：针对性练习\n"
    
    report += f"""
---

## 📅 下月目标

- [ ] 减少 {top_error[0][0] if top_error else '错误'} 的发生
- [ ] 重点攻克 {top_weak[0][0] if top_weak else '薄弱知识点'}
- [ ] 建立错题复习习惯，每周复习 1 次

---

**生成于**：{datetime.now().strftime('%Y-%m-%d %H:%M')} · mistake-notebook
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description='月度错题总结报告')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--month', help='年月（YYYY-MM），默认为当前月份')
    parser.add_argument('--subject', help='仅统计该学科（与 frontmatter subject 一致，如 math / physics）')
    parser.add_argument('--output', help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    if not args.month:
        args.month = datetime.now().strftime('%Y-%m')
    
    print(f"正在生成 {args.student} 的 {args.month} 月度报告...")
    
    # 加载错题
    mistakes_by_month = load_mistakes_by_month(args.student, args.month)
    mistakes = mistakes_by_month.get(args.month, [])
    if args.subject:
        mistakes = [m for m in mistakes if m.get('subject') == args.subject]
    
    print(f"找到 {len(mistakes)} 道错题\n")
    
    if not mistakes:
        print(f"⚠️  {args.month} 暂无错题记录")
        return
    
    # 生成报告
    report = generate_monthly_report(args.student, args.month, mistakes)
    
    # 输出
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = out_names.default_monthly_report_path(
            args.student, args.month, args.subject
        )
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding='utf-8')
    print(f"✅ 月度报告已保存：{output_path}")
    out_names.print_output_path(output_path)


if __name__ == '__main__':
    main()
