"""
复习服务模块 - 错题复习状态管理和统计

提供复习到期查询、状态更新、批量操作和统计功能。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

from scripts.core.file_ops import find_mistake_files, get_student_dir, read_mistake_file, write_mistake_file
from scripts.core.models import Mistake, Subject, ErrorType, Confidence
from scripts.core.srs import calculate_next_due, is_due_today, ReviewSchedule


@dataclass
class ReviewResult:
    """单次复习更新结果
    
    Attributes:
        mistake_id: 错题 ID
        success: 是否更新成功
        old_round: 原复习轮次
        new_round: 新复习轮次
        old_due_date: 原到期日
        new_due_date: 新到期日
        error: 错误信息（如果失败）
    """
    mistake_id: str
    success: bool
    old_round: int = 0
    new_round: int = 0
    old_due_date: Optional[date] = None
    new_due_date: Optional[date] = None
    error: Optional[str] = None


@dataclass
class BatchResult:
    """批量复习更新结果
    
    Attributes:
        total: 总处理数量
        success_count: 成功数量
        failed_count: 失败数量
        results: 详细结果列表
    """
    total: int = 0
    success_count: int = 0
    failed_count: int = 0
    results: List[ReviewResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total == 0:
            return 0.0
        return self.success_count / self.total


@dataclass
class ReviewHistoryEntry:
    """复习历史条目
    
    Attributes:
        date: 复习日期
        subject: 学科
        confidence: 掌握度
        mistake_id: 错题 ID
        knowledge_point: 知识点
    """
    date: date
    subject: str
    confidence: str
    mistake_id: str
    knowledge_point: str


@dataclass
class ReviewStats:
    """复习统计信息
    
    Attributes:
        total_mistakes: 总错题数
        completed: 已完成复习数
        due_today: 今日到期数
        overdue: 已逾期数
        upcoming: 即将到期（未来 7 天内）
        by_subject: 按学科统计
        by_error_type: 按错误类型统计
        average_round: 平均复习轮次
    """
    total_mistakes: int = 0
    completed: int = 0
    due_today: int = 0
    overdue: int = 0
    upcoming: int = 0
    by_subject: dict = field(default_factory=dict)
    by_error_type: dict = field(default_factory=dict)
    average_round: float = 0.0


class ReviewService:
    """复习服务类
    
    提供学生错题复习状态的管理功能，包括：
    - 查询到期复习的错题
    - 更新单次复习状态
    - 批量更新复习状态
    - 获取复习统计信息
    
    Attributes:
        student_name: 学生姓名
        base_dir: 基础目录（可选）
        student_dir: 学生目录路径
    """
    
    def __init__(self, student_name: str, base_dir: Optional[Path] = None):
        """初始化复习服务
        
        Args:
            student_name: 学生姓名
            base_dir: 基础目录，默认为 data/mistake-notebook/students
        """
        self.student_name = student_name
        self.base_dir = base_dir
        self.student_dir = get_student_dir(student_name, base_dir)
    
    def _parse_mistake_from_file(self, file_path: Path) -> Optional[Mistake]:
        """从文件解析 Mistake 对象
        
        Args:
            file_path: 错题文件路径
        
        Returns:
            Mistake 对象，解析失败返回 None
        """
        try:
            fm, body = read_mistake_file(file_path)
            
            # 解析必需字段
            mistake_id = fm.get('id', '')
            subject_str = fm.get('subject', '')
            knowledge_point = fm.get('knowledge-point', '')
            error_type_str = fm.get('error-type', '')
            created_str = fm.get('created', '')
            due_date_str = fm.get('due-date', '')
            
            if not all([mistake_id, subject_str, knowledge_point, error_type_str, created_str, due_date_str]):
                return None
            
            # 转换枚举类型
            try:
                subject = Subject(subject_str)
            except ValueError:
                return None
            
            try:
                error_type = ErrorType(error_type_str)
            except ValueError:
                return None
            
            # 解析日期
            from datetime import datetime
            try:
                created = datetime.strptime(created_str, '%Y-%m-%d').date()
            except ValueError:
                return None
            
            # 处理 due_date
            if due_date_str.lower() == 'completed':
                due_date = date.max
            else:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                except ValueError:
                    return None
            
            # 解析可选字段
            unit = fm.get('unit')
            review_round = int(fm.get('review-round', 0) or 0)
            confidence_str = fm.get('confidence', 'low')
            
            try:
                confidence = Confidence(confidence_str)
            except ValueError:
                confidence = Confidence.LOW
            
            return Mistake(
                id=mistake_id,
                student=self.student_name,
                subject=subject,
                knowledge_point=knowledge_point,
                unit=unit,
                error_type=error_type,
                created=created,
                due_date=due_date,
                review_round=review_round,
                confidence=confidence,
                question=body.strip() if body else '',
                path=str(file_path),
            )
        except (OSError, UnicodeDecodeError, KeyError):
            return None
    
    def _update_mistake_file(self, mistake: Mistake) -> bool:
        """更新错题文件
        
        Args:
            mistake: Mistake 对象
        
        Returns:
            是否更新成功
        """
        try:
            if mistake.path:
                file_path = Path(mistake.path)
            else:
                # 构建默认路径
                mistakes_dir = self.student_dir / 'mistakes'
                subject_dir = mistakes_dir / mistake.subject.value
                mistake_dir = subject_dir / mistake.id
                file_path = mistake_dir / 'mistake.md'
            
            # 读取现有内容
            fm, body = read_mistake_file(file_path)
            
            # 更新 frontmatter
            fm['review-round'] = str(mistake.review_round)
            fm['due-date'] = 'completed' if mistake.due_date == date.max else mistake.due_date.strftime('%Y-%m-%d')
            fm['confidence'] = mistake.confidence.value
            
            # 写回文件
            write_mistake_file(file_path, fm, body)
            return True
        except (OSError, UnicodeDecodeError, FileNotFoundError):
            return False
    
    def get_due_reviews(self, target_date: Optional[date] = None) -> List[Mistake]:
        """获取到期需要复习的错题列表
        
        返回所有到期日小于等于目标日期的未完成错题。
        
        Args:
            target_date: 目标日期，默认为今天
        
        Returns:
            到期错题列表，按到期日升序排序
        """
        if target_date is None:
            target_date = date.today()
        
        due_mistakes: List[Mistake] = []
        
        # 查找所有错题文件
        mistake_files = find_mistake_files(self.student_dir)
        
        for file_path in mistake_files:
            mistake = self._parse_mistake_from_file(file_path)
            if mistake is None:
                continue
            
            # 跳过已完成的错题
            if mistake.is_completed():
                continue
            
            # 检查是否到期
            if is_due_today(mistake.due_date, target_date):
                due_mistakes.append(mistake)
        
        # 按到期日排序（最紧急的在前）
        due_mistakes.sort(key=lambda m: m.due_date)
        
        return due_mistakes
    
    def update_review(self, mistake_id: str, result: str = 'pass', confidence: Optional[str] = None) -> ReviewResult:
        """更新单次复习结果
        
        根据复习结果更新错题的复习轮次和下次到期日。
        
        Args:
            mistake_id: 错题 ID
            result: 复习结果，'pass' 表示通过，'fail' 表示未通过
            confidence: 掌握度级别，可选 'low', 'medium', 'high'，用于调整下次复习间隔
        
        Returns:
            ReviewResult 对象，包含更新结果详情
        """
        # 查找错题文件
        mistake_files = find_mistake_files(self.student_dir)
        target_file = None
        
        for file_path in mistake_files:
            try:
                fm, _ = read_mistake_file(file_path)
                if fm.get('id') == mistake_id:
                    target_file = file_path
                    break
            except (OSError, UnicodeDecodeError):
                continue
        
        if target_file is None:
            return ReviewResult(
                mistake_id=mistake_id,
                success=False,
                error=f'未找到错题：{mistake_id}'
            )
        
        # 解析错题
        mistake = self._parse_mistake_from_file(target_file)
        if mistake is None:
            return ReviewResult(
                mistake_id=mistake_id,
                success=False,
                error=f'解析错题失败：{mistake_id}'
            )
        
        # 记录旧状态
        old_round = mistake.review_round
        old_due_date = mistake.due_date
        
        # 如果已完成，直接返回
        if mistake.is_completed():
            return ReviewResult(
                mistake_id=mistake_id,
                success=True,
                old_round=old_round,
                new_round=old_round,
                old_due_date=old_due_date,
                new_due_date=old_due_date,
            )
        
        # 根据结果更新状态
        if result == 'pass':
            # 通过：进入下一轮
            mistake.review_round += 1
            
            # 如果提供了新的掌握度，更新它
            if confidence is not None:
                try:
                    mistake.confidence = Confidence(confidence)
                except ValueError:
                    # 无效的 confidence 值，保持原值
                    pass
            
            # 计算下次到期日
            mistake.due_date = calculate_next_due(
                current_round=mistake.review_round,
                last_review=date.today(),
                confidence=mistake.confidence.value,
            )
        else:
            # 未通过：保持当前轮次，重新安排复习（1 天后）
            mistake.due_date = date.today() + timedelta(days=1)
        
        # 写回文件
        if not self._update_mistake_file(mistake):
            return ReviewResult(
                mistake_id=mistake_id,
                success=False,
                old_round=old_round,
                new_round=mistake.review_round,
                old_due_date=old_due_date,
                new_due_date=mistake.due_date,
                error='写入文件失败'
            )
        
        return ReviewResult(
            mistake_id=mistake_id,
            success=True,
            old_round=old_round,
            new_round=mistake.review_round,
            old_due_date=old_due_date,
            new_due_date=mistake.due_date,
        )
    
    def batch_update(self, mistake_ids: List[str], confidence: Optional[str] = None) -> BatchResult:
        """批量更新复习状态
        
        对所有指定的错题执行复习更新（默认为通过）。
        
        Args:
            mistake_ids: 错题 ID 列表
            confidence: 掌握度级别，可选 'low', 'medium', 'high'，批量设置给所有错题
        
        Returns:
            BatchResult 对象，包含批量操作结果统计
        """
        batch_result = BatchResult(total=len(mistake_ids))
        
        for mistake_id in mistake_ids:
            result = self.update_review(mistake_id, confidence=confidence)
            batch_result.results.append(result)
            
            if result.success:
                batch_result.success_count += 1
            else:
                batch_result.failed_count += 1
        
        return batch_result
    
    def get_review_stats(self, period: str = 'week') -> ReviewStats:
        """获取复习统计信息
        
        Args:
            period: 统计周期，'week'（周）或 'month'（月）
        
        Returns:
            ReviewStats 对象，包含详细统计信息
        """
        stats = ReviewStats()
        
        # 查找所有错题文件
        mistake_files = find_mistake_files(self.student_dir)
        
        today = date.today()
        stats.by_subject = {}
        stats.by_error_type = {}
        total_rounds = 0
        
        for file_path in mistake_files:
            mistake = self._parse_mistake_from_file(file_path)
            if mistake is None:
                continue
            
            stats.total_mistakes += 1
            total_rounds += mistake.review_round
            
            # 统计完成情况
            if mistake.is_completed():
                stats.completed += 1
            else:
                # 统计到期情况
                if mistake.due_date <= today:
                    if mistake.due_date < today:
                        stats.overdue += 1
                    else:
                        stats.due_today += 1
                elif mistake.due_date <= today + timedelta(days=7):
                    stats.upcoming += 1
            
            # 按学科统计
            subject_key = mistake.subject.value
            stats.by_subject[subject_key] = stats.by_subject.get(subject_key, 0) + 1
            
            # 按错误类型统计
            error_type_key = mistake.error_type.value
            stats.by_error_type[error_type_key] = stats.by_error_type.get(error_type_key, 0) + 1
        
        # 计算平均复习轮次
        if stats.total_mistakes > 0:
            stats.average_round = total_rounds / stats.total_mistakes
        
        return stats
    
    def get_review_history(self, period: str = 'month') -> List[ReviewHistoryEntry]:
        """获取复习历史数据
        
        根据指定的时间周期，返回复习历史数据，包括日期、学科、掌握度等信息。
        用于生成复习热力图等可视化图表。
        
        Args:
            period: 时间周期，支持：
                    - 'week': 最近 7 天
                    - 'month': 最近 30 天
                    - 'year': 最近 365 天
                    - 'all': 所有历史数据
                    - 或自定义格式 'YYYY-MM'（指定月份）
        
        Returns:
            ReviewHistoryEntry 列表，按日期升序排序
        
        Example:
            >>> service = ReviewService("张三")
            >>> history = service.get_review_history(period='month')
            >>> len(history) >= 0
            True
        """
        today = date.today()
        
        # 计算起始日期和结束日期
        if period == 'week':
            start_date = today - timedelta(days=7)
            end_date = today
        elif period == 'month':
            start_date = today - timedelta(days=30)
            end_date = today
        elif period == 'year':
            start_date = today - timedelta(days=365)
            end_date = today
        elif period == 'all':
            start_date = date(2000, 1, 1)  # 足够早的日期
            end_date = today
        else:
            # 尝试解析 YYYY-MM 格式
            try:
                year_month = date.fromisoformat(f"{period}-01")
                start_date = year_month.replace(day=1)
                # 结束日期为下个月第一天
                if year_month.month == 12:
                    end_date = year_month.replace(year=year_month.year + 1, month=1, day=1)
                else:
                    end_date = year_month.replace(month=year_month.month + 1, day=1)
            except ValueError:
                # 无法解析，默认为 month
                start_date = today - timedelta(days=30)
                end_date = today
        
        history: List[ReviewHistoryEntry] = []
        
        # 查找所有错题文件
        mistake_files = find_mistake_files(self.student_dir)
        
        for file_path in mistake_files:
            mistake = self._parse_mistake_from_file(file_path)
            if mistake is None:
                continue
            
            # 根据 review-round 和 created 推断复习历史
            # 假设每轮复习都产生了记录
            review_round = mistake.review_round
            
            # 如果是已完成的，使用 due_date 作为最后复习日期
            if mistake.is_completed():
                # 已完成：使用到期日作为参考
                if start_date <= mistake.due_date <= end_date:
                    history.append(ReviewHistoryEntry(
                        date=mistake.due_date,
                        subject=mistake.subject.value,
                        confidence=mistake.confidence.value,
                        mistake_id=mistake.id,
                        knowledge_point=mistake.knowledge_point,
                    ))
            else:
                # 未完成：根据 review_round 推断历史复习
                if review_round > 0:
                    # 有复习历史，根据轮次推算复习日期
                    # 简化处理：使用 created + 轮次 * 平均间隔 估算
                    from scripts.core.srs import DEFAULT_REVIEW_INTERVALS
                    
                    review_dates = []
                    current_date = mistake.created
                    
                    for round_num in range(1, review_round + 1):
                        if round_num <= len(DEFAULT_REVIEW_INTERVALS):
                            interval = DEFAULT_REVIEW_INTERVALS[round_num - 1]
                        else:
                            interval = 30  # 默认间隔
                        
                        current_date = current_date + timedelta(days=interval)
                        review_dates.append(current_date)
                    
                    # 过滤在时间范围内的复习记录
                    for review_date in review_dates:
                        if start_date <= review_date <= end_date:
                            history.append(ReviewHistoryEntry(
                                date=review_date,
                                subject=mistake.subject.value,
                                confidence=mistake.confidence.value,
                                mistake_id=mistake.id,
                                knowledge_point=mistake.knowledge_point,
                            ))
        
        # 按日期排序
        history.sort(key=lambda x: x.date)
        
        return history
