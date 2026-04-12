"""
ReportService 错误类型柱状图单元测试。

测试 generate_weak_points_report() 中错误类型柱状图的生成和嵌入功能。
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.services.report_service import ReportService


class TestBarChartGeneration:
    """测试柱状图生成功能。"""
    
    @pytest.fixture
    def temp_student_dir(self) -> Path:
        """创建带测试数据的临时学生目录。"""
        temp_dir = tempfile.mkdtemp()
        base_dir = Path(temp_dir) / "students"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        student_dir = base_dir / "测试学生"
        student_dir.mkdir(parents=True)
        
        # 创建测试错题数据 - 多种错误类型
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir(parents=True)
        
        # 创建 5 道不同错误类型的错题
        test_cases = [
            ("math-001", "math", "二次函数", "概念不清"),
            ("math-002", "math", "二次函数", "计算错误"),
            ("math-003", "math", "一次函数", "概念不清"),
            ("physics-001", "physics", "牛顿定律", "审题错误"),
            ("physics-002", "physics", "牛顿定律", "计算错误"),
            ("physics-003", "physics", "能量守恒", "概念不清"),
        ]
        
        for mistake_id, subject, kp, error_type in test_cases:
            test_subdir = mistakes_dir / mistake_id
            test_subdir.mkdir(parents=True)
            (test_subdir / "mistake.md").write_text(
                f"""---
id: {mistake_id}
student: 测试学生
subject: {subject}
knowledge-point: {kp}
error-type: {error_type}
created: 2026-04-01
due-date: 2026-04-02
review-round: 0
difficulty: ⭐⭐
status: 待复习
---

# 题目内容

这是一道测试题目。
""",
                encoding="utf-8"
            )
        
        yield base_dir
        
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_student_dir: Path) -> ReportService:
        """创建 ReportService 实例。"""
        return ReportService("测试学生", base_dir=temp_student_dir)
    
    def test_bar_chart_generated_in_weak_points_report(self, service: ReportService, tmp_path: Path):
        """测试薄弱知识点报告生成时创建柱状图。"""
        output_path = tmp_path / "weak_points_report.md"
        report = service.generate_weak_points_report(top_n=5, output_path=output_path)
        
        # 验证元数据包含图表路径
        assert 'error_type_chart_path' in report.metadata
        chart_path_str = report.metadata['error_type_chart_path']
        assert chart_path_str is not None
        
        # 验证图表文件存在
        chart_path = Path(chart_path_str)
        assert chart_path.exists(), f"图表文件不存在：{chart_path}"
        assert chart_path.suffix.lower() == ".png"
        assert chart_path.stat().st_size > 0, "图表文件大小为 0"
    
    def test_bar_chart_contains_all_error_types(self, service: ReportService, tmp_path: Path):
        """测试柱状图包含所有错误类型。"""
        output_path = tmp_path / "report.md"
        report = service.generate_weak_points_report(output_path=output_path)
        
        # 验证报告内容包含错误类型
        content = report.content
        assert "概念不清" in content
        assert "计算错误" in content
        assert "审题错误" in content
        
        # 验证图表路径在报告中被引用
        assert "error_type_bar" in report.metadata['error_type_chart_path']
    
    def test_bar_chart_embedded_in_report_content(self, service: ReportService, tmp_path: Path):
        """测试柱状图被嵌入到报告内容中。"""
        output_path = tmp_path / "embedded_report.md"
        report = service.generate_weak_points_report(output_path=output_path)
        
        # 验证报告 Markdown 内容包含图片引用
        assert "![错误类型柱状图]" in report.content
        assert ".png" in report.content
        assert "错误类型分布" in report.content
    
    def test_bar_chart_output_directory_creation(self, service: ReportService, tmp_path: Path):
        """测试柱状图输出目录自动创建。"""
        nested_output_path = tmp_path / "nested" / "path" / "report.md"
        report = service.generate_weak_points_report(output_path=nested_output_path)
        
        chart_path_str = report.metadata.get('error_type_chart_path')
        assert chart_path_str is not None
        
        chart_path = Path(chart_path_str)
        assert chart_path.parent.exists()
        assert chart_path.exists()
    
    def test_bar_chart_with_custom_output_path(self, service: ReportService, tmp_path: Path):
        """测试使用自定义输出路径时柱状图生成正常。"""
        custom_output = tmp_path / "custom_reports" / "my_report.md"
        report = service.generate_weak_points_report(output_path=custom_output)
        
        chart_path_str = report.metadata.get('error_type_chart_path')
        assert chart_path_str is not None
        
        chart_path = Path(chart_path_str)
        # 图表应该在与报告相同的目录
        assert chart_path.parent == custom_output.parent
        assert chart_path.exists()


class TestBarChartEmptyData:
    """测试空数据情况下的柱状图处理。"""
    
    @pytest.fixture
    def temp_student_dir(self) -> Path:
        """创建空学生目录。"""
        temp_dir = tempfile.mkdtemp()
        base_dir = Path(temp_dir) / "students"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        student_dir = base_dir / "空学生"
        student_dir.mkdir(parents=True)
        
        yield base_dir
        
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def empty_service(self, temp_student_dir: Path) -> ReportService:
        """创建无错题数据的 ReportService 实例。"""
        return ReportService("空学生", base_dir=temp_student_dir)
    
    def test_no_chart_when_no_mistakes(self, empty_service: ReportService, tmp_path: Path):
        """测试无错题时不生成柱状图。"""
        output_path = tmp_path / "empty_report.md"
        report = empty_service.generate_weak_points_report(output_path=output_path)
        
        # 无错题时，图表路径应为 None
        assert report.metadata.get('error_type_chart_path') is None
        assert "暂无错题数据" in report.content
    
    def test_report_content_mentions_no_data(self, empty_service: ReportService, tmp_path: Path):
        """测试空数据报告内容提示。"""
        report = empty_service.generate_weak_points_report()
        
        assert "暂无错题数据" in report.content
        assert "请先录入错题" in report.content


class TestBarChartIntegration:
    """柱状图集成测试。"""
    
    @pytest.fixture
    def temp_student_dir(self) -> Path:
        """创建带丰富测试数据的目录。"""
        temp_dir = tempfile.mkdtemp()
        base_dir = Path(temp_dir) / "students"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        student_dir = base_dir / "集成测试学生"
        student_dir.mkdir(parents=True)
        
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir(parents=True)
        
        # 创建大量错题数据
        test_data = [
            ("m1", "math", "函数", "概念不清"),
            ("m2", "math", "函数", "概念不清"),
            ("m3", "math", "函数", "计算错误"),
            ("m4", "math", "几何", "审题错误"),
            ("m5", "math", "几何", "计算错误"),
            ("m6", "math", "几何", "逻辑错误"),
            ("m7", "physics", "力学", "概念不清"),
            ("m8", "physics", "力学", "公式错误"),
            ("m9", "physics", "电磁学", "计算错误"),
            ("m10", "chemistry", "化学反应", "概念不清"),
        ]
        
        for mistake_id, subject, kp, error_type in test_data:
            test_subdir = mistakes_dir / mistake_id
            test_subdir.mkdir(parents=True)
            (test_subdir / "mistake.md").write_text(
                f"""---
id: {mistake_id}
student: 集成测试学生
subject: {subject}
knowledge-point: {kp}
error-type: {error_type}
created: 2026-04-01
due-date: 2026-04-02
review-round: 0
---

# 题目
""",
                encoding="utf-8"
            )
        
        yield base_dir
        
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_student_dir: Path) -> ReportService:
        """创建 ReportService 实例。"""
        return ReportService("集成测试学生", base_dir=temp_student_dir)
    
    def test_bar_chart_with_multiple_subjects(self, service: ReportService, tmp_path: Path):
        """测试多学科错题的柱状图生成。"""
        output_path = tmp_path / "multi_subject_report.md"
        report = service.generate_weak_points_report(output_path=output_path)
        
        # 验证图表生成
        chart_path_str = report.metadata.get('error_type_chart_path')
        assert chart_path_str is not None
        chart_path = Path(chart_path_str)
        assert chart_path.exists()
        
        # 验证报告包含多个学科
        assert "math" in report.content or "数学" in report.content
        assert "physics" in report.content or "物理" in report.content
        assert "chemistry" in report.content or "化学" in report.content
    
    def test_bar_chart_aggregates_error_types_correctly(self, service: ReportService, tmp_path: Path):
        """测试柱状图正确聚合所有知识点的错误类型。"""
        report = service.generate_weak_points_report(output_path=tmp_path / "report.md")
        
        # 验证报告内容包含所有错误类型的统计
        content = report.content
        assert "概念不清" in content
        assert "计算错误" in content
        assert "审题错误" in content
        assert "逻辑错误" in content
        assert "公式错误" in content
        
        # 验证柱状图章节存在
        assert "## 📊 错误类型分布" in content
    
    def test_report_save_with_chart(self, service: ReportService, tmp_path: Path):
        """测试保存带柱状图的报告。"""
        output_path = tmp_path / "saved_report.md"
        report = service.generate_weak_points_report(output_path=output_path)
        
        # 保存报告
        saved_path = report.save()
        assert saved_path == output_path
        assert saved_path.exists()
        
        # 验证保存的内容包含图表引用
        saved_content = saved_path.read_text(encoding="utf-8")
        assert "![错误类型柱状图]" in saved_content
        assert ".png" in saved_content
    
    def test_metadata_completeness_with_chart(self, service: ReportService, tmp_path: Path):
        """测试带柱状图时元数据完整性。"""
        report = service.generate_weak_points_report(output_path=tmp_path / "report.md")
        
        metadata = report.metadata
        assert 'top_n' in metadata
        assert 'total_mistakes' in metadata
        assert 'knowledge_points_count' in metadata
        assert 'error_type_chart_path' in metadata
        
        assert metadata['total_mistakes'] == 10
        assert metadata['knowledge_points_count'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
