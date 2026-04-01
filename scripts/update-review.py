#!/usr/bin/env python3
"""
复习进度更新脚本（支持单题和批量更新）

待复习列表：到期日 <= 今天 且仍在 SRS 中；`review-round: 0` 时到期日严格为 `created + 1 天`（与文件里旧 due-date 无关，可用 `--fix-first-due` 写回）。
批量 `--today`：每道题 `review-round` 自增 1 并写回下一 `due-date`，不再使用固定 `--round`。完成全部轮次时 `due-date: completed`。

用法:
    # 单题更新
    python3 update-review.py --student 曲凌松 --id 20260331-001 --round 1
    
    # 批量更新 - 一键完成今日所有复习
    python3 update-review.py --student 曲凌松 --today
    
    # 批量更新 - 按学科
    python3 update-review.py --student 曲凌松 --today --subject physics
    
    # 交互式更新
    python3 update-review.py --student 曲凌松 --interactive

    # 把所有 review-round 0 的 due-date 校正为 created+1 天
    python3 update-review.py --student 曲凌松 --fix-first-due
"""

import argparse
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import mistake_srs as srs

REVIEW_INTERVALS = srs.REVIEW_INTERVALS


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
        fm = srs.parse_frontmatter(content)

        # 只有 SRS 结束（due-date 为 completed 等）才不再进入待复习列表。
        if not srs.due_date_is_scheduled(fm):
            continue

        due_date = srs.effective_due_date_for_queue(fm)
        
        # 学科筛选
        if subject and fm.get('subject') != subject:
            continue
        
        # 仅到期或已超期：有效到期日 <= 查询日；未到期的题目不列入今日复习
        if srs.is_effective_due_on_or_before(due_date, target_date):
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
                'review_round': int(fm.get('review-round', 0) or 0),
                'due_date': due_date,
                'days_overdue': days_overdue,
                'path': mistake_file,
            })
    
    reviews.sort(key=lambda x: (x['subject'], x['review_round'], -x['days_overdue']))
    return reviews


def fix_first_round_due_dates(student: str, dry_run: bool = False) -> int:
    """将 review-round 为 0 的错题的 due-date 写为 created+1 天（与队列规则一致）。"""
    changed = 0
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    if not base_path.exists():
        return 0
    for mistake_file in base_path.rglob('mistake.md'):
        content = mistake_file.read_text(encoding='utf-8')
        fm = srs.parse_frontmatter(content)
        try:
            rr = int(fm.get('review-round', 0) or 0)
        except ValueError:
            continue
        if rr != 0:
            continue
        canon = srs.first_round_due_str(fm)
        if not canon:
            continue
        current = (fm.get('due-date') or '').strip()
        if current == canon:
            continue
        changed += 1
        print(f"{'[dry-run] ' if dry_run else ''}{mistake_file}: due-date {current!r} -> {canon}")
        if dry_run:
            continue
        if re.search(r'^due-date:\s*', content, re.MULTILINE):
            newc = re.sub(r'^due-date:\s*.*$', f'due-date: {canon}', content, flags=re.MULTILINE)
        else:
            ins = re.search(r'^---\s*\n', content, re.MULTILINE)
            if not ins:
                continue
            pos = ins.end()
            newc = content[:pos] + f'due-date: {canon}\n' + content[pos:]
        mistake_file.write_text(newc, encoding='utf-8')
    return changed


def update_mistake_file(mistake_file: Path, review_round: int) -> tuple:
    """更新错题文件"""
    content = mistake_file.read_text(encoding='utf-8')
    fm = srs.parse_frontmatter(content)

    # 第一轮（写入后仍为 review-round 0）：到期日严格为 created + 1 天，不跟「今天」走。
    if review_round == 0:
        created_dt = srs.parse_created_date(fm.get('created'))
        if created_dt:
            next_review_str = (created_dt + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            next_review_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    elif review_round < len(REVIEW_INTERVALS):
        next_interval = REVIEW_INTERVALS[review_round]
        next_review = datetime.now() + timedelta(days=next_interval)
        next_review_str = next_review.strftime('%Y-%m-%d')
    else:
        next_review_str = 'completed'
    
    content = re.sub(r'review-round: \d+', f'review-round: {review_round}', content)
    content = re.sub(r'due-date: \S+', f'due-date: {next_review_str}', content)

    mistake_file.write_text(content, encoding='utf-8')
    return True, next_review_str


def batch_update(reviews: list) -> dict:
    """批量更新：每道题在自身 review-round 基础上 +1，并写回下一 due-date。"""
    stats = defaultdict(int)
    for r in reviews:
        stats[r['subject']] += 1
        new_round = int(r['review_round']) + 1
        update_mistake_file(r['path'], new_round)
    return stats


def print_summary(stats: dict):
    """打印汇总"""
    total = sum(stats.values())
    print("\n" + "=" * 60)
    print("✅ 复习更新完成！")
    print("=" * 60)
    print(f"更新错题数：{total} 道")
    for subj, count in sorted(stats.items()):
        print(f"  • {subj}: {count} 道")
    print("\n每道题已在原 review-round 基础上 +1，并按艾宾浩斯间隔写入新的 due-date。")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='复习进度更新')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--id', help='错题 ID（单题更新时使用）')
    parser.add_argument('--round', type=int, default=1, help='复习轮次（0-5）')
    parser.add_argument('--today', action='store_true', help='更新今日到期的错题')
    parser.add_argument('--subject', help='按学科筛选')
    parser.add_argument('--interactive', action='store_true', help='交互式更新')
    parser.add_argument('--dry-run', action='store_true', help='预览模式')
    parser.add_argument('--fix-first-due', action='store_true',
                        help='将 review-round 0 的 due-date 校正为 created+1 天')
    
    args = parser.parse_args()

    if args.fix_first_due:
        n = fix_first_round_due_dates(args.student, args.dry_run)
        print(f"\n共 {n} 个文件{'（dry-run 未写入）' if args.dry_run else '已更新'}")
        return
    
    # 单题更新模式
    if args.id:
        print(f"🔍 正在查找错题 {args.id}...")
        mistake_file = find_mistake_file(args.student, args.id)
        
        if not mistake_file:
            print(f"❌ 未找到错题 {args.id}")
            return
        
        print(f"✅ 找到错题：{mistake_file}")
        
        if not args.dry_run:
            success, next_review = update_mistake_file(mistake_file, args.round)
            if success:
                print(f"\n✅ 复习进度已更新！")
                print(f"   下次复习日期：{next_review}")
        else:
            print(f"\n🚫 预览模式：将更新为第{args.round}轮")
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
        print("更新参数:")
        print("  复习轮次：每道题在各自当前轮次上 +1（不再使用固定 --round）")
        print("=" * 60)
        
        if args.dry_run:
            print("\n🚫 预览模式，未实际更新")
            return
        
        # 执行批量更新
        stats = batch_update(reviews)
        print_summary(stats)
        return
    
    print("❌ 请指定更新方式：")
    print("  单题更新：--id <错题 ID> --round <轮次>")
    print("  批量更新：--today")
    print("  校正第一轮 due-date：--fix-first-due")
    print("\n使用示例：")
    print("  # 单题更新")
    print("  python3 update-review.py --student 曲凌松 --id 20260331-001 --round 1")
    print()
    print("  # 批量更新（一键完成今日所有复习）")
    print("  python3 update-review.py --student 曲凌松 --today")
    print()
    print("  # 按学科批量更新")
    print("  python3 update-review.py --student 曲凌松 --today --subject physics")
    print()
    print("  # 校正第一轮 due-date（与 created+1 对齐）")
    print("  python3 update-review.py --student 曲凌松 --fix-first-due")


if __name__ == '__main__':
    main()
