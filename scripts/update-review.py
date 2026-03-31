#!/usr/bin/env python3
"""
复习进度更新脚本（支持单题和批量更新）

用法:
    # 单题更新
    python3 update-review.py --student 曲凌松 --id 20260331-001 --round 1 --mastered good
    
    # 批量更新 - 一键完成今日所有复习
    python3 update-review.py --student 曲凌松 --today --mastered good
    
    # 批量更新 - 按学科
    python3 update-review.py --student 曲凌松 --today --subject physics --mastered good
    
    # 交互式更新
    python3 update-review.py --student 曲凌松 --interactive
"""

import argparse
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


# 艾宾浩斯复习间隔（天）
REVIEW_INTERVALS = [1, 3, 7, 15, 30]


def find_mistake_file(student: str, mistake_id: str) -> Path:
    """查找错题文件"""
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    for mistake_file in base_path.rglob('mistake.md'):
        content = mistake_file.read_text(encoding='utf-8')
        if f'id: {mistake_id}' in content:
            return mistake_file
    
    return None


def load_due_reviews(student: str, target_date: str = None, subject: str = None) -> list:
    """加载今日到期的错题"""
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    reviews = []
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return reviews
    
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
        
        # 跳过已掌握的
        if fm.get('mastered') == 'true':
            continue
        
        due_date = fm.get('due-date', '')
        
        # 学科筛选
        if subject and fm.get('subject') != subject:
            continue
        
        # 检查是否到期
        if due_date and due_date <= target_date:
            try:
                due = datetime.strptime(due_date, '%Y-%m-%d')
                today = datetime.strptime(target_date, '%Y-%m-%d')
                days_overdue = (today - due).days
            except:
                days_overdue = 0
            
            reviews.append({
                'id': fm.get('id', 'unknown'),
                'subject': fm.get('subject', 'unknown'),
                'knowledge_point': fm.get('knowledge-point', ''),
                'unit': fm.get('unit-name', ''),
                'review_round': int(fm.get('review-round', 0)),
                'due_date': due_date,
                'days_overdue': days_overdue,
                'path': mistake_file,
            })
    
    reviews.sort(key=lambda x: (x['subject'], x['review_round'], -x['days_overdue']))
    return reviews


def update_mistake_file(mistake_file: Path, review_round: int, mastered: str = None) -> tuple:
    """更新错题文件"""
    content = mistake_file.read_text(encoding='utf-8')
    
    if review_round < len(REVIEW_INTERVALS):
        next_interval = REVIEW_INTERVALS[review_round]
        next_review = datetime.now() + timedelta(days=next_interval)
        next_review_str = next_review.strftime('%Y-%m-%d')
    else:
        next_review_str = 'completed'
    
    content = re.sub(r'review-round: \d+', f'review-round: {review_round}', content)
    content = re.sub(r'due-date: \S+', f'due-date: {next_review_str}', content)
    
    if mastered:
        mastered_value = 'true' if mastered in ['good', 'excellent', '5', '4'] else 'false'
        content = re.sub(r'mastered: (true|false)', f'mastered: {mastered_value}', content)
    
    mistake_file.write_text(content, encoding='utf-8')
    return True, next_review_str


def batch_update(reviews: list, review_round: int, mastered: str = None) -> dict:
    """批量更新"""
    stats = defaultdict(int)
    for r in reviews:
        stats[r['subject']] += 1
        update_mistake_file(r['path'], review_round, mastered)
    return stats


def print_summary(stats: dict, review_round: int, mastered: str):
    """打印汇总"""
    total = sum(stats.values())
    print("\n" + "=" * 60)
    print("✅ 复习更新完成！")
    print("=" * 60)
    print(f"更新错题数：{total} 道")
    for subj, count in sorted(stats.items()):
        print(f"  • {subj}: {count} 道")
    if review_round < len(REVIEW_INTERVALS):
        print(f"\n下次复习日期：{(datetime.now() + timedelta(days=REVIEW_INTERVALS[review_round])).strftime('%Y-%m-%d')}")
    else:
        print(f"\n🎉 已完成全部 5 轮复习，永久掌握！")
    print(f"掌握情况：{mastered}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='复习进度更新')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--id', help='错题 ID（单题更新时使用）')
    parser.add_argument('--round', type=int, default=1, help='复习轮次（0-5）')
    parser.add_argument('--mastered', choices=['poor', 'fair', 'good', 'excellent'],
                       default='good', help='掌握情况')
    parser.add_argument('--today', action='store_true', help='更新今日到期的错题')
    parser.add_argument('--subject', help='按学科筛选')
    parser.add_argument('--interactive', action='store_true', help='交互式更新')
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    
    args = parser.parse_args()
    
    # 单题更新模式
    if args.id:
        print(f"🔍 正在查找错题 {args.id}...")
        mistake_file = find_mistake_file(args.student, args.id)
        
        if not mistake_file:
            print(f"❌ 未找到错题 {args.id}")
            return
        
        print(f"✅ 找到错题：{mistake_file}")
        
        if not args.dry_run:
            success, next_review = update_mistake_file(mistake_file, args.round, args.mastered)
            if success:
                print(f"\n✅ 复习进度已更新！")
                print(f"   下次复习日期：{next_review}")
        else:
            print(f"\n🚫 预览模式：将更新为第{args.round}轮，掌握情况：{args.mastered}")
        return
    
    # 批量更新模式
    if args.today:
        target_date = datetime.now().strftime('%Y-%m-%d')
        print(f"🔍 正在加载 {args.student} 的待复习错题...")
        
        reviews = load_due_reviews(args.student, target_date, args.subject)
        
        if not reviews:
            print("✅ 太棒了！没有待复习的错题！")
            return
        
        print(f"找到 {len(reviews)} 道待复习的错题\n")
        
        # 显示预览
        by_subject = defaultdict(list)
        for r in reviews:
            by_subject[r['subject']].append(r)
        
        print("=" * 60)
        print("待更新错题列表：")
        print("=" * 60)
        
        for subj, items in sorted(by_subject.items()):
            print(f"\n📚 {subj.upper()}（{len(items)} 道）")
            for r in items:
                urgency = f"🔴 逾期{r['days_overdue']}天" if r['days_overdue'] > 0 else "🟡 今日"
                print(f"  • {r['id']} - {r['knowledge_point']} (第{r['review_round']+1}轮) {urgency}")
        
        print("\n" + "=" * 60)
        print(f"更新参数:")
        print(f"  复习轮次：{args.round}")
        print(f"  掌握情况：{args.mastered}")
        if args.round < len(REVIEW_INTERVALS):
            print(f"  下次复习：{(datetime.now() + timedelta(days=REVIEW_INTERVALS[args.round])).strftime('%Y-%m-%d')}")
        print("=" * 60)
        
        if args.dry_run:
            print("\n🚫 预览模式，未实际更新")
            return
        
        # 执行批量更新
        stats = batch_update(reviews, args.round, args.mastered)
        print_summary(stats, args.round, args.mastered)
        return
    
    print("❌ 请指定更新方式：")
    print("  单题更新：--id <错题 ID> --round <轮次>")
    print("  批量更新：--today --mastered good")
    print("\n使用示例：")
    print("  # 单题更新")
    print("  python3 update-review.py --student 曲凌松 --id 20260331-001 --round 1 --mastered good")
    print()
    print("  # 批量更新（一键完成今日所有复习）")
    print("  python3 update-review.py --student 曲凌松 --today --mastered good")
    print()
    print("  # 按学科批量更新")
    print("  python3 update-review.py --student 曲凌松 --today --subject physics --mastered good")


if __name__ == '__main__':
    main()
