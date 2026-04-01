"""
错题间隔复习（SRS）共用逻辑：frontmatter 解析、第一轮 due-date、待复习队列用的到期日。

第一轮（review-round 0）的到期日严格为 created 日期 + 1 天，与文件里旧的 due-date 无关（队列侧用 canonical；可用 update-review --fix-first-due 写回文件）。

是否「练完 SRS」只看 `due-date` 为 `completed` / `done`，不再使用 `mastered` 字段（见 `srs_complete()`）。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

REVIEW_INTERVALS = [1, 3, 7, 15, 30]
COMPLETED_DUE_MARKERS = frozenset({"completed", "done", "none"})


def parse_frontmatter(content: str) -> dict:
    fm = {}
    match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match:
        for line in match.group(1).strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                fm[key.strip()] = value.strip()
    return fm


def parse_created_date(val) -> Optional[datetime]:
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
    dt = parse_created_date(fm.get("created"))
    if not dt:
        return None
    return (dt + timedelta(days=1)).strftime("%Y-%m-%d")


def due_date_is_scheduled(fm: dict) -> bool:
    try:
        rr = int(fm.get("review-round", 0) or 0)
    except ValueError:
        rr = 0
    if rr == 0 and first_round_due_str(fm):
        return True
    raw = (fm.get("due-date") or "").strip()
    if not raw:
        return False
    low = raw.lower()
    if low in COMPLETED_DUE_MARKERS:
        return False
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def srs_complete(fm: dict) -> bool:
    """是否已结束全部间隔复习（唯一完成信号，与 frontmatter 里是否曾有 mastered 无关）。"""
    due = str(fm.get("due-date") or "").strip().lower()
    return due in ("completed", "done")


def effective_due_date_for_queue(fm: dict) -> str:
    try:
        rr = int(fm.get("review-round", 0) or 0)
    except ValueError:
        rr = 0
    if rr == 0:
        canon = first_round_due_str(fm)
        if canon:
            return canon
    return (fm.get("due-date") or "").strip()
