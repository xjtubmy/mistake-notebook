"""
数据模型模块 - 错题本核心数据结构

定义错题记录的基本数据模型，包括学科、错误类型、置信度等枚举类型，
以及 Mistake 数据类用于表示单个错题记录。
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Subject(str, Enum):
    """学科枚举类型
    
    定义支持的学科类别，用于标识错题所属的学科。
    """
    MATH = 'math'
    CHINESE = 'chinese'
    ENGLISH = 'english'
    PHYSICS = 'physics'
    CHEMISTRY = 'chemistry'
    BIOLOGY = 'biology'


class ErrorType(str, Enum):
    """错误类型枚举
    
    定义学生做题时可能出现的错误类型，用于分类统计和针对性复习。
    """
    CONCEPT = '概念不清'
    CALC = '计算错误'
    READ = '审题错误'
    FORMULA = '公式错误'
    LOGIC = '逻辑错误'
    FORMAT = '书写错误'


class Confidence(str, Enum):
    """置信度枚举
    
    表示学生对某道题目的掌握程度置信度，用于调整复习间隔。
    """
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


@dataclass
class Mistake:
    """错题数据模型
    
    表示单个错题记录的完整数据结构，包含题目信息、学生答案、
    正确答案、分析以及复习状态等字段。
    
    Attributes:
        id: 错题唯一标识符
        student: 学生标识符
        subject: 所属学科
        knowledge_point: 知识点
        unit: 所属单元（可选）
        error_type: 错误类型
        created: 创建日期
        due_date: 下次复习日期
        review_round: 当前复习轮次，默认为 0
        confidence: 掌握程度置信度，默认为 LOW
        question: 题目内容，默认为空字符串
        student_answer: 学生答案，默认为空字符串
        correct_answer: 正确答案，默认为空字符串
        analysis: 解析说明，默认为空字符串
        path: 原始文件路径（可选）
        image_path: 题目图片路径（可选）
    
    Methods:
        is_completed: 判断该错题是否已完成复习
        days_overdue: 计算逾期天数
    """
    
    id: str
    student: str
    subject: Subject
    knowledge_point: str
    unit: Optional[str]
    error_type: ErrorType
    created: date
    due_date: date
    review_round: int = 0
    confidence: Confidence = Confidence.LOW
    question: str = ''
    student_answer: str = ''
    correct_answer: str = ''
    analysis: str = ''
    path: Optional[str] = None
    image_path: Optional[str] = None
    
    def is_completed(self) -> bool:
        """判断错题是否已完成复习
        
        当 due_date 为 date.max 或字符串 'completed' 时，表示该错题
        已完成所有复习轮次，不再需要复习。
        
        Returns:
            bool: 如果已完成复习返回 True，否则返回 False
        """
        return self.due_date == date.max or str(self.due_date) == 'completed'
    
    def days_overdue(self, target_date: Optional[date] = None) -> int:
        """计算错题逾期天数
        
        计算从 due_date 到目标日期的逾期天数。如果 target_date
        早于或等于 due_date，则返回 0 或负数。
        
        Args:
            target_date: 目标日期，默认为今天
        
        Returns:
            int: 逾期天数，正数表示已逾期，0 或负数表示未逾期
        """
        if target_date is None:
            target_date = date.today()
        return (target_date - self.due_date).days
