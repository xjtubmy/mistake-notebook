"""
错题间隔复习（SRS）核心算法模块。

提供间隔复习调度、到期日计算、复习状态判断等功能。

## 核心功能

- `ReviewSchedule`: 复习间隔和掌握度乘数配置
- `calculate_next_due()`: 计算下次复习到期日
- `is_due_today()`: 判断是否到期
- `srs_complete()`: 判断是否完成全部复习

## 复习间隔

默认复习间隔：[1, 3, 7, 15, 30] 天

## 掌握度乘数

- low: 1.0（基础间隔）
- medium: 1.2（延长 20%）
- high: 1.5（延长 50%）
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional


def _default_intervals() -> list[int]:
    """默认复习间隔列表。"""
    return [1, 3, 7, 15, 30]


def _default_confidence_multipliers() -> dict[str, float]:
    """默认掌握度乘数字典。"""
    return {
        'low': 1.0,
        'medium': 1.2,
        'high': 1.5,
    }


@dataclass
class ReviewSchedule:
    """
    复习间隔调度配置。
    
    Attributes:
        intervals: 复习间隔列表（单位：天），默认 [1, 3, 7, 15, 30]
        confidence_multipliers: 掌握度乘数字典，默认 {'low': 1.0, 'medium': 1.2, 'high': 1.5}
    
    Example:
        >>> schedule = ReviewSchedule()
        >>> schedule.intervals
        [1, 3, 7, 15, 30]
        >>> schedule.confidence_multipliers['high']
        1.5
    """
    intervals: list[int] = field(default_factory=_default_intervals)
    confidence_multipliers: dict[str, float] = field(default_factory=_default_confidence_multipliers)


# 默认复习间隔（天）
DEFAULT_REVIEW_INTERVALS = [1, 3, 7, 15, 30]

# 完成状态标记
COMPLETED_DUE_MARKERS = frozenset({"completed", "done"})


def calculate_next_due(
    current_round: int,
    last_review: date,
    confidence: str = 'low',
    schedule: Optional[ReviewSchedule] = None
) -> date:
    """
    计算下次复习的到期日。
    
    根据当前复习轮次、上次复习日期和掌握度，计算下次复习的到期日。
    掌握度越高，复习间隔越长。
    
    Args:
        current_round: 当前复习轮次（0 表示第一轮）
        last_review: 上次复习日期（或创建日期用于第一轮）
        confidence: 掌握度级别，可选 'low', 'medium', 'high'
        schedule: 复习调度配置，使用默认配置如果为 None
    
    Returns:
        下次复习的到期日
    
    Example:
        >>> from datetime import date
        >>> today = date(2026, 4, 12)
        >>> calculate_next_due(0, today)  # 第一轮：1 天后
        datetime.date(2026, 4, 13)
        >>> calculate_next_due(1, today, 'high')  # 第二轮，高掌握度：3*1.5=4.5 天后
        datetime.date(2026, 4, 16)
    """
    if schedule is None:
        schedule = ReviewSchedule()
    
    # 如果已完成所有轮次，返回最大日期表示完成
    if current_round >= len(schedule.intervals):
        return date.max
    
    # 获取基础间隔和掌握度乘数
    base_interval = schedule.intervals[current_round]
    multiplier = schedule.confidence_multipliers.get(confidence, 1.0)
    
    # 计算调整后的间隔（向下取整）
    adjusted_interval = int(base_interval * multiplier)
    
    return last_review + timedelta(days=adjusted_interval)


def is_due_today(due_date: date, target_date: Optional[date] = None) -> bool:
    """
    判断是否已到期（在目标日期或之前）。
    
    用于「今日待复习」过滤：到期日小于等于目标日期的题目需要复习。
    
    Args:
        due_date: 到期日期
        target_date: 目标日期，默认为今天
    
    Returns:
        True 表示已到期（需要复习），False 表示未到期
    
    Example:
        >>> from datetime import date, timedelta
        >>> today = date.today()
        >>> is_due_today(today)
        True
        >>> is_due_today(today + timedelta(days=1))
        False
        >>> is_due_today(today - timedelta(days=1))
        True
    """
    if target_date is None:
        target_date = date.today()
    return due_date <= target_date


def srs_complete(fm: dict) -> bool:
    """
    判断是否已结束全部间隔复习。
    
    通过检查 frontmatter 中的 due-date 字段判断：
    - 'completed' 或 'done' 表示已完成
    - 其他值表示未完成
    
    Args:
        fm: frontmatter 字典，包含 'due-date' 字段
    
    Returns:
        True 表示已完成全部复习，False 表示未完成
    
    Example:
        >>> srs_complete({'due-date': 'completed'})
        True
        >>> srs_complete({'due-date': 'done'})
        True
        >>> srs_complete({'due-date': '2026-04-15'})
        False
        >>> srs_complete({})
        False
    """
    due = str(fm.get("due-date") or "").strip().lower()
    return due in COMPLETED_DUE_MARKERS


def parse_frontmatter(content: str) -> dict:
    """
    解析 Markdown 文件的 frontmatter。
    
    提取 YAML 格式的 frontmatter 内容为字典。
    
    Args:
        content: Markdown 文件内容
    
    Returns:
        frontmatter 字典
    
    Example:
        >>> content = "---\\ncreated: 2026-04-12\\ndue-date: 2026-04-13\\n---\\n# Title"
        >>> fm = parse_frontmatter(content)
        >>> fm['created']
        '2026-04-12'
    """
    fm = {}
    match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match:
        for line in match.group(1).strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                fm[key.strip()] = value.strip()
    return fm


def parse_created_date(val: Optional[str]) -> Optional[datetime]:
    """
    解析创建日期字符串为 datetime 对象。
    
    Args:
        val: 日期字符串（格式：YYYY-MM-DD）
    
    Returns:
        datetime 对象，解析失败返回 None
    
    Example:
        >>> parse_created_date('2026-04-12')
        datetime.datetime(2026, 4, 12, 0, 0)
        >>> parse_created_date('invalid')
        None
    """
    if not val:
        return None
    s = str(val).strip()
    if len(s) < 10:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except ValueError:
        return None


def first_round_due_str(fm: dict) -> Optional[str]:
    """
    计算第一轮复习的到期日字符串。
    
    第一轮（review-round 0）的到期日严格为 created 日期 + 1 天。
    
    Args:
        fm: frontmatter 字典，包含 'created' 字段
    
    Returns:
        到期日字符串（YYYY-MM-DD 格式），解析失败返回 None
    
    Example:
        >>> first_round_due_str({'created': '2026-04-12'})
        '2026-04-13'
    """
    dt = parse_created_date(fm.get("created"))
    if not dt:
        return None
    return (dt + timedelta(days=1)).strftime("%Y-%m-%d")


def effective_due_date_for_queue(fm: dict) -> str:
    """
    获取用于队列查询的有效到期日。
    
    对于第一轮复习（review-round 0），使用创建日期 +1 天；
    对于后续轮次，使用 frontmatter 中的 due-date 字段。
    
    Args:
        fm: frontmatter 字典
    
    Returns:
        有效到期日字符串（YYYY-MM-DD 格式）
    
    Example:
        >>> effective_due_date_for_queue({'review-round': '0', 'created': '2026-04-12'})
        '2026-04-13'
    """
    try:
        rr = int(fm.get("review-round", 0) or 0)
    except ValueError:
        rr = 0
    
    if rr == 0:
        canon = first_round_due_str(fm)
        if canon:
            return canon
    
    return (fm.get("due-date") or "").strip()


def is_effective_due_on_or_before(effective_due: str, target_date: str) -> bool:
    """
    判断是否在目标日或之前已到期（含超期）。
    
    用于「今日待复习」过滤：未到期的题目应为 False。
    
    Args:
        effective_due: 有效到期日字符串（YYYY-MM-DD 格式）
        target_date: 目标日期字符串（YYYY-MM-DD 格式）
    
    Returns:
        True 表示已到期，False 表示未到期
    
    Example:
        >>> is_effective_due_on_or_before('2026-04-12', '2026-04-12')
        True
        >>> is_effective_due_on_or_before('2026-04-11', '2026-04-12')
        True
        >>> is_effective_due_on_or_before('2026-04-13', '2026-04-12')
        False
    """
    d = (effective_due or "").strip()
    t = (target_date or "").strip()
    
    if len(d) < 10 or len(t) < 10:
        return False
    
    try:
        due = datetime.strptime(d[:10], "%Y-%m-%d").date()
        tgt = datetime.strptime(t[:10], "%Y-%m-%d").date()
    except ValueError:
        return False
    
    return due <= tgt


# 完成状态标记（用于 due_date_is_scheduled）
COMPLETED_DUE_MARKERS = frozenset({"completed", "done", "none"})


def due_date_is_scheduled(fm: dict) -> bool:
    """
    判断 frontmatter 中是否有有效的复习计划。
    
    用于「今日待复习」队列过滤：只有已安排复习计划的题目才应出现在队列中。
    第一轮复习（review-round 0）使用 created+1 作为到期日；
    后续轮次使用 due-date 字段；
    已完成（due-date 为 completed/done/none）的题目不视为有复习计划。
    
    Args:
        fm: frontmatter 字典，包含 review-round、created、due-date 等字段
    
    Returns:
        True 表示有复习计划，False 表示无计划或已完成
    
    Example:
        >>> due_date_is_scheduled({'review-round': '0', 'created': '2026-04-12'})
        True
        >>> due_date_is_scheduled({'review-round': '1', 'due-date': '2026-04-15'})
        True
        >>> due_date_is_scheduled({'due-date': 'completed'})
        False
        >>> due_date_is_scheduled({'due-date': 'done'})
        False
        >>> due_date_is_scheduled({})
        False
    """
    try:
        rr = int(fm.get("review-round", 0) or 0)
    except ValueError:
        rr = 0
    
    # 第一轮：检查是否有有效的 created 日期
    if rr == 0:
        dt = parse_created_date(fm.get("created"))
        if dt is not None:
            return True
        return False
    
    # 后续轮次：检查 due-date 是否有效
    raw = (fm.get("due-date") or "").strip()
    if not raw:
        return False
    
    # 检查是否已完成
    low = raw.lower()
    if low in COMPLETED_DUE_MARKERS:
        return False
    
    # 尝试解析为日期
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return False
    
    return True
