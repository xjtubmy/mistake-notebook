"""
各脚本默认输出文件名约定（中文日期 + 学科/类型），供 export / 报告类脚本复用。

复习导出（exports/）：
  {年}年{月}月{日}日-{数学|物理|…|全科}[-单元…].pdf|md

综合分析报告（reports/）：
  {年}月{日}日-{学科|全科}-错题分析报告.md

月度总结（reports/）：
  {年}年{月}月-{学科|全科}-错题分析报告.md
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# frontmatter 中学科常为英文码
SUBJECT_ZH = {
    "physics": "物理",
    "math": "数学",
    "mathematics": "数学",
    "chinese": "语文",
    "english": "英语",
    "chemistry": "化学",
    "biology": "生物",
    "history": "历史",
    "geography": "地理",
    "politics": "政治",
    "morality": "道法",
    "science": "科学",
    "it": "信息技术",
    "pe": "体育",
    "art": "美术",
    "music": "音乐",
}


def slug_segment(s: Optional[str]) -> str:
    if not s:
        return ""
    t = str(s).strip()
    t = re.sub(r'[\s/\\:*?"<>|]+', "-", t)
    t = re.sub(r"-+", "-", t).strip("-")
    return t[:100] if t else ""


def subject_label_for_filename(subject: str) -> str:
    """有学科时返回中文或清理后的标签（不用于表示「全科」）。"""
    s = str(subject).strip()
    if not s:
        return "学科"
    z = SUBJECT_ZH.get(s.lower())
    if z:
        return z
    return slug_segment(s) or "学科"


def chinese_ymd(dt: Optional[datetime] = None) -> str:
    d = dt or datetime.now()
    return f"{d.year}年{d.month}月{d.day}日"


def chinese_year_month(year_month: str) -> str:
    """YYYY-MM -> 2026年3月"""
    parts = year_month.strip().split("-")
    if len(parts) >= 2:
        try:
            y, m = int(parts[0]), int(parts[1])
            return f"{y}年{m}月"
        except ValueError:
            pass
    return year_month


def default_review_export_path(
    student: str,
    subject: Optional[str],
    unit: Optional[str],
    fmt: str,
    ref_date: Optional[datetime] = None,
) -> Path:
    """今日（或指定日）复习导出：日期+学科/全科。"""
    d = ref_date or datetime.now()
    base = Path(f"data/mistake-notebook/students/{student}/exports")
    ext = "pdf" if fmt == "pdf" else "md"
    parts = [chinese_ymd(d)]
    if subject and str(subject).strip():
        parts.append(subject_label_for_filename(subject))
    else:
        parts.append("全科")
    if unit and str(unit).strip():
        u = slug_segment(unit) or str(unit).strip() or "未知"
        parts.append(f"单元{u}")
    stem = "-".join(parts)
    return base / f"{stem}.{ext}"


def default_analysis_report_path(student: str, subject: Optional[str]) -> Path:
    """综合分析：日期+学科+错题分析报告。"""
    base = Path(f"data/mistake-notebook/students/{student}/reports")
    sub = subject_label_for_filename(subject) if (subject and str(subject).strip()) else "全科"
    stem = f"{chinese_ymd()}-{sub}-错题分析报告"
    return base / f"{stem}.md"


def default_monthly_report_path(
    student: str, year_month: str, subject: Optional[str]
) -> Path:
    """月度：N年N月+学科+错题分析报告。"""
    base = Path(f"data/mistake-notebook/students/{student}/reports")
    ym = chinese_year_month(year_month)
    sub = subject_label_for_filename(subject) if (subject and str(subject).strip()) else "全科"
    stem = f"{ym}-{sub}-错题分析报告"
    return base / f"{stem}.md"


def default_weak_points_path(student: str, top: int) -> Path:
    base = Path(f"data/mistake-notebook/students/{student}/reports")
    return base / f"{chinese_ymd()}-薄弱知识点TOP{top}.md"


def default_parent_brief_path(student: str) -> Path:
    base = Path(f"data/mistake-notebook/students/{student}/reports")
    return base / f"{chinese_ymd()}-家长简报.md"


def default_search_results_path(student: str) -> Path:
    """同日多次检索用时分区分。"""
    base = Path(f"data/mistake-notebook/students/{student}/search")
    hm = datetime.now().strftime("%H%M")
    return base / f"{chinese_ymd()}-{hm}-检索结果.md"


def default_practice_path(student: str, knowledge: str) -> Path:
    base = Path(f"data/mistake-notebook/students/{student}/practice")
    kp = slug_segment(knowledge) or "练习"
    return base / f"{chinese_ymd()}-{kp}-举一反三.md"


def print_output_path(path: Path) -> None:
    resolved = str(path.resolve())
    print(f"OUTPUT_PATH={resolved}")
