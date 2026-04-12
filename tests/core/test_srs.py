"""
SRS 算法模块单元测试。

测试覆盖：
- ReviewSchedule 数据类
- calculate_next_due() 复习日期计算
- is_due_today() 到期判断
- srs_complete() 完成状态判断
"""

from datetime import date, timedelta

import pytest

from scripts.core.srs import (
    ReviewSchedule,
    calculate_next_due,
    is_due_today,
    srs_complete,
    parse_frontmatter,
    first_round_due_str,
    effective_due_date_for_queue,
    is_effective_due_on_or_before,
)


class TestReviewSchedule:
    """ReviewSchedule 数据类测试。"""
    
    def test_default_values(self):
        """测试默认值初始化。"""
        schedule = ReviewSchedule()
        assert schedule.intervals == [1, 3, 7, 15, 30]
        assert schedule.confidence_multipliers == {
            'low': 1.0,
            'medium': 1.2,
            'high': 1.5,
        }
    
    def test_custom_values(self):
        """测试自定义值初始化。"""
        schedule = ReviewSchedule(
            intervals=[2, 5, 10],
            confidence_multipliers={'low': 0.8, 'high': 2.0}
        )
        assert schedule.intervals == [2, 5, 10]
        assert schedule.confidence_multipliers == {'low': 0.8, 'high': 2.0}
    
    def test_custom_intervals_only(self):
        """测试仅自定义间隔。"""
        schedule = ReviewSchedule(intervals=[5, 10, 20])
        assert schedule.intervals == [5, 10, 20]
        # confidence_multipliers 应使用默认值
        assert schedule.confidence_multipliers == {
            'low': 1.0,
            'medium': 1.2,
            'high': 1.5,
        }


class TestCalculateNextDue:
    """calculate_next_due 函数测试。"""
    
    def test_calculate_next_due_round0(self):
        """第一轮复习日期计算（基础间隔 1 天）。"""
        today = date(2026, 4, 12)
        next_due = calculate_next_due(0, today)
        assert next_due == today + timedelta(days=1)
    
    def test_calculate_next_due_round1(self):
        """第二轮复习日期计算（基础间隔 3 天）。"""
        today = date(2026, 4, 12)
        next_due = calculate_next_due(1, today)
        assert next_due == today + timedelta(days=3)
    
    def test_calculate_next_due_round2(self):
        """第三轮复习日期计算（基础间隔 7 天）。"""
        today = date(2026, 4, 12)
        next_due = calculate_next_due(2, today)
        assert next_due == today + timedelta(days=7)
    
    def test_calculate_next_due_with_confidence_low(self):
        """低掌握度影响（乘数 1.0，无变化）。"""
        today = date(2026, 4, 12)
        next_due = calculate_next_due(1, today, confidence='low')
        # 3 * 1.0 = 3 天
        assert next_due == today + timedelta(days=3)
    
    def test_calculate_next_due_with_confidence_medium(self):
        """中等掌握度影响（乘数 1.2，延长 20%）。"""
        today = date(2026, 4, 12)
        next_due = calculate_next_due(1, today, confidence='medium')
        # 3 * 1.2 = 3.6 -> 3 天（向下取整）
        assert next_due == today + timedelta(days=3)
    
    def test_calculate_next_due_with_confidence_high(self):
        """高掌握度影响（乘数 1.5，延长 50%）。"""
        today = date(2026, 4, 12)
        next_due = calculate_next_due(1, today, confidence='high')
        # 3 * 1.5 = 4.5 -> 4 天（向下取整）
        assert next_due == today + timedelta(days=4)
    
    def test_calculate_next_due_high_confidence_round2(self):
        """高掌握度在第三轮的影响。"""
        today = date(2026, 4, 12)
        next_due = calculate_next_due(2, today, confidence='high')
        # 7 * 1.5 = 10.5 -> 10 天（向下取整）
        assert next_due == today + timedelta(days=10)
    
    def test_calculate_next_due_completed(self):
        """超过最大轮次返回 date.max 表示完成。"""
        today = date(2026, 4, 12)
        # 默认只有 5 轮（索引 0-4），第 5 轮及以后应返回 date.max
        next_due = calculate_next_due(5, today)
        assert next_due == date.max
    
    def test_calculate_next_due_custom_schedule(self):
        """自定义复习间隔配置。"""
        today = date(2026, 4, 12)
        custom_schedule = ReviewSchedule(intervals=[2, 4, 8, 16, 32])
        next_due = calculate_next_due(0, today, schedule=custom_schedule)
        assert next_due == today + timedelta(days=2)
        
        next_due = calculate_next_due(2, today, schedule=custom_schedule)
        assert next_due == today + timedelta(days=8)


class TestIsDueToday:
    """is_due_today 函数测试。"""
    
    def test_is_due_today_true(self):
        """到期判断：今天到期应返回 True。"""
        today = date(2026, 4, 12)
        assert is_due_today(today, today) is True
    
    def test_is_due_today_false(self):
        """未到期判断：明天到期应返回 False。"""
        today = date(2026, 4, 12)
        tomorrow = today + timedelta(days=1)
        assert is_due_today(tomorrow, today) is False
    
    def test_is_due_today_overdue(self):
        """超期判断：昨天到期应返回 True。"""
        today = date(2026, 4, 12)
        yesterday = today - timedelta(days=1)
        assert is_due_today(yesterday, today) is True
    
    def test_is_due_today_default_target(self):
        """默认使用今天作为目标日期。"""
        # 这个测试依赖于实际运行日期，所以只验证函数能正常调用
        today = date.today()
        result = is_due_today(today)
        assert result is True


class TestSrsComplete:
    """srs_complete 函数测试。"""
    
    def test_srs_complete_completed_marker(self):
        """完成标记：'completed' 应返回 True。"""
        assert srs_complete({'due-date': 'completed'}) is True
    
    def test_srs_complete_done_marker(self):
        """完成标记：'done' 应返回 True。"""
        assert srs_complete({'due-date': 'done'}) is True
    
    def test_srs_complete_case_insensitive(self):
        """完成标记：大小写不敏感。"""
        assert srs_complete({'due-date': 'COMPLETED'}) is True
        assert srs_complete({'due-date': 'Done'}) is True
    
    def test_srs_complete_not_complete(self):
        """未完成：具体日期应返回 False。"""
        assert srs_complete({'due-date': '2026-04-15'}) is False
    
    def test_srs_complete_empty_dict(self):
        """空字典应返回 False。"""
        assert srs_complete({}) is False
    
    def test_srs_complete_whitespace(self):
        """带空格的完成标记应返回 True。"""
        assert srs_complete({'due-date': '  completed  '}) is True


class TestParseFrontmatter:
    """parse_frontmatter 函数测试。"""
    
    def test_parse_simple_frontmatter(self):
        """解析简单 frontmatter。"""
        content = """---
created: 2026-04-12
due-date: 2026-04-13
---
# Title"""
        fm = parse_frontmatter(content)
        assert fm['created'] == '2026-04-12'
        assert fm['due-date'] == '2026-04-13'
    
    def test_parse_empty_frontmatter(self):
        """解析空 frontmatter。"""
        content = """---
---
# Title"""
        fm = parse_frontmatter(content)
        assert fm == {}
    
    def test_parse_no_frontmatter(self):
        """无 frontmatter 返回空字典。"""
        content = "# Title\nSome content"
        fm = parse_frontmatter(content)
        assert fm == {}


class TestFirstRoundDueStr:
    """first_round_due_str 函数测试。"""
    
    def test_first_round_due_calculation(self):
        """第一轮到期日计算：created + 1 天。"""
        fm = {'created': '2026-04-12'}
        assert first_round_due_str(fm) == '2026-04-13'
    
    def test_first_round_due_missing_created(self):
        """缺少 created 字段返回 None。"""
        assert first_round_due_str({}) is None
        assert first_round_due_str({'due-date': '2026-04-13'}) is None
    
    def test_first_round_due_invalid_date(self):
        """无效日期返回 None。"""
        assert first_round_due_str({'created': 'invalid'}) is None


class TestEffectiveDueDateForQueue:
    """effective_due_date_for_queue 函数测试。"""
    
    def test_effective_due_round0(self):
        """第一轮使用 created + 1 天。"""
        fm = {'review-round': '0', 'created': '2026-04-12'}
        assert effective_due_date_for_queue(fm) == '2026-04-13'
    
    def test_effective_due_round1(self):
        """后续轮次使用 due-date。"""
        fm = {'review-round': '1', 'due-date': '2026-04-15'}
        assert effective_due_date_for_queue(fm) == '2026-04-15'
    
    def test_effective_due_default_round0(self):
        """默认 review-round 为 0。"""
        fm = {'created': '2026-04-12'}
        assert effective_due_date_for_queue(fm) == '2026-04-13'


class TestIsEffectiveDueOnOrBefore:
    """is_effective_due_on_or_before 函数测试。"""
    
    def test_due_on_target_date(self):
        """到期日等于目标日应返回 True。"""
        assert is_effective_due_on_or_before('2026-04-12', '2026-04-12') is True
    
    def test_due_before_target_date(self):
        """到期日早于目标日应返回 True（超期）。"""
        assert is_effective_due_on_or_before('2026-04-11', '2026-04-12') is True
    
    def test_due_after_target_date(self):
        """到期日晚于目标日应返回 False（未到期）。"""
        assert is_effective_due_on_or_before('2026-04-13', '2026-04-12') is False
    
    def test_invalid_date_format(self):
        """无效日期格式返回 False。"""
        assert is_effective_due_on_or_before('invalid', '2026-04-12') is False
        assert is_effective_due_on_or_before('2026-04-12', 'invalid') is False
    
    def test_empty_strings(self):
        """空字符串返回 False。"""
        assert is_effective_due_on_or_before('', '') is False
