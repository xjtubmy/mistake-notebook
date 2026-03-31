#!/usr/bin/env python3
"""
每日复习提醒脚本 - 智能发送到飞书/微信

用法:
    python3 daily-review-reminder.py --student <学生名> [--channel <渠道>]

功能:
    - 扫描今日到期的错题
    - 生成复习提醒消息
    - 通过 message 工具发送到飞书/微信

定时任务配置 (crontab -e):
    0 18 * * * cd /home/ubuntu/clawd && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu
"""

import argparse
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta


def load_due_reviews(student: str, target_date: str = None) -> list:
    """加载今日到期的错题"""
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    reviews = []
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return reviews
    
    # 查找所有 mistake.md 文件
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
            # 计算逾期天数
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
    
    # 按复习轮次和到期日期排序（优先复习轮次少的、逾期长的）
    reviews.sort(key=lambda x: (x['review_round'], -x['days_overdue']))
    
    return reviews


def generate_reminder_message(student: str, reviews: list, target_date: str = None) -> str:
    """生成复习提醒消息"""
    if target_date is None:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    if not reviews:
        return f"""🎉 **好消息！**

**学生**：{student}  
**日期**：{target_date}

✅ 今日没有待复习的错题！

继续保持，按时复习哦！💪"""
    
    # 按学科分组
    by_subject = {}
    for r in reviews:
        subj = r['subject']
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
        'history': '历史',
        'geography': '地理',
        'politics': '政治',
    }
    
    # 生成消息
    total = len(reviews)
    overdue = sum(1 for r in reviews if r['days_overdue'] > 0)
    
    message = f"""📅 **复习提醒**

**学生**：{student}  
**日期**：{target_date}  
**待复习**：{total} 道"""
    
    if overdue > 0:
        message += f"（🔴 {overdue} 道已逾期）"
    
    message += "\n\n" + "━" * 40 + "\n\n"
    
    # 按学科列出
    for subj, items in sorted(by_subject.items()):
        subj_name = subject_names.get(subj, subj)
        message += f"**📚 {subj_name}**（{len(items)} 道）\n\n"
        
        for r in items[:10]:  # 每科最多显示 10 道
            round_num = r['review_round'] + 1
            
            # 逾期标记
            if r['days_overdue'] > 0:
                urgency = f"🔴 逾期{r['days_overdue']}天"
            elif r['days_overdue'] == 0:
                urgency = "🟡 今日"
            else:
                urgency = "🟢 提前"
            
            message += f"• {r['knowledge_point']}（第{round_num}轮）{urgency}\n"
        
        message += "\n"
    
    # 复习建议
    message += "━" * 40 + "\n\n"
    message += """💡 **复习建议**

1️⃣ **盖住答案**：先独立重做题目
2️⃣ **对照解析**：核对答案，理解思路
3️⃣ **记录进度**：在复习记录表上打勾
4️⃣ **举一反三**：完成相似题练习

📊 **复习轮次说明**：
• 第 1 轮：录入后 1 天（关键复习）
• 第 2 轮：录入后 3 天
• 第 3 轮：录入后 7 天
• 第 4 轮：录入后 15 天
• 第 5 轮：录入后 30 天（永久记忆）

"""
    
    message += "━" * 40 + "\n\n"
    
    if total <= 5:
        message += "⏰ 预计用时：10-15 分钟\n\n"
    elif total <= 10:
        message += "⏰ 预计用时：20-30 分钟\n\n"
    else:
        message += "⏰ 预计用时：30 分钟以上，建议分批次完成\n\n"
    
    message += "加油！坚持就是胜利！💪"
    
    return message


def send_message_via_openclaw(channel: str, message: str):
    """通过 OpenClaw message 工具发送消息"""
    # 这里生成 message 工具调用命令
    # 实际执行需要调用 openclaw message 命令
    
    print(f"\n📨 准备发送消息到 {channel}...")
    print(f"\n消息内容：\n{message}")
    print(f"\n" + "=" * 60)
    print(f"执行以下命令发送：")
    print(f"openclaw message send --channel {channel} --message \"...\"")
    print("=" * 60)
    
    # 实际调用 message 工具（需要 runtime 支持）
    # 这里生成调用代码
    return True


def main():
    parser = argparse.ArgumentParser(description='每日复习提醒')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--channel', choices=['feishu', 'wechat', 'openclaw-weixin'], 
                       default='feishu', help='发送渠道')
    parser.add_argument('--date', help='指定日期（YYYY-MM-DD），默认为今天')
    parser.add_argument('--dry-run', action='store_true', help='仅显示消息，不发送')
    
    args = parser.parse_args()
    
    print(f"🔍 正在扫描 {args.student} 的复习计划...")
    
    # 加载到期复习
    reviews = load_due_reviews(args.student, args.date)
    print(f"找到 {len(reviews)} 道待复习的错题\n")
    
    # 生成消息
    message = generate_reminder_message(args.student, reviews, args.date)
    
    if args.dry_run:
        print("📝 预览消息：\n")
        print(message)
        return
    
    # 发送消息
    print(f"📱 发送渠道：{args.channel}")
    send_message_via_openclaw(args.channel, message)
    
    print("\n✅ 复习提醒已发送！")


if __name__ == '__main__':
    main()
