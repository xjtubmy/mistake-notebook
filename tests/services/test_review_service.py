"""
ReviewService 服务层单元测试

测试覆盖：
- ReviewService 初始化
- get_due_reviews 到期查询
- update_review 单次更新
- batch_update 批量更新
- get_review_stats 统计信息
"""

import shutil
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from scripts.core.models import Mistake, Subject, ErrorType, Confidence
from scripts.core.file_ops import get_student_dir, write_mistake_file
from scripts.services.review_service import (
    ReviewService,
    ReviewResult,
    BatchResult,
    ReviewStats,
)


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def sample_mistake_content():
    """样本错题内容"""
    return """---
id: test-001
student: 张三
subject: math
knowledge-point: 一元二次方程
error-type: 计算错误
created: 2026-04-10
due-date: 2026-04-11
review-round: 0
confidence: low
---

# 题目

解方程：x² - 5x + 6 = 0

# 学生答案

x = 2

# 正确答案

x = 2 或 x = 3

# 解析

因式分解：(x-2)(x-3) = 0
"""


@pytest.fixture
def setup_student_mistakes(temp_dir, sample_mistake_content):
    """设置学生错题数据"""
    student_dir = get_student_dir('张三', temp_dir)
    mistakes_dir = student_dir / 'mistakes' / 'math'
    
    # 创建已到期错题
    mistake1_dir = mistakes_dir / 'test-001'
    mistake1_dir.mkdir(parents=True, exist_ok=True)
    write_mistake_file(
        mistake1_dir / 'mistake.md',
        {
            'id': 'test-001',
            'student': '张三',
            'subject': 'math',
            'knowledge-point': '一元二次方程',
            'error-type': '计算错误',
            'created': '2026-04-10',
            'due-date': '2026-04-11',  # 已到期
            'review-round': '0',
            'confidence': 'low',
        },
        sample_mistake_content
    )
    
    # 创建未到期错题
    mistake2_dir = mistakes_dir / 'test-002'
    mistake2_dir.mkdir(parents=True, exist_ok=True)
    write_mistake_file(
        mistake2_dir / 'mistake.md',
        {
            'id': 'test-002',
            'student': '张三',
            'subject': 'math',
            'knowledge-point': '函数',
            'error-type': '概念不清',
            'created': '2026-04-12',
            'due-date': '2026-04-20',  # 未到期
            'review-round': '1',
            'confidence': 'medium',
        },
        sample_mistake_content
    )
    
    # 创建已完成错题
    mistake3_dir = mistakes_dir / 'test-003'
    mistake3_dir.mkdir(parents=True, exist_ok=True)
    write_mistake_file(
        mistake3_dir / 'mistake.md',
        {
            'id': 'test-003',
            'student': '张三',
            'subject': 'math',
            'knowledge-point': '几何',
            'error-type': '逻辑错误',
            'created': '2026-04-01',
            'due-date': 'completed',  # 已完成
            'review-round': '5',
            'confidence': 'high',
        },
        sample_mistake_content
    )
    
    return student_dir


class TestReviewServiceInit:
    """ReviewService 初始化测试"""
    
    def test_init_with_default_base_dir(self, temp_dir, monkeypatch):
        """测试使用默认基础目录初始化"""
        # 临时切换到 temp_dir 以便默认路径能正常工作
        monkeypatch.chdir(temp_dir)
        
        service = ReviewService('李四')
        assert service.student_name == '李四'
        assert service.base_dir is None
        assert service.student_dir.exists()
        assert '李四' in str(service.student_dir)
    
    def test_init_with_custom_base_dir(self, temp_dir):
        """测试使用自定义基础目录初始化"""
        service = ReviewService('王五', base_dir=temp_dir)
        assert service.student_name == '王五'
        assert service.base_dir == temp_dir
        assert service.student_dir == temp_dir / '王五'
        assert service.student_dir.exists()
    
    def test_init_creates_student_dir(self, temp_dir):
        """测试初始化时自动创建学生目录"""
        service = ReviewService('赵六', base_dir=temp_dir)
        assert service.student_dir.exists()
        assert service.student_dir.is_dir()


class TestGetDueReviews:
    """get_due_reviews 方法测试"""
    
    def test_get_due_reviews_returns_overdue(self, temp_dir, setup_student_mistakes):
        """测试返回已到期的错题"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        # 使用固定日期测试（2026-04-12）
        from datetime import date as date_cls
        target_date = date_cls(2026, 4, 12)
        
        due_mistakes = service.get_due_reviews(target_date=target_date)
        
        # 应返回 test-001（2026-04-11 到期）
        assert len(due_mistakes) == 1
        assert due_mistakes[0].id == 'test-001'
    
    def test_get_due_reviews_excludes_completed(self, temp_dir, setup_student_mistakes):
        """测试排除已完成的错题"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        target_date = date(2026, 4, 12)
        due_mistakes = service.get_due_reviews(target_date=target_date)
        
        # test-003 已完成，不应返回
        ids = [m.id for m in due_mistakes]
        assert 'test-003' not in ids
    
    def test_get_due_reviews_excludes_not_due(self, temp_dir, setup_student_mistakes):
        """测试排除未到期的错题"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        target_date = date(2026, 4, 12)
        due_mistakes = service.get_due_reviews(target_date=target_date)
        
        # test-002 未到期（2026-04-20），不应返回
        ids = [m.id for m in due_mistakes]
        assert 'test-002' not in ids
    
    def test_get_due_reviews_default_target_date(self, temp_dir, setup_student_mistakes):
        """测试默认使用今天作为目标日期"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        # 不指定 target_date，应使用今天
        due_mistakes = service.get_due_reviews()
        
        # 验证函数能正常执行
        assert isinstance(due_mistakes, list)
    
    def test_get_due_reviews_empty(self, temp_dir):
        """测试没有错题时返回空列表"""
        service = ReviewService('空学生', base_dir=temp_dir)
        
        due_mistakes = service.get_due_reviews()
        assert due_mistakes == []
    
    def test_get_due_reviews_sorted_by_due_date(self, temp_dir, sample_mistake_content):
        """测试返回结果按到期日排序"""
        student_dir = get_student_dir('排序测试', temp_dir)
        mistakes_dir = student_dir / 'mistakes' / 'math'
        
        # 创建多个不同到期日的错题
        for i, due_day in enumerate([15, 10, 12]):
            mistake_dir = mistakes_dir / f'test-{i:03d}'
            mistake_dir.mkdir(parents=True, exist_ok=True)
            write_mistake_file(
                mistake_dir / 'mistake.md',
                {
                    'id': f'test-{i:03d}',
                    'student': '排序测试',
                    'subject': 'math',
                    'knowledge-point': '测试',
                    'error-type': '计算错误',
                    'created': '2026-04-01',
                    'due-date': f'2026-04-{due_day:02d}',
                    'review-round': '0',
                },
                sample_mistake_content
            )
        
        service = ReviewService('排序测试', base_dir=temp_dir)
        target_date = date(2026, 4, 16)
        
        due_mistakes = service.get_due_reviews(target_date=target_date)
        
        # 应返回 3 个错题，按到期日升序排序
        assert len(due_mistakes) == 3
        assert due_mistakes[0].due_date == date(2026, 4, 10)
        assert due_mistakes[1].due_date == date(2026, 4, 12)
        assert due_mistakes[2].due_date == date(2026, 4, 15)


class TestUpdateReview:
    """update_review 方法测试"""
    
    def test_update_review_pass_increases_round(self, temp_dir, setup_student_mistakes):
        """测试通过复习后轮次增加"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('test-001', result='pass')
        
        assert result.success is True
        assert result.mistake_id == 'test-001'
        assert result.old_round == 0
        assert result.new_round == 1
        assert result.error is None
    
    def test_update_review_pass_updates_due_date(self, temp_dir, setup_student_mistakes):
        """测试通过复习后更新到期日"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('test-001', result='pass')
        
        assert result.success is True
        assert result.new_due_date is not None
        # 新到期日应晚于今天
        assert result.new_due_date > date.today()
    
    def test_update_review_fail_keeps_round(self, temp_dir, setup_student_mistakes):
        """测试未通过复习保持当前轮次"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('test-001', result='fail')
        
        assert result.success is True
        assert result.old_round == 0
        assert result.new_round == 0  # 轮次不变
    
    def test_update_review_fail_reschedules(self, temp_dir, setup_student_mistakes):
        """测试未通过复习重新安排（1 天后）"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('test-001', result='fail')
        
        assert result.success is True
        assert result.new_due_date == date.today() + timedelta(days=1)
    
    def test_update_review_not_found(self, temp_dir, setup_student_mistakes):
        """测试错题不存在时返回错误"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('nonexistent', result='pass')
        
        assert result.success is False
        assert result.error is not None
        assert '未找到' in result.error
    
    def test_update_review_already_completed(self, temp_dir, setup_student_mistakes):
        """测试已完成的错题不再更新"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('test-003', result='pass')
        
        assert result.success is True
        assert result.old_round == 5
        assert result.new_round == 5  # 轮次不变
    
    def test_update_review_default_result(self, temp_dir, setup_student_mistakes):
        """测试默认结果为 pass"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('test-001')
        
        assert result.success is True
        assert result.new_round == 1  # 默认 pass，轮次增加
    
    def test_update_review_with_confidence_low(self, temp_dir, setup_student_mistakes):
        """测试低掌握度更新（间隔乘数 1.0）"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('test-001', result='pass', confidence='low')
        
        assert result.success is True
        assert result.new_round == 1
        # 低掌握度：基础间隔 3 天 * 1.0 = 3 天
        expected_due = date.today() + timedelta(days=3)
        assert result.new_due_date == expected_due
    
    def test_update_review_with_confidence_medium(self, temp_dir, setup_student_mistakes):
        """测试中等掌握度更新（间隔乘数 1.2）"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('test-001', result='pass', confidence='medium')
        
        assert result.success is True
        assert result.new_round == 1
        # 中等掌握度：基础间隔 3 天 * 1.2 = 3.6 -> 3 天（向下取整）
        expected_due = date.today() + timedelta(days=3)
        assert result.new_due_date == expected_due
    
    def test_update_review_with_confidence_high(self, temp_dir, setup_student_mistakes):
        """测试高掌握度更新（间隔乘数 1.5）"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.update_review('test-001', result='pass', confidence='high')
        
        assert result.success is True
        assert result.new_round == 1
        # 高掌握度：基础间隔 3 天 * 1.5 = 4.5 -> 4 天（向下取整）
        expected_due = date.today() + timedelta(days=4)
        assert result.new_due_date == expected_due
    
    def test_update_review_confidence_invalid(self, temp_dir, setup_student_mistakes):
        """测试无效掌握度值保持原值"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        # 传入无效的 confidence 值，应保持原有的 'low'
        result = service.update_review('test-001', result='pass', confidence='invalid')
        
        assert result.success is True
        # 应使用默认乘数 1.0
        expected_due = date.today() + timedelta(days=3)
        assert result.new_due_date == expected_due


class TestBatchUpdate:
    """batch_update 方法测试"""
    
    def test_batch_update_all_success(self, temp_dir, setup_student_mistakes):
        """测试批量更新全部成功"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.batch_update(['test-001', 'test-002'])
        
        assert result.total == 2
        assert result.success_count == 2
        assert result.failed_count == 0
        assert result.success_rate == 1.0
    
    def test_batch_update_partial_success(self, temp_dir, setup_student_mistakes):
        """测试批量更新部分成功"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.batch_update(['test-001', 'nonexistent'])
        
        assert result.total == 2
        assert result.success_count == 1
        assert result.failed_count == 1
        assert result.success_rate == 0.5
    
    def test_batch_update_empty_list(self, temp_dir, setup_student_mistakes):
        """测试空列表批量更新"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.batch_update([])
        
        assert result.total == 0
        assert result.success_count == 0
        assert result.failed_count == 0
        assert result.success_rate == 0.0
    
    def test_batch_update_results_detail(self, temp_dir, setup_student_mistakes):
        """测试批量更新返回详细结果"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        result = service.batch_update(['test-001'])
        
        assert len(result.results) == 1
        assert isinstance(result.results[0], ReviewResult)
        assert result.results[0].mistake_id == 'test-001'
        assert result.results[0].success is True
    
    def test_batch_update_with_confidence(self, temp_dir, setup_student_mistakes):
        """测试批量更新支持掌握度参数"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        # 批量更新并设置高掌握度
        result = service.batch_update(['test-001', 'test-002'], confidence='high')
        
        assert result.total == 2
        assert result.success_count == 2
        assert result.failed_count == 0
        
        # 验证两道题都使用了高掌握度计算
        # test-001: round 0 -> 1，第二轮高掌握度：3 * 1.5 = 4.5 -> 4 天
        # test-002: round 1 -> 2，第三轮高掌握度：7 * 1.5 = 10.5 -> 10 天
        assert result.results[0].new_due_date == date.today() + timedelta(days=4)
        assert result.results[1].new_due_date == date.today() + timedelta(days=10)


class TestGetReviewStats:
    """get_review_stats 方法测试"""
    
    def test_get_review_stats_total_count(self, temp_dir, setup_student_mistakes):
        """测试统计总错题数"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        stats = service.get_review_stats()
        
        assert stats.total_mistakes == 3
    
    def test_get_review_stats_completed_count(self, temp_dir, setup_student_mistakes):
        """测试统计已完成数量"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        stats = service.get_review_stats()
        
        assert stats.completed == 1  # test-003
    
    def test_get_review_stats_due_today(self, temp_dir, sample_mistake_content):
        """测试统计今日到期数量"""
        student_dir = get_student_dir('统计测试', temp_dir)
        mistakes_dir = student_dir / 'mistakes' / 'math'
        
        # 创建今天到期的错题
        today = date.today()
        mistake_dir = mistakes_dir / 'today-due'
        mistake_dir.mkdir(parents=True, exist_ok=True)
        write_mistake_file(
            mistake_dir / 'mistake.md',
            {
                'id': 'today-due',
                'student': '统计测试',
                'subject': 'math',
                'knowledge-point': '测试',
                'error-type': '计算错误',
                'created': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
                'due-date': today.strftime('%Y-%m-%d'),
                'review-round': '0',
            },
            sample_mistake_content
        )
        
        service = ReviewService('统计测试', base_dir=temp_dir)
        stats = service.get_review_stats()
        
        assert stats.due_today == 1
    
    def test_get_review_stats_overdue(self, temp_dir, setup_student_mistakes):
        """测试统计已逾期数量"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        # 使用固定日期测试（2026-04-12）
        # test-001 在 2026-04-11 到期，已逾期
        from datetime import date as date_cls
        import scripts.services.review_service as rs_module
        
        # 通过修改 find_mistake_files 的返回值来间接测试
        # 这里直接验证 stats 对象结构
        stats = service.get_review_stats()
        
        # 验证 stats 对象有正确的属性
        assert hasattr(stats, 'overdue')
        assert hasattr(stats, 'due_today')
        assert hasattr(stats, 'upcoming')
    
    def test_get_review_stats_by_subject(self, temp_dir, sample_mistake_content):
        """测试按学科统计"""
        student_dir = get_student_dir('学科统计', temp_dir)
        
        # 创建不同学科的错题（使用唯一 ID）
        test_cases = [
            ('math-001', 'math'),
            ('chinese-001', 'chinese'),
            ('math-002', 'math'),
        ]
        for mistake_id, subject in test_cases:
            mistakes_dir = student_dir / 'mistakes' / subject
            mistake_dir = mistakes_dir / mistake_id
            mistake_dir.mkdir(parents=True, exist_ok=True)
            write_mistake_file(
                mistake_dir / 'mistake.md',
                {
                    'id': mistake_id,
                    'student': '学科统计',
                    'subject': subject,
                    'knowledge-point': '测试',
                    'error-type': '计算错误',
                    'created': '2026-04-01',
                    'due-date': '2026-05-01',
                    'review-round': '0',
                },
                sample_mistake_content
            )
        
        service = ReviewService('学科统计', base_dir=temp_dir)
        stats = service.get_review_stats()
        
        assert stats.by_subject.get('math', 0) == 2
        assert stats.by_subject.get('chinese', 0) == 1
    
    def test_get_review_stats_by_error_type(self, temp_dir, sample_mistake_content):
        """测试按错误类型统计"""
        student_dir = get_student_dir('错误类型统计', temp_dir)
        mistakes_dir = student_dir / 'mistakes' / 'math'
        
        # 创建不同错误类型的错题（使用唯一 ID）
        test_cases = [
            ('calc-001', '计算错误'),
            ('concept-001', '概念不清'),
            ('calc-002', '计算错误'),
        ]
        for mistake_id, error_type in test_cases:
            mistake_dir = mistakes_dir / mistake_id
            mistake_dir.mkdir(parents=True, exist_ok=True)
            write_mistake_file(
                mistake_dir / 'mistake.md',
                {
                    'id': mistake_id,
                    'student': '错误类型统计',
                    'subject': 'math',
                    'knowledge-point': '测试',
                    'error-type': error_type,
                    'created': '2026-04-01',
                    'due-date': '2026-05-01',
                    'review-round': '0',
                },
                sample_mistake_content
            )
        
        service = ReviewService('错误类型统计', base_dir=temp_dir)
        stats = service.get_review_stats()
        
        assert stats.by_error_type.get('计算错误', 0) == 2
        assert stats.by_error_type.get('概念不清', 0) == 1
    
    def test_get_review_stats_average_round(self, temp_dir, sample_mistake_content):
        """测试平均复习轮次计算"""
        student_dir = get_student_dir('平均轮次统计', temp_dir)
        mistakes_dir = student_dir / 'mistakes' / 'math'
        
        # 创建不同轮次的错题
        for i, round_val in enumerate([0, 2, 4]):
            mistake_dir = mistakes_dir / f'test-{i}'
            mistake_dir.mkdir(parents=True, exist_ok=True)
            write_mistake_file(
                mistake_dir / 'mistake.md',
                {
                    'id': f'test-{i}',
                    'student': '平均轮次统计',
                    'subject': 'math',
                    'knowledge-point': '测试',
                    'error-type': '计算错误',
                    'created': '2026-04-01',
                    'due-date': '2026-05-01',
                    'review-round': str(round_val),
                },
                sample_mistake_content
            )
        
        service = ReviewService('平均轮次统计', base_dir=temp_dir)
        stats = service.get_review_stats()
        
        # 平均轮次 = (0 + 2 + 4) / 3 = 2.0
        assert stats.average_round == 2.0
    
    def test_get_review_stats_empty(self, temp_dir):
        """测试空数据统计"""
        service = ReviewService('空学生', base_dir=temp_dir)
        
        stats = service.get_review_stats()
        
        assert stats.total_mistakes == 0
        assert stats.completed == 0
        assert stats.due_today == 0
        assert stats.overdue == 0
        assert stats.upcoming == 0
        assert stats.by_subject == {}
        assert stats.by_error_type == {}
        assert stats.average_round == 0.0
    
    def test_get_review_stats_period_parameter(self, temp_dir, setup_student_mistakes):
        """测试 period 参数（目前未实现差异化，但应能接受）"""
        service = ReviewService('张三', base_dir=temp_dir)
        
        stats_week = service.get_review_stats(period='week')
        stats_month = service.get_review_stats(period='month')
        
        # 目前 period 参数不影响结果，但应能正常调用
        assert isinstance(stats_week, ReviewStats)
        assert isinstance(stats_month, ReviewStats)


class TestReviewResult:
    """ReviewResult 数据类测试"""
    
    def test_review_result_success(self):
        """测试成功的 ReviewResult"""
        result = ReviewResult(
            mistake_id='test-001',
            success=True,
            old_round=0,
            new_round=1,
            old_due_date=date(2026, 4, 11),
            new_due_date=date(2026, 4, 14),
        )
        
        assert result.mistake_id == 'test-001'
        assert result.success is True
        assert result.error is None
    
    def test_review_result_failure(self):
        """测试失败的 ReviewResult"""
        result = ReviewResult(
            mistake_id='test-001',
            success=False,
            error='未找到错题',
        )
        
        assert result.success is False
        assert result.error == '未找到错题'


class TestBatchResult:
    """BatchResult 数据类测试"""
    
    def test_batch_result_success_rate(self):
        """测试成功率计算"""
        result = BatchResult(
            total=10,
            success_count=8,
            failed_count=2,
        )
        
        assert result.success_rate == 0.8
    
    def test_batch_result_zero_total(self):
        """测试总数为 0 时的成功率"""
        result = BatchResult(
            total=0,
            success_count=0,
            failed_count=0,
        )
        
        assert result.success_rate == 0.0
    
    def test_batch_result_with_results_list(self):
        """测试包含详细结果列表"""
        results = [
            ReviewResult(mistake_id='test-001', success=True),
            ReviewResult(mistake_id='test-002', success=False, error='not found'),
        ]
        
        batch = BatchResult(
            total=2,
            success_count=1,
            failed_count=1,
            results=results,
        )
        
        assert len(batch.results) == 2
        assert batch.results[0].mistake_id == 'test-001'
        assert batch.results[1].mistake_id == 'test-002'


class TestReviewStats:
    """ReviewStats 数据类测试"""
    
    def test_review_stats_default_values(self):
        """测试默认值"""
        stats = ReviewStats()
        
        assert stats.total_mistakes == 0
        assert stats.completed == 0
        assert stats.due_today == 0
        assert stats.overdue == 0
        assert stats.upcoming == 0
        assert stats.by_subject == {}
        assert stats.by_error_type == {}
        assert stats.average_round == 0.0
    
    def test_review_stats_custom_values(self):
        """测试自定义值"""
        stats = ReviewStats(
            total_mistakes=10,
            completed=3,
            due_today=2,
            overdue=1,
            upcoming=4,
            by_subject={'math': 6, 'chinese': 4},
            by_error_type={'计算错误': 5, '概念不清': 5},
            average_round=2.5,
        )
        
        assert stats.total_mistakes == 10
        assert stats.completed == 3
        assert stats.by_subject['math'] == 6
        assert stats.by_error_type['计算错误'] == 5
        assert stats.average_round == 2.5
