#!/usr/bin/env python3
"""
复习提醒脚本 - 生成今日复习列表

用法:
    python3 review-reminder.py --student <学生名> [--today <日期>]

功能:
    - 扫描所有错题的 due-date 字段
    - 生成今日/本周复习列表
    - 输出 Markdown 格式
"""

import argparse
from pathlib import Path
from datetime import datetime, timedelta
import re


def parse_frontmatter(content: str) -> dict:
    """解析 YAML Frontmatter（简易版）"""
    data = {}
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        for line in match.group(1).strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # 处理布尔值
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                # 处理数字
                elif value.isdigit():
                    value = int(value)
                data[key] = value
    return data


def get_due_reviews(student: str, target_date: str = None) -> list:
    """获取待复习的错题"""
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    reviews = []
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return reviews
    
    # 查找所有 mistake.md 文件
    for mistake_file in base_path.rglob('mistake.md'):
        content = mistake_file.read_text(encoding='utf-8')
        frontmatter = parse_frontmatter(content)
        
        # 跳过已掌握的
        if frontmatter.get('mastered') == True:
            continue
        
        due_date = frontmatter.get('due-date', '')
        
        # 检查是否到期
        if due_date and due_date <= target_date:
            reviews.append({
                'id': frontmatter.get('id', 'unknown'),
                'subject': frontmatter.get('subject', 'unknown'),
                'grade': frontmatter.get('grade', ''),
                'semester': frontmatter.get('semester', ''),
                'unit': frontmatter.get('unit', ''),
                'unit_name': frontmatter.get('unit-name', ''),
                'knowledge_point': frontmatter.get('knowledge-point', ''),
                'error_type': frontmatter.get('error-type', ''),
                'review_round': frontmatter.get('review-round', 0),
                'due_date': due_date,
                'difficulty': frontmatter.get('difficulty', '⭐'),
                'path': mistake_file,
                'status': frontmatter.get('status', '待复习')
            })
    
    # 按复习轮次排序（优先复习轮次少的）
    reviews.sort(key=lambda x: (x['review_round'], x['due_date']))
    
    return reviews


def get_review_interval(round_num: int) -> int:
    """根据复习轮次获取间隔天数（艾宾浩斯）"""
    intervals = [1, 3, 7, 15, 30]  # 第 1-5 轮的间隔
    if round_num < len(intervals):
        return intervals[round_num]
    return 30  # 第 5 轮后每月复习一次


def generate_reminder(student: str, reviews: list, target_date: str = None) -> str:
    """生成复习提醒"""
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    today = datetime.strptime(target_date, '%Y-%m-%d')
    
    # 按学科分组
    by_subject = {}
    for r in reviews:
        subj = r['subject']
        if subj not in by_subject:
            by_subject[subj] = []
        by_subject[subj].append(r)
    
    reminder = f"""---
type: review-reminder
student: {student}
date: {target_date}
generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 📅 今日复习计划

**学生**：[[../profile|{student}]]  
**日期**：{target_date}  
**待复习**：{len(reviews)} 道

---

## ⏰ 紧急程度

| 优先级 | 数量 | 说明 |
|--------|------|------|
| 🔴 超期 | {sum(1 for r in reviews if r['due_date'] < target_date)} | 到期日期已过 |
| 🟡 今日 | {sum(1 for r in reviews if r['due_date'] == target_date)} | 今天到期 |
| 🟢 提前 | 0 | 提前复习 |

---

## 📚 按学科分组

"""
    
    for subj, items in sorted(by_subject.items()):
        reminder += f"""### {subj}（{len(items)} 道）

| 错题 ID | 知识点 | 单元 | 复习轮次 | 到期日期 | 链接 |
|--------|--------|------|---------|---------|------|
"""
        for r in items[:10]:  # 每科最多显示 10 道
            rel_path = r['path'].relative_to(Path(f'mistake-notebook/students/{student}'))
            round_num = int(r['review_round'])
            interval = get_review_interval(round_num)
            reminder += f"| {r['id']} | {r['knowledge_point']} | {r['unit_name']} | 第{round_num+1}轮 (+{interval}天) | {r['due_date']} | [[{rel_path}]] |\n"
        
        reminder += "\n"
    
    # 复习方法提示
    reminder += """---

## 💡 复习方法建议

### 三步复习法

1. **盖住答案**：先独立重做题目
2. **对照解析**：核对答案，理解思路
3. **举一反三**：完成相似题练习

### 掌握标准

- ✅ 能独立正确解答
- ✅ 能讲解解题思路
- ✅ 能识别类似题目

---

## 📝 复习记录模板

复制以下模板到每道错题的 analysis.md 中：

```markdown
## 📊 复习记录

| 轮次 | 日期 | 用时 | 掌握情况 | 签名 |
|------|------|------|---------|------|
| 第 X 轮 | """ + target_date + """ | | 😐 模糊 / 🙂 掌握 / 🤩 熟练 | |
```

---

## 🔗 快速链接

- [[../profile|返回学生主页]]
- [[./README|返回错题总览]]

---

**生成时间**：""" + datetime.now().strftime('%Y-%m-%d %H:%M') + """

> 💡 提示：完成复习后，记得更新错题的 `review-round` 和 `due-date` 字段
"""
    
    return reminder


def generate_weekly_plan(student: str, start_date: str = None) -> str:
    """生成本周复习计划"""
    if start_date is None:
        start_date = datetime.now().strftime('%Y-%m-%d')
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    # 找到本周的周一
    monday = start - timedelta(days=start.weekday())
    
    plan = f"""---
type: weekly-review-plan
student: {student}
week-start: {monday.strftime('%Y-%m-%d')}
generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 📅 本周复习计划

**学生**：[[../profile|{student}]]  
**周次**：{monday.strftime('%Y-W%W')}  
**周期**：{monday.strftime('%m/%d')} - {(monday + timedelta(days=6)).strftime('%m/%d')}

---

## 每日安排

"""
    
    for i in range(7):
        day = monday + timedelta(days=i)
        date_str = day.strftime('%Y-%m-%d')
        day_name = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i]
        
        reviews = get_due_reviews(student, date_str)
        
        plan += f"""### {day_name}（{date_str}）

"""
        if reviews:
            plan += f"**待复习**：{len(reviews)} 道\n\n"
            plan += "| 学科 | 知识点 | 复习轮次 | 链接 |\n"
            plan += "|------|--------|---------|------|\n"
            for r in reviews[:5]:  # 每天最多显示 5 道
                rel_path = r['path'].relative_to(Path(f'mistake-notebook/students/{student}'))
                plan += f"| {r['subject']} | {r['knowledge_point']} | 第{int(r['review_round'])+1}轮 | [[{rel_path}]] |\n"
        else:
            plan += "🎉 无复习任务\n"
        
        plan += "\n"
    
    plan += f"""---

**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    return plan


def main():
    parser = argparse.ArgumentParser(description='复习提醒生成')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--today', help='指定日期（YYYY-MM-DD），默认为今天')
    parser.add_argument('--weekly', action='store_true', help='生成本周计划')
    parser.add_argument('--output', help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    if args.weekly:
        print(f"正在生成 {args.student} 的本周复习计划...")
        content = generate_weekly_plan(args.student, args.today)
        default_output = f'mistake-notebook/students/{args.student}/weekly-plan.md'
    else:
        print(f"正在生成 {args.student} 的今日复习提醒...")
        reviews = get_due_reviews(args.student, args.today)
        print(f"找到 {len(reviews)} 道待复习的错题")
        content = generate_reminder(args.student, reviews, args.today)
        default_output = f'mistake-notebook/students/{args.student}/today-review.md'
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(content, encoding='utf-8')
        print(f"已保存：{args.output}")
    else:
        # 默认保存到 data 目录
        default_output = f'data/mistake-notebook/students/{args.student}/today-review.md'
        Path(default_output).parent.mkdir(parents=True, exist_ok=True)
        Path(default_output).write_text(content, encoding='utf-8')
        print(f"已保存：{default_output}")


if __name__ == '__main__':
    main()
