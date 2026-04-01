#!/usr/bin/env python3
"""
复习状态更新工具

用法:
    # 用户查询后调用
    python3 update-review-state.py --student <学生名> --action query
    
    # 用户完成复习后调用
    python3 update-review-state.py --student <学生名> --action complete --subjects physics math

功能:
    - 更新复习状态记录
    - 支持查询、完成等操作
    - 供智能提醒脚本使用
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime


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


def update_query_state(student: str, state: dict):
    """更新查询状态"""
    today = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now().strftime('%H:%M')
    
    state['last_query_date'] = today
    state['last_query_time'] = now
    
    print(f"✅ 已更新查询状态")
    print(f"   日期：{today}")
    print(f"   时间：{now}")


def update_complete_state(student: str, state: dict, subjects: list):
    """更新完成状态"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 添加已完成科目
    completed = state.get('completed_subjects', [])
    for subj in subjects:
        if subj not in completed:
            completed.append(subj)
            print(f"✅ 标记完成：{subj}")
    
    state['completed_subjects'] = completed
    state['last_review_date'] = today
    
    # 更新待复习科目
    all_subjects = state.get('pending_subjects', [])
    state['pending_subjects'] = [s for s in all_subjects if s not in subjects]
    
    print(f"\n📊 当前状态:")
    print(f"   已完成科目：{completed}")
    print(f"   待复习科目：{state['pending_subjects']}")
    
    # 检查是否全部完成
    if not state['pending_subjects']:
        print(f"\n🎉 恭喜！今日复习已全部完成！")


def reset_daily_state(student: str, state: dict):
    """重置每日状态（新的一天）"""
    today = datetime.now().strftime('%Y-%m-%d')
    last_date = state.get('last_review_date')
    
    if last_date != today:
        # 新的一天，清空已完成科目
        state['completed_subjects'] = []
        state['pending_subjects'] = []  # 重新计算
        print(f"✅ 已重置每日状态（{today}）")
    else:
        print(f"ℹ️  仍是同一天（{today}），不清空状态")


def show_state(student: str, state: dict):
    """显示当前状态"""
    print(f"\n📊 复习状态（{student}）")
    print("=" * 40)
    print(f"上次查询：{state.get('last_query_date', '无')} {state.get('last_query_time', '')}")
    print(f"上次复习：{state.get('last_review_date', '无')}")
    print(f"已完成科目：{state.get('completed_subjects', [])}")
    print(f"待复习科目：{state.get('pending_subjects', [])}")
    print("=" * 40)


def main():
    parser = argparse.ArgumentParser(description='复习状态更新')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--action', required=True, 
                       choices=['query', 'complete', 'reset', 'show'],
                       help='操作类型')
    parser.add_argument('--subjects', nargs='+', help='科目列表（complete 操作使用）')
    
    args = parser.parse_args()
    
    # 加载状态
    state = load_review_state(args.student)
    
    # 检查是否需要重置（新的一天）
    if args.action != 'reset':
        reset_daily_state(args.student, state)
        state = load_review_state(args.student)  # 重新加载
    
    # 执行操作
    if args.action == 'query':
        update_query_state(args.student, state)
    elif args.action == 'complete':
        if not args.subjects:
            print("❌ complete 操作需要 --subjects 参数")
            return
        update_complete_state(args.student, state, args.subjects)
    elif args.action == 'reset':
        reset_daily_state(args.student, state)
    elif args.action == 'show':
        show_state(args.student, state)
    
    # 保存状态
    save_review_state(args.student, state)


if __name__ == '__main__':
    main()
