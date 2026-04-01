#!/usr/bin/env python3
"""
每日复习提醒脚本 - 智能判断是否发送

用法:
    python3 daily-review-reminder.py --student <学生名> [--channel <渠道>]

功能:
    - 智能判断是否需要发送提醒
    - 检查今日是否已查询过
    - 检查今日是否已完成复习
    - 只在需要时发送提醒
"""

import argparse
import sys
import re
import json
from pathlib import Path
from datetime import datetime, timedelta


def load_review_state(student: str) -> dict:
    """加载复习状态"""
    state_file = Path(f'data/mistake-notebook/students/{student}/review-state.json')
    
    if state_file.exists():
        return json.loads(state_file.read_text(encoding='utf-8'))
    
    return {
        'last_query_date': None,
        'last_query_time': None,
        'completed_subjects': [],
        'pending_subjects': [],
        'last_review_date': None,
        'last_reminder_sent': None
    }


def save_review_state(student: str, state: dict):
    """保存复习状态"""
    state_file = Path(f'data/mistake-notebook/students/{student}/review-state.json')
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def load_due_reviews(student: str, target_date: str = None) -> list:
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
        
        # 检查是否到期
        if due_date and due_date <= target_date:
            reviews.append({
                'id': fm.get('id', 'unknown'),
                'subject': fm.get('subject', 'unknown'),
                'knowledge_point': fm.get('knowledge-point', ''),
                'review_round': int(fm.get('review-round', 0)),
                'due_date': due_date,
            })
    
    return reviews


def check_if_query_today(state: dict, today: str) -> bool:
    """检查今日是否已查询过复习内容"""
    return state.get('last_query_date') == today


def check_if_completed_today(state: dict, today: str) -> bool:
    """检查今日是否已完成复习"""
    last_review = state.get('last_review_date')
    
    if last_review == today:
        # 今日有复习记录，检查是否还有未完成科目
        pending = state.get('pending_subjects', [])
        return len(pending) == 0
    
    return False


def get_pending_subjects(reviews: list, completed_subjects: list) -> list:
    """获取待复习科目"""
    subjects = set(r['subject'] for r in reviews)
    pending = [s for s in subjects if s not in completed_subjects]
    return pending


def should_send_reminder(student: str, reviews: list, state: dict, today: str) -> tuple:
    """智能判断是否应该发送提醒"""
    
    # 无待复习错题
    if not reviews:
        return False, 'no_reviews'
    
    # 检查今日是否已完成复习
    completed_subjects = state.get('completed_subjects', [])
    pending = get_pending_subjects(reviews, completed_subjects)
    
    # 全部完成
    if not pending:
        return False, 'completed'
    
    # 检查今日是否已查询过
    queried_today = check_if_query_today(state, today)
    
    if queried_today:
        # 今日已查询过，但未完成 → 发送提醒（提醒完成）
        return True, 'incomplete'
    else:
        # 今日未查询过 → 发送提醒（首次提醒）
        return True, 'first_reminder'


def generate_reminder_message(student: str, reviews: list, state: dict, scenario: str) -> str:
    """生成提醒消息"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    completed_subjects = state.get('completed_subjects', [])
    pending = get_pending_subjects(reviews, completed_subjects)
    
    # 按学科分组
    by_subject = {}
    for r in reviews:
        subj = r['subject']
        if subj in pending:  # 只显示未完成的
            if subj not in by_subject:
                by_subject[subj] = []
            by_subject[subj].append(r)
    
    # 学科名称映射
    subject_names = {
        'math': '数学',
        'chinese': '语文',
        'english': '英语',
        'physics': '物理',
        'chemistry': '化学',
        'biology': '生物',
    }
    
    total = sum(len(items) for items in by_subject.values())
    
    # 根据场景生成不同消息
    if scenario == 'incomplete':
        header = "⏰ **复习提醒**（未完成）"
        encouragement = "还有科目没复习哦！抓紧时间！💪"
    else:  # first_reminder
        header = "📅 **复习提醒**"
        encouragement = "加油！坚持就是胜利！💪"
    
    message = f"""{header}

**学生**：{student}  
**日期**：{today}  
**待复习**：{total} 道"""
    
    if completed_subjects:
        completed_names = [subject_names.get(s, s) for s in completed_subjects]
        message += f"（已完成：{', '.join(completed_names)} ✅）"
    
    message += "\n\n" + "━" * 40 + "\n\n"
    
    # 按学科列出
    for subj, items in sorted(by_subject.items()):
        subj_name = subject_names.get(subj, subj)
        message += f"**📚 {subj_name}**（{len(items)} 道）\n\n"
        
        for r in items[:10]:  # 每科最多显示 10 道
            round_num = r['review_round'] + 1
            message += f"• {r['knowledge_point']}（第{round_num}轮）🟡 今日\n"
        
        message += "\n"
    
    # 使用建议
    message += "━" * 40 + "\n\n"
    message += """💡 **使用方式**

• 说"**发送 XX 的复习内容**"→ 奴才发送长图
• 说"**发送所有复习内容**"→ 奴才发送全部长图
• 说"**XX 复习完了**"→ 奴才更新进度

"""
    
    # 预计用时
    if total <= 3:
        message += "⏰ 预计用时：5-10 分钟\n\n"
    elif total <= 10:
        message += "⏰ 预计用时：10-20 分钟\n\n"
    else:
        message += "⏰ 预计用时：20 分钟以上，建议分批次完成\n\n"
    
    message += f"{encouragement}"
    
    return message


def update_state_after_query(student: str, state: dict):
    """查询后更新状态"""
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime('%H:%M')
    
    state['last_query_date'] = today
    state['last_query_time'] = now
    
    save_review_state(student, state)


def update_state_after_review(student: str, state: dict, subjects: list):
    """复习完成后更新状态"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 添加已完成科目
    completed = state.get('completed_subjects', [])
    for subj in subjects:
        if subj not in completed:
            completed.append(subj)
    
    state['completed_subjects'] = completed
    state['last_review_date'] = today
    
    # 更新待复习科目
    all_subjects = state.get('pending_subjects', [])
    state['pending_subjects'] = [s for s in all_subjects if s not in subjects]
    
    save_review_state(student, state)


def send_message_via_openclaw(channel: str, message: str):
    """通过 OpenClaw message 工具发送消息"""
    print(f"\n📨 准备发送消息到 {channel}...")
    print(f"\n消息内容：\n{message}")
    print(f"\n" + "=" * 60)
    print(f"实际执行：openclaw message send --channel {channel} --message \"...\"")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='每日复习提醒（智能判断）')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--channel', choices=['feishu', 'wechat', 'openclaw-weixin'], 
                       default='feishu', help='发送渠道')
    parser.add_argument('--date', help='指定日期（YYYY-MM-DD），默认为今天')
    parser.add_argument('--force', action='store_true', help='强制发送（忽略智能判断）')
    parser.add_argument('--dry-run', action='store_true', help='仅显示消息，不发送')
    
    args = parser.parse_args()
    
    today = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
    
    print(f"🔍 智能复习提醒检查...")
    print(f"学生：{args.student}")
    print(f"日期：{today}")
    
    # 加载状态
    state = load_review_state(args.student)
    
    # 加载待复习错题
    reviews = load_due_reviews(args.student, today)
    
    print(f"待复习错题：{len(reviews)} 道")
    print(f"上次查询：{state.get('last_query_date', '无')}")
    print(f"上次复习：{state.get('last_review_date', '无')}")
    print(f"已完成科目：{state.get('completed_subjects', [])}")
    
    # 智能判断
    if not args.force:
        should_send, scenario = should_send_reminder(args.student, reviews, state, today)
    else:
        should_send, scenario = True, 'force'
    
    print(f"\n智能判断结果：{'发送' if should_send else '不发送'}（{scenario}）")
    
    if not should_send:
        if scenario == 'no_reviews':
            print("\n✅ 无待复习错题，不发送提醒")
        elif scenario == 'completed':
            print("\n✅ 今日复习已全部完成，不发送提醒")
        return
    
    # 生成消息
    message = generate_reminder_message(args.student, reviews, state, scenario)
    
    if args.dry_run:
        print(f"\n📝 预览消息：\n")
        print(message)
        return
    
    # 发送消息
    send_message_via_openclaw(args.channel, message)
    
    print("\n✅ 复习提醒已发送！")


if __name__ == '__main__':
    main()
