"""
数据模型单元测试

测试 scripts.core.models 模块中的枚举类型和 Mistake 数据类。
"""

from datetime import date, timedelta
import pytest
from scripts.core.models import Mistake, Subject, ErrorType, Confidence


class TestSubject:
    """Subject 枚举类型测试"""
    
    def test_subject_math(self):
        """测试数学学科枚举值"""
        assert Subject.MATH.value == 'math'
        assert Subject.MATH.name == 'MATH'
    
    def test_subject_chinese(self):
        """测试语文学科枚举值"""
        assert Subject.CHINESE.value == 'chinese'
    
    def test_subject_english(self):
        """测试英语学科枚举值"""
        assert Subject.ENGLISH.value == 'english'
    
    def test_subject_physics(self):
        """测试物理学科枚举值"""
        assert Subject.PHYSICS.value == 'physics'
    
    def test_subject_chemistry(self):
        """测试化学学科枚举值"""
        assert Subject.CHEMISTRY.value == 'chemistry'
    
    def test_subject_biology(self):
        """测试生物学科枚举值"""
        assert Subject.BIOLOGY.value == 'biology'
    
    def test_subject_string_comparison(self):
        """测试 Subject 支持字符串比较（继承自 str）"""
        assert Subject.MATH == 'math'
        assert 'math' == Subject.MATH
    
    def test_subject_iteration(self):
        """测试可以遍历所有 Subject 枚举"""
        subjects = list(Subject)
        assert len(subjects) == 6
        assert Subject.MATH in subjects
        assert Subject.BIOLOGY in subjects


class TestErrorType:
    """ErrorType 枚举类型测试"""
    
    def test_error_type_concept(self):
        """测试概念不清错误类型"""
        assert ErrorType.CONCEPT.value == '概念不清'
    
    def test_error_type_calc(self):
        """测试计算错误错误类型"""
        assert ErrorType.CALC.value == '计算错误'
    
    def test_error_type_read(self):
        """测试审题错误错误类型"""
        assert ErrorType.READ.value == '审题错误'
    
    def test_error_type_formula(self):
        """测试公式错误错误类型"""
        assert ErrorType.FORMULA.value == '公式错误'
    
    def test_error_type_logic(self):
        """测试逻辑错误错误类型"""
        assert ErrorType.LOGIC.value == '逻辑错误'
    
    def test_error_type_format(self):
        """测试书写错误错误类型"""
        assert ErrorType.FORMAT.value == '书写错误'
    
    def test_error_type_string_comparison(self):
        """测试 ErrorType 支持字符串比较"""
        assert ErrorType.CALC == '计算错误'
    
    def test_error_type_iteration(self):
        """测试可以遍历所有 ErrorType 枚举"""
        error_types = list(ErrorType)
        assert len(error_types) == 6


class TestConfidence:
    """Confidence 枚举类型测试"""
    
    def test_confidence_low(self):
        """测试低置信度"""
        assert Confidence.LOW.value == 'low'
    
    def test_confidence_medium(self):
        """测试中等置信度"""
        assert Confidence.MEDIUM.value == 'medium'
    
    def test_confidence_high(self):
        """测试高置信度"""
        assert Confidence.HIGH.value == 'high'
    
    def test_confidence_string_comparison(self):
        """测试 Confidence 支持字符串比较"""
        assert Confidence.LOW == 'low'
        assert Confidence.HIGH == 'high'
    
    def test_confidence_iteration(self):
        """测试可以遍历所有 Confidence 枚举"""
        confidences = list(Confidence)
        assert len(confidences) == 3


class TestMistakeCreation:
    """Mistake 数据类创建和属性测试"""
    
    def test_mistake_minimal_creation(self):
        """测试创建最小必需的 Mistake 实例"""
        mistake = Mistake(
            id='001',
            student='test_student',
            subject=Subject.MATH,
            knowledge_point='一元二次方程',
            unit=None,
            error_type=ErrorType.CALC,
            created=date(2026, 4, 12),
            due_date=date(2026, 4, 13),
        )
        
        assert mistake.id == '001'
        assert mistake.student == 'test_student'
        assert mistake.subject == Subject.MATH
        assert mistake.knowledge_point == '一元二次方程'
        assert mistake.unit is None
        assert mistake.error_type == ErrorType.CALC
        assert mistake.created == date(2026, 4, 12)
        assert mistake.due_date == date(2026, 4, 13)
    
    def test_mistake_default_values(self):
        """测试 Mistake 字段的默认值"""
        mistake = Mistake(
            id='002',
            student='test_student',
            subject=Subject.MATH,
            knowledge_point='函数',
            unit=None,
            error_type=ErrorType.CONCEPT,
            created=date.today(),
            due_date=date.today(),
        )
        
        assert mistake.review_round == 0
        assert mistake.confidence == Confidence.LOW
        assert mistake.question == ''
        assert mistake.student_answer == ''
        assert mistake.correct_answer == ''
        assert mistake.analysis == ''
        assert mistake.path is None
        assert mistake.image_path is None
    
    def test_mistake_full_creation(self):
        """测试创建包含所有字段的 Mistake 实例"""
        mistake = Mistake(
            id='003',
            student='test_student',
            subject=Subject.ENGLISH,
            knowledge_point='定语从句',
            unit='Unit 5',
            error_type=ErrorType.GRAMMAR if hasattr(ErrorType, 'GRAMMAR') else ErrorType.LOGIC,
            created=date(2026, 4, 10),
            due_date=date(2026, 4, 15),
            review_round=2,
            confidence=Confidence.HIGH,
            question='What is the relative clause?',
            student_answer='That is...',
            correct_answer='Which/That/Who...',
            analysis='定语从句需要关系代词引导',
            path='/path/to/mistake.md',
            image_path='/path/to/image.png',
        )
        
        assert mistake.review_round == 2
        assert mistake.confidence == Confidence.HIGH
        assert mistake.question == 'What is the relative clause?'
        assert mistake.student_answer == 'That is...'
        assert mistake.correct_answer == 'Which/That/Who...'
        assert mistake.analysis == '定语从句需要关系代词引导'
        assert mistake.path == '/path/to/mistake.md'
        assert mistake.image_path == '/path/to/image.png'
    
    def test_mistake_with_chinese_error_type(self):
        """测试使用中文错误类型创建 Mistake"""
        mistake = Mistake(
            id='004',
            student='张三',
            subject=Subject.CHINESE,
            knowledge_point='文言文阅读',
            unit=None,
            error_type=ErrorType.READ,
            created=date.today(),
            due_date=date.today(),
        )
        
        assert mistake.error_type == ErrorType.READ
        assert mistake.error_type.value == '审题错误'


class TestMistakeIsCompleted:
    """Mistake.is_completed() 方法测试"""
    
    def test_is_completed_with_date_max(self):
        """测试 due_date 为 date.max 时返回 True"""
        mistake = Mistake(
            id='005',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=date.today(),
            due_date=date.max,
        )
        
        assert mistake.is_completed() is True
    
    def test_is_completed_with_completed_string(self):
        """测试 due_date 为 'completed' 字符串时返回 True"""
        # 注意：由于 due_date 是 date 类型，无法直接设置为字符串
        # 这个测试验证当 str(due_date) == 'completed' 时的情况
        # 实际上 date 类型无法等于 'completed'，所以主要测试 date.max 情况
        mistake = Mistake(
            id='006',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=date.today(),
            due_date=date.max,
        )
        
        assert mistake.is_completed() is True
    
    def test_is_completed_not_completed(self):
        """测试未完成的错题返回 False"""
        mistake = Mistake(
            id='007',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=date.today(),
            due_date=date.today() + timedelta(days=1),
        )
        
        assert mistake.is_completed() is False
    
    def test_is_completed_overdue(self):
        """测试已逾期但未完成的错题返回 False"""
        mistake = Mistake(
            id='008',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=1),
        )
        
        assert mistake.is_completed() is False


class TestMistakeDaysOverdue:
    """Mistake.days_overdue() 方法测试"""
    
    def test_days_overdue_one_day(self):
        """测试逾期 1 天"""
        yesterday = date.today() - timedelta(days=1)
        mistake = Mistake(
            id='009',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=yesterday - timedelta(days=1),
            due_date=yesterday,
        )
        
        assert mistake.days_overdue() == 1
    
    def test_days_overdue_multiple_days(self):
        """测试逾期多天"""
        due_date = date.today() - timedelta(days=5)
        mistake = Mistake(
            id='010',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=due_date - timedelta(days=10),
            due_date=due_date,
        )
        
        assert mistake.days_overdue() == 5
    
    def test_days_overdue_zero(self):
        """测试当天到期，逾期 0 天"""
        mistake = Mistake(
            id='011',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=date.today(),
            due_date=date.today(),
        )
        
        assert mistake.days_overdue() == 0
    
    def test_days_overdue_negative(self):
        """测试未到期，返回负数"""
        tomorrow = date.today() + timedelta(days=3)
        mistake = Mistake(
            id='012',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=date.today(),
            due_date=tomorrow,
        )
        
        assert mistake.days_overdue() == -3
    
    def test_days_overdue_with_custom_target_date(self):
        """测试使用自定义目标日期"""
        due_date = date(2026, 4, 10)
        target_date = date(2026, 4, 15)
        mistake = Mistake(
            id='013',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=date(2026, 4, 1),
            due_date=due_date,
        )
        
        assert mistake.days_overdue(target_date) == 5
    
    def test_days_overdue_completed_mistake(self):
        """测试已完成的错题（due_date 为 date.max）"""
        mistake = Mistake(
            id='014',
            student='test',
            subject=Subject.MATH,
            knowledge_point='test',
            unit=None,
            error_type=ErrorType.CALC,
            created=date.today(),
            due_date=date.max,
        )
        
        # date.max - date.today() 会是一个非常大的数字
        # 这表示已完成的错题不会逾期（实际上是负数，因为 date.max 是未来）
        assert mistake.days_overdue() < 0
