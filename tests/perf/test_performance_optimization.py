"""
性能优化单元测试

测试覆盖：
- find_mistake_files_parallel: 并行文件查找
- 目录缓存功能
- get_due_reviews 性能
"""

import shutil
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

import pytest

from scripts.core.file_ops import (
    clear_directory_cache,
    find_mistake_files,
    find_mistake_files_parallel,
    get_student_dir,
    write_mistake_file,
)
from scripts.core.models import Subject, ErrorType, Confidence
from scripts.services.review_service import ReviewService


class TestFindMistakeFilesParallel:
    """find_mistake_files_parallel 函数测试。"""
    
    @pytest.fixture
    def temp_student_dir(self):
        """创建临时学生目录用于测试。"""
        temp_dir = tempfile.mkdtemp()
        student_dir = Path(temp_dir) / "test_student"
        student_dir.mkdir()
        
        # 创建测试文件结构
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir()
        
        # 创建多个数学错题
        for i in range(10):
            math_dir = mistakes_dir / f"math-{i:03d}"
            math_dir.mkdir()
            (math_dir / "mistake.md").write_text(
                f"""---
id: math-{i:03d}
subject: math
knowledge-point: 方程
created: 2026-04-12
due-date: 2026-04-13
review-round: 0
confidence: low
---
# 数学题 {i}
""",
                encoding="utf-8"
            )
        
        # 创建多个物理错题
        for i in range(5):
            physics_dir = mistakes_dir / f"physics-{i:03d}"
            physics_dir.mkdir()
            (physics_dir / "mistake.md").write_text(
                f"""---
id: physics-{i:03d}
subject: physics
knowledge-point: 力学
created: 2026-04-12
due-date: 2026-04-13
review-round: 0
confidence: low
---
# 物理题 {i}
""",
                encoding="utf-8"
            )
        
        yield student_dir
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
    
    def test_parallel_find_all_files(self, temp_student_dir):
        """并行查找所有文件。"""
        files = find_mistake_files_parallel(temp_student_dir)
        assert len(files) == 15
    
    def test_parallel_find_by_subject(self, temp_student_dir):
        """并行按学科筛选。"""
        math_files = find_mistake_files_parallel(temp_student_dir, subject="math")
        assert len(math_files) == 10
        
        physics_files = find_mistake_files_parallel(temp_student_dir, subject="physics")
        assert len(physics_files) == 5
    
    def test_parallel_vs_serial_results(self, temp_student_dir):
        """并行和串行结果一致。"""
        parallel_files = find_mistake_files_parallel(temp_student_dir)
        serial_files = find_mistake_files(temp_student_dir)
        
        # 结果应该相同（顺序可能不同）
        assert len(parallel_files) == len(serial_files)
        assert set(parallel_files) == set(serial_files)
    
    def test_parallel_empty_dir(self):
        """并行查找空目录。"""
        temp_dir = tempfile.mkdtemp()
        student_dir = Path(temp_dir) / "empty_student"
        student_dir.mkdir()
        (student_dir / "mistakes").mkdir()
        
        files = find_mistake_files_parallel(student_dir)
        assert files == []
        
        shutil.rmtree(temp_dir)
    
    def test_parallel_nonexistent_dir(self):
        """并行查找不存在的目录。"""
        files = find_mistake_files_parallel(Path("/nonexistent/path"))
        assert files == []


class TestDirectoryCache:
    """目录缓存功能测试。"""
    
    @pytest.fixture
    def temp_student_dir(self):
        """创建临时学生目录。"""
        temp_dir = tempfile.mkdtemp()
        student_dir = Path(temp_dir) / "cache_test_student"
        student_dir.mkdir()
        
        # 创建测试文件
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir()
        
        for i in range(5):
            math_dir = mistakes_dir / f"math-{i:03d}"
            math_dir.mkdir()
            (math_dir / "mistake.md").write_text(
                f"""---
id: math-{i:03d}
subject: math
knowledge-point: 方程
---
# 数学题
""",
                encoding="utf-8"
            )
        
        yield student_dir
        
        # 清理
        clear_directory_cache()
        shutil.rmtree(temp_dir)
    
    def test_cache_is_used(self, temp_student_dir):
        """测试缓存被使用。"""
        # 第一次查询（建立缓存）
        files1 = find_mistake_files(temp_student_dir, use_cache=True)
        assert len(files1) == 5
        
        # 第二次查询（使用缓存）
        files2 = find_mistake_files(temp_student_dir, use_cache=True)
        assert len(files2) == 5
        
        # 结果应该相同
        assert files1 == files2
    
    def test_cache_can_be_cleared(self, temp_student_dir):
        """测试缓存可以被清除。"""
        # 建立缓存
        files1 = find_mistake_files(temp_student_dir, use_cache=True)
        assert len(files1) == 5
        
        # 清除缓存
        clear_directory_cache(temp_student_dir)
        
        # 再次查询（重新扫描）
        files2 = find_mistake_files(temp_student_dir, use_cache=True)
        assert len(files2) == 5
    
    def test_cache_clear_all(self, temp_student_dir):
        """测试清除所有缓存。"""
        # 建立缓存
        files1 = find_mistake_files(temp_student_dir, use_cache=True)
        assert len(files1) == 5
        
        # 清除所有缓存
        clear_directory_cache()
        
        # 再次查询
        files2 = find_mistake_files(temp_student_dir, use_cache=True)
        assert len(files2) == 5


class TestReviewServicePerformance:
    """ReviewService 性能测试。"""
    
    @pytest.fixture
    def large_dataset_student(self):
        """创建包含大量错题的学生目录。"""
        temp_dir = tempfile.mkdtemp()
        student_name = "perf_test_student"
        student_dir = get_student_dir(student_name, base=Path(temp_dir))
        
        # 创建 100 道错题（测试用，不用太多）
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir()
        
        today = date.today()
        
        for i in range(100):
            subject = Subject.MATH if i % 2 == 0 else Subject.PHYSICS
            error_type = ErrorType.CONCEPT if i % 2 == 0 else ErrorType.CALC
            # 部分到期（50 道），部分未到期
            if i < 50:
                due_date = today - timedelta(days=i % 10 + 1)  # 已到期
            else:
                due_date = today + timedelta(days=i % 10 + 1)  # 未到期
            
            math_dir = mistakes_dir / f"{subject.value}-{i:03d}"
            math_dir.mkdir()
            (math_dir / "mistake.md").write_text(
                f"""---
id: perf-{i:03d}
student: {student_name}
subject: {subject.value}
knowledge-point: 测试知识点
error-type: {error_type.value}
created: 2026-01-01
due-date: {due_date.strftime('%Y-%m-%d')}
review-round: {i % 5}
confidence: medium
---
# 测试题目 {i}
""",
                encoding="utf-8"
            )
        
        yield student_name, Path(temp_dir)
        
        # 清理
        clear_directory_cache()
        shutil.rmtree(temp_dir)
    
    def test_get_due_reviews_performance(self, large_dataset_student):
        """测试 get_due_reviews 性能。"""
        student_name, base_dir = large_dataset_student
        
        service = ReviewService(student_name, base_dir=base_dir, use_parallel=True)
        
        # 测试查询时间
        start_time = time.time()
        due_reviews = service.get_due_reviews()
        elapsed_time = time.time() - start_time
        
        # 100 道错题应该在 0.1 秒内完成
        assert elapsed_time < 0.5, f"查询时间过长：{elapsed_time}秒"
        assert len(due_reviews) > 0, "应该有到期的错题"
    
    def test_get_due_reviews_with_cache(self, large_dataset_student):
        """测试带缓存的查询性能。"""
        student_name, base_dir = large_dataset_student
        
        service = ReviewService(student_name, base_dir=base_dir, use_parallel=True)
        
        # 第一次查询（建立缓存）
        due_reviews_1 = service.get_due_reviews()
        
        # 第二次查询（使用缓存）
        start_time = time.time()
        due_reviews_2 = service.get_due_reviews()
        elapsed_time = time.time() - start_time
        
        # 使用缓存应该更快
        assert elapsed_time < 0.5, f"缓存查询时间过长：{elapsed_time}秒"
        assert len(due_reviews_1) == len(due_reviews_2)
    
    def test_get_review_stats_performance(self, large_dataset_student):
        """测试 get_review_stats 性能。"""
        student_name, base_dir = large_dataset_student
        
        service = ReviewService(student_name, base_dir=base_dir, use_parallel=True)
        
        start_time = time.time()
        stats = service.get_review_stats()
        elapsed_time = time.time() - start_time
        
        # 统计查询应该在合理时间内完成
        assert elapsed_time < 1.0, f"统计查询时间过长：{elapsed_time}秒"
        assert stats.total_mistakes == 100


class TestReviewServiceParallelConfig:
    """ReviewService 并行配置测试。"""
    
    @pytest.fixture
    def temp_student(self):
        """创建临时学生。"""
        temp_dir = tempfile.mkdtemp()
        student_name = "config_test_student"
        student_dir = get_student_dir(student_name, base=Path(temp_dir))
        
        # 创建少量错题
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir()
        
        today = date.today()
        
        for i in range(5):
            math_dir = mistakes_dir / f"math-{i:03d}"
            math_dir.mkdir()
            (math_dir / "mistake.md").write_text(
                f"""---
id: config-{i:03d}
student: {student_name}
subject: math
knowledge-point: 测试
error-type: 概念不清
created: 2026-01-01
due-date: {(today - timedelta(days=1)).strftime('%Y-%m-%d')}
review-round: 0
confidence: low
---
# 测试题目
""",
                encoding="utf-8"
            )
        
        yield student_name, Path(temp_dir)
        
        clear_directory_cache()
        shutil.rmtree(temp_dir)
    
    def test_parallel_enabled(self, temp_student):
        """测试并行处理启用。"""
        student_name, base_dir = temp_student
        
        service = ReviewService(
            student_name,
            base_dir=base_dir,
            use_parallel=True,
            max_workers=4,
        )
        
        assert service.use_parallel is True
        assert service.max_workers == 4
        
        due_reviews = service.get_due_reviews()
        assert len(due_reviews) == 5
    
    def test_parallel_disabled(self, temp_student):
        """测试并行处理禁用（向后兼容）。"""
        student_name, base_dir = temp_student
        
        service = ReviewService(
            student_name,
            base_dir=base_dir,
            use_parallel=False,
        )
        
        assert service.use_parallel is False
        
        due_reviews = service.get_due_reviews()
        assert len(due_reviews) == 5
    
    def test_default_config(self, temp_student):
        """测试默认配置。"""
        student_name, base_dir = temp_student
        
        service = ReviewService(student_name, base_dir=base_dir)
        
        # 默认启用并行
        assert service.use_parallel is True
        assert service.max_workers == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
