"""
ReportService 单元测试模块

测试报告生成服务的各项功能，包括：
- 初始化
- 薄弱知识点报告生成
- 月度报告生成
- 分析报告生成
- 报告保存功能
"""

import tempfile
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest

from scripts.services.report_service import (
    Report,
    ReportService,
    KnowledgePointStats,
    create_report_service,
)


class TestReportDataclass:
    """测试 Report 数据类"""
    
    def test_report_creation(self):
        """测试 Report 基本创建"""
        report = Report(
            title="测试报告",
            student="张三",
            report_type="analysis",
            content="# 测试内容"
        )
        
        assert report.title == "测试报告"
        assert report.student == "张三"
        assert report.report_type == "analysis"
        assert report.content == "# 测试内容"
        assert isinstance(report.generated_at, datetime)
        assert report.output_path is None
    
    def test_report_with_metadata(self):
        """测试带元数据的 Report"""
        metadata = {'top_n': 5, 'total': 100}
        report = Report(
            title="薄弱知识点",
            student="李四",
            report_type="weak-points",
            content="内容",
            metadata=metadata
        )
        
        assert report.metadata == metadata
        assert report.metadata['top_n'] == 5
    
    def test_report_save(self, tmp_path: Path):
        """测试 Report 保存功能"""
        output_path = tmp_path / "test_report.md"
        report = Report(
            title="保存测试",
            student="王五",
            report_type="test",
            content="# 保存测试内容\n\n这是测试。"
        )
        
        saved_path = report.save(output_path)
        
        assert saved_path == output_path
        assert saved_path.exists()
        content = saved_path.read_text(encoding="utf-8")
        assert "# 保存测试内容" in content
        assert "这是测试。" in content
    
    def test_report_save_without_path_raises(self):
        """测试未指定路径时保存抛出异常"""
        report = Report(
            title="无路径",
            student="赵六",
            report_type="test",
            content="内容"
        )
        
        with pytest.raises(ValueError, match="未指定输出路径"):
            report.save()


class TestKnowledgePointStats:
    """测试 KnowledgePointStats 数据类"""
    
    def test_stats_creation(self):
        """测试知识点统计创建"""
        stats = KnowledgePointStats(name="二次函数")
        
        assert stats.name == "二次函数"
        assert stats.mistake_count == 0
        assert len(stats.subjects) == 0
        assert len(stats.error_types) == 0
        assert len(stats.mistakes) == 0
    
    def test_stats_with_data(self):
        """测试带数据的知识点统计"""
        stats = KnowledgePointStats(
            name="牛顿定律",
            mistake_count=5,
            subjects={'physics', 'math'},
            error_types={'概念不清': 3, '计算错误': 2}
        )
        
        assert stats.mistake_count == 5
        assert len(stats.subjects) == 2
        assert 'physics' in stats.subjects
        assert stats.error_types['概念不清'] == 3


class TestReportService:
    """测试 ReportService 服务类"""
    
    @pytest.fixture
    def temp_student_dir(self) -> Path:
        """创建临时学生目录"""
        temp_dir = tempfile.mkdtemp()
        base_dir = Path(temp_dir) / "students"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试学生目录
        student_dir = base_dir / "测试学生"
        student_dir.mkdir(parents=True)
        
        yield base_dir
        
        # 清理
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_student_dir: Path) -> ReportService:
        """创建 ReportService 实例"""
        return ReportService("测试学生", base_dir=temp_student_dir)
    
    def test_service_initialization(self, temp_student_dir: Path):
        """测试服务初始化"""
        service = ReportService("测试学生", base_dir=temp_student_dir)
        
        assert service.student_name == "测试学生"
        assert service.base_dir == temp_student_dir
        assert service.student_dir == temp_student_dir / "测试学生"
        assert service.student_dir.exists()
    
    def test_service_default_base_dir(self):
        """测试默认基础目录"""
        service = ReportService("默认学生")
        
        assert service.student_name == "默认学生"
        assert service.base_dir is None
    
    def test_load_empty_mistakes(self, service: ReportService):
        """测试加载空错题列表"""
        mistakes = service._load_all_mistakes()
        
        assert isinstance(mistakes, list)
        assert len(mistakes) == 0
    
    def test_analyze_empty_knowledge_points(self, service: ReportService):
        """测试分析空知识点"""
        stats = service._analyze_knowledge_points([])
        
        assert isinstance(stats, dict)
        assert len(stats) == 0
    
    def test_get_suggestion_for_count(self, service: ReportService):
        """测试根据错题数量获取建议"""
        assert service._get_suggestion_for_count(1) == "🟡 正常复习巩固"
        assert service._get_suggestion_for_count(2) == "🟡 正常复习巩固"
        assert service._get_suggestion_for_count(3) == "🟠 重点加强练习"
        assert service._get_suggestion_for_count(4) == "🟠 重点加强练习"
        assert service._get_suggestion_for_count(5) == "🔴 立即专项突破"
        assert service._get_suggestion_for_count(10) == "🔴 立即专项突破"
    
    def test_get_learning_suggestions(self, service: ReportService):
        """测试获取学习建议"""
        # 测试单个错误类型
        suggestions = service._get_learning_suggestions({'概念不清': 2})
        assert len(suggestions) == 1
        assert "📖 回归课本" in suggestions[0]
        
        # 测试多个错误类型
        suggestions = service._get_learning_suggestions({
            '概念不清': 2,
            '计算错误': 3,
            '审题错误': 1
        })
        assert len(suggestions) == 3
        assert any("📖" in s for s in suggestions)
        assert any("✏️" in s for s in suggestions)
        assert any("🔍" in s for s in suggestions)
    
    def test_create_report_service_function(self, temp_student_dir: Path):
        """测试便利函数"""
        service = create_report_service("函数测试", base_dir=temp_student_dir)
        
        assert isinstance(service, ReportService)
        assert service.student_name == "函数测试"


class TestReportServiceWithFixtures:
    """使用测试夹具的 ReportService 集成测试"""
    
    @pytest.fixture
    def temp_student_dir(self) -> Path:
        """创建带测试数据的临时学生目录"""
        temp_dir = tempfile.mkdtemp()
        base_dir = Path(temp_dir) / "students"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        student_dir = base_dir / "测试学生"
        student_dir.mkdir(parents=True)
        
        # 创建测试错题数据
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir(parents=True)
        
        # 创建数学错题 1
        math1_dir = mistakes_dir / "math-001"
        math1_dir.mkdir(parents=True)
        (math1_dir / "mistake.md").write_text(
            """---
id: math-001
student: 测试学生
subject: math
knowledge-point: 二次函数
error-type: 概念不清
created: 2026-04-01
due-date: 2026-04-02
review-round: 0
difficulty: ⭐⭐
status: 待复习
---

# 题目内容

这是一道关于二次函数的题目。
""",
            encoding="utf-8"
        )
        
        # 创建数学错题 2（同知识点）
        math2_dir = mistakes_dir / "math-002"
        math2_dir.mkdir(parents=True)
        (math2_dir / "mistake.md").write_text(
            """---
id: math-002
student: 测试学生
subject: math
knowledge-point: 二次函数
error-type: 计算错误
created: 2026-04-02
due-date: 2026-04-03
review-round: 0
difficulty: ⭐⭐⭐
status: 待复习
---

# 题目内容 2

另一道二次函数题目。
""",
            encoding="utf-8"
        )
        
        # 创建物理错题
        physics_dir = mistakes_dir / "physics-001"
        physics_dir.mkdir(parents=True)
        (physics_dir / "mistake.md").write_text(
            """---
id: physics-001
student: 测试学生
subject: physics
knowledge-point: 牛顿第一定律
error-type: 审题错误
created: 2026-04-03
due-date: 2026-04-04
review-round: 0
difficulty: ⭐⭐⭐⭐
status: 待复习
---

# 物理题目

关于牛顿定律的题目。
""",
            encoding="utf-8"
        )
        
        yield base_dir
        
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_student_dir: Path) -> ReportService:
        """创建 ReportService 实例"""
        return ReportService("测试学生", base_dir=temp_student_dir)
    
    def test_load_mistakes(self, service: ReportService):
        """测试加载错题"""
        mistakes = service._load_all_mistakes()
        
        assert len(mistakes) == 3
        assert all('id' in m for m in mistakes)
        assert all('knowledge-point' in m for m in mistakes)
    
    def test_load_mistakes_by_subject(self, service: ReportService):
        """测试按学科加载错题"""
        math_mistakes = service._load_all_mistakes(subject="math")
        physics_mistakes = service._load_all_mistakes(subject="physics")
        
        assert len(math_mistakes) == 2
        assert len(physics_mistakes) == 1
        assert all(m['subject'] == 'math' for m in math_mistakes)
        assert all(m['subject'] == 'physics' for m in physics_mistakes)
    
    def test_analyze_knowledge_points(self, service: ReportService):
        """测试知识点分析"""
        mistakes = service._load_all_mistakes()
        stats = service._analyze_knowledge_points(mistakes)
        
        assert len(stats) == 2  # 二次函数、牛顿第一定律
        assert "二次函数" in stats
        assert "牛顿第一定律" in stats
        assert stats["二次函数"].mistake_count == 2
        assert stats["牛顿第一定律"].mistake_count == 1
    
    def test_generate_weak_points_report(self, service: ReportService):
        """测试生成薄弱知识点报告"""
        report = service.generate_weak_points_report(top_n=5)
        
        assert report.report_type == "weak-points"
        assert report.student == "测试学生"
        assert "薄弱知识点" in report.title
        assert "二次函数" in report.content
        assert "牛顿第一定律" in report.content
        assert "TOP 5" in report.content or "TOP5" in report.content
        assert report.metadata['total_mistakes'] == 3
        assert report.output_path is not None
    
    def test_generate_weak_points_report_empty(self, temp_student_dir: Path):
        """测试生成空薄弱知识点报告"""
        service = ReportService("空学生", base_dir=temp_student_dir)
        report = service.generate_weak_points_report()
        
        assert report.report_type == "weak-points"
        assert "暂无错题数据" in report.content
        assert report.metadata['total_mistakes'] == 0
    
    def test_generate_monthly_report(self, service: ReportService):
        """测试生成月度报告"""
        report = service.generate_monthly_report("2026-04")
        
        assert report.report_type == "monthly"
        assert report.student == "测试学生"
        assert "2026 年 4 月" in report.title or "月度" in report.title
        assert "数学" in report.content or "math" in report.content
        assert "物理" in report.content or "physics" in report.content
        assert report.metadata['year_month'] == "2026-04"
        assert report.metadata['total_mistakes'] == 3
    
    def test_generate_monthly_report_no_data(self, service: ReportService):
        """测试生成无数据的月度报告"""
        report = service.generate_monthly_report("2025-01")
        
        assert report.report_type == "monthly"
        assert report.metadata['total_mistakes'] == 0
    
    def test_generate_analysis_report(self, service: ReportService):
        """测试生成分析报告"""
        report = service.generate_analysis_report()
        
        assert report.report_type == "analysis"
        assert report.student == "测试学生"
        assert "分析" in report.title
        assert "错题总数" in report.content
        assert "3" in report.content  # 总错题数
        assert report.metadata['total_mistakes'] == 3
    
    def test_generate_analysis_report_by_subject(self, service: ReportService):
        """测试按学科生成分析报告"""
        report = service.generate_analysis_report(subject="math")
        
        assert report.report_type == "analysis"
        assert report.metadata['subject'] == "math"
        assert report.metadata['total_mistakes'] == 2
    
    def test_report_save_integration(self, service: ReportService, tmp_path: Path):
        """测试报告保存集成"""
        output_path = tmp_path / "weak_points.md"
        report = service.generate_weak_points_report(top_n=5, output_path=output_path)
        
        saved_path = report.save()
        assert saved_path == output_path
        assert saved_path.exists()
        
        content = saved_path.read_text(encoding="utf-8")
        assert "薄弱知识点" in content
        assert "测试学生" in content


class TestReportServiceEdgeCases:
    """测试边界情况"""
    
    @pytest.fixture
    def temp_student_dir(self) -> Path:
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        base_dir = Path(temp_dir) / "students"
        base_dir.mkdir(parents=True, exist_ok=True)
        yield base_dir
        shutil.rmtree(temp_dir)
    
    def test_student_dir_creation(self, temp_student_dir: Path):
        """测试学生目录自动创建"""
        service = ReportService("新学生", base_dir=temp_student_dir)
        
        assert service.student_dir.exists()
        assert service.student_dir.name == "新学生"
    
    def test_mistakes_dir_not_exists(self, temp_student_dir: Path):
        """测试错题目录不存在时的处理"""
        service = ReportService("新学生", base_dir=temp_student_dir)
        mistakes = service._load_all_mistakes()
        
        assert isinstance(mistakes, list)
        assert len(mistakes) == 0
    
    def test_report_with_special_characters(self, temp_student_dir: Path):
        """测试包含特殊字符的报告生成"""
        student_dir = temp_student_dir / "特殊学生"
        student_dir.mkdir()
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir()
        
        # 创建包含特殊字符的错题
        test_dir = mistakes_dir / "test-001"
        test_dir.mkdir()
        (test_dir / "mistake.md").write_text(
            """---
id: test-001
student: 特殊学生
subject: math
knowledge-point: 特殊字符测试：αβγ & < > "
error-type: 概念不清
created: 2026-04-01
due-date: 2026-04-02
review-round: 0
---

# 题目

包含特殊字符：αβγδ & < > " '
""",
            encoding="utf-8"
        )
        
        service = ReportService("特殊学生", base_dir=temp_student_dir)
        report = service.generate_weak_points_report()
        
        assert report.metadata['total_mistakes'] == 1
        assert "特殊字符测试" in report.content
    
    def test_report_metadata_completeness(self, temp_student_dir: Path):
        """测试报告元数据完整性"""
        student_dir = temp_student_dir / "元数据学生"
        student_dir.mkdir()
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir()
        
        # 创建测试数据
        for i in range(3):
            test_dir = mistakes_dir / f"test-{i:03d}"
            test_dir.mkdir()
            (test_dir / "mistake.md").write_text(
                f"""---
id: test-{i:03d}
student: 元数据学生
subject: math
knowledge-point: 知识点{i}
error-type: 概念不清
created: 2026-04-0{i+1}
due-date: 2026-04-0{i+2}
review-round: 0
---

# 题目 {i}
""",
                encoding="utf-8"
            )
        
        service = ReportService("元数据学生", base_dir=temp_student_dir)
        
        # 测试薄弱知识点报告元数据
        wp_report = service.generate_weak_points_report(top_n=3)
        assert 'top_n' in wp_report.metadata
        assert 'total_mistakes' in wp_report.metadata
        assert 'knowledge_points_count' in wp_report.metadata
        
        # 测试月度报告元数据
        monthly_report = service.generate_monthly_report("2026-04")
        assert 'year_month' in monthly_report.metadata
        assert 'total_mistakes' in monthly_report.metadata
        assert 'subject' in monthly_report.metadata
        
        # 测试分析报告元数据
        analysis_report = service.generate_analysis_report()
        assert 'total_mistakes' in analysis_report.metadata
        assert 'subject' in analysis_report.metadata
        assert 'due_reviews_count' in analysis_report.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
