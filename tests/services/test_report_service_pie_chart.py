"""
ReportService 饼图生成单元测试模块

测试分析报告中的学科分布饼图生成功能，包括：
- 饼图文件生成
- 饼图嵌入 Markdown 报告
- 饼图嵌入 PDF 报告
"""

import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List

import pytest

from scripts.services.report_service import ReportService
from scripts.core.chart_engine import ChartEngine
from scripts.core.pdf_engine import PDFEngine


class TestPieChartGeneration:
    """测试饼图生成功能"""
    
    @pytest.fixture
    def temp_student_dir(self) -> Path:
        """创建带测试数据的临时学生目录"""
        temp_dir = tempfile.mkdtemp()
        base_dir = Path(temp_dir) / "students"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        student_dir = base_dir / "饼图测试学生"
        student_dir.mkdir(parents=True)
        
        # 创建测试错题数据 - 多个学科
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir(parents=True)
        
        # 创建数学错题 3 道
        for i in range(3):
            math_dir = mistakes_dir / f"math-{i:03d}"
            math_dir.mkdir(parents=True)
            (math_dir / "mistake.md").write_text(
                f"""---
id: math-{i:03d}
student: 饼图测试学生
subject: math
knowledge-point: 二次函数{i}
error-type: 概念不清
created: 2026-04-0{i+1}
due-date: 2026-04-0{i+2}
review-round: 0
difficulty: ⭐⭐
status: 待复习
---

# 题目内容

这是一道数学题目。
""",
                encoding="utf-8"
            )
        
        # 创建物理错题 2 道
        for i in range(2):
            physics_dir = mistakes_dir / f"physics-{i:03d}"
            physics_dir.mkdir(parents=True)
            (physics_dir / "mistake.md").write_text(
                f"""---
id: physics-{i:03d}
student: 饼图测试学生
subject: physics
knowledge-point: 牛顿定律{i}
error-type: 审题错误
created: 2026-04-0{i+1}
due-date: 2026-04-0{i+2}
review-round: 0
difficulty: ⭐⭐⭐
status: 待复习
---

# 物理题目

这是一道物理题目。
""",
                encoding="utf-8"
            )
        
        # 创建化学错题 1 道
        chem_dir = mistakes_dir / "chemistry-001"
        chem_dir.mkdir(parents=True)
        (chem_dir / "mistake.md").write_text(
            """---
id: chemistry-001
student: 饼图测试学生
subject: chemistry
knowledge-point: 化学方程式
error-type: 计算错误
created: 2026-04-01
due-date: 2026-04-02
review-round: 0
difficulty: ⭐⭐
status: 待复习
---

# 化学题目

这是一道化学题目。
""",
            encoding="utf-8"
        )
        
        yield base_dir
        
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_student_dir: Path) -> ReportService:
        """创建 ReportService 实例"""
        return ReportService("饼图测试学生", base_dir=temp_student_dir)
    
    def test_chart_engine_pie_chart(self, tmp_path: Path):
        """测试 ChartEngine 饼图生成"""
        chart_engine = ChartEngine()
        output_path = tmp_path / "test_pie.png"
        
        data = {"math": 3, "physics": 2, "chemistry": 1}
        result_path = chart_engine.pie_chart(
            data=data,
            title="测试饼图",
            output_path=output_path
        )
        
        assert result_path == output_path.resolve()
        assert output_path.exists()
        assert output_path.stat().st_size > 0  # 文件不为空
        assert output_path.suffix == ".png"
    
    def test_analysis_report_generates_pie_chart(self, service: ReportService, tmp_path: Path):
        """测试分析报告生成时创建饼图"""
        output_path = tmp_path / "analysis_report.md"
        
        report = service.generate_analysis_report(output_path=output_path)
        
        # 验证报告生成
        assert report.report_type == "analysis"
        assert report.metadata['total_mistakes'] == 6
        
        # 验证饼图文件生成
        chart_dir = output_path.parent
        chart_files = list(chart_dir.glob("subject_distribution_*.png"))
        assert len(chart_files) > 0, "未生成学科分布饼图"
        
        chart_path = chart_files[0]
        assert chart_path.exists()
        assert chart_path.stat().st_size > 0
    
    def test_pie_chart_embedded_in_markdown(self, service: ReportService, tmp_path: Path):
        """测试饼图嵌入 Markdown 报告"""
        output_path = tmp_path / "analysis_report.md"
        
        report = service.generate_analysis_report(output_path=output_path)
        
        # 验证 Markdown 内容包含图片引用
        assert "![学科分布饼图]" in report.content
        assert ".png" in report.content
        assert "subject_distribution" in report.content
    
    def test_pie_chart_shows_all_subjects(self, service: ReportService, tmp_path: Path):
        """测试饼图包含所有学科"""
        output_path = tmp_path / "analysis_report.md"
        
        report = service.generate_analysis_report(output_path=output_path)
        
        # 验证报告内容包含所有学科
        content = report.content
        assert "math" in content or "数学" in content
        assert "physics" in content or "物理" in content
        assert "chemistry" in content or "化学" in content


class TestPDFWithPieChart:
    """测试 PDF 报告中嵌入饼图"""
    
    @pytest.fixture
    def temp_student_dir(self) -> Path:
        """创建带测试数据的临时学生目录"""
        temp_dir = tempfile.mkdtemp()
        base_dir = Path(temp_dir) / "students"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        student_dir = base_dir / "PDF 测试学生"
        student_dir.mkdir(parents=True)
        
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir(parents=True)
        
        # 创建数学错题 2 道
        for i in range(2):
            math_dir = mistakes_dir / f"math-{i:03d}"
            math_dir.mkdir(parents=True)
            (math_dir / "mistake.md").write_text(
                f"""---
id: math-{i:03d}
student: PDF 测试学生
subject: math
knowledge-point: 函数{i}
error-type: 概念不清
created: 2026-04-0{i+1}
due-date: 2026-04-0{i+2}
review-round: 0
difficulty: ⭐⭐
status: 待复习
---

# 题目

数学题。
""",
                encoding="utf-8"
            )
        
        # 创建物理错题 1 道
        physics_dir = mistakes_dir / "physics-001"
        physics_dir.mkdir(parents=True)
        (physics_dir / "mistake.md").write_text(
            """---
id: physics-001
student: PDF 测试学生
subject: physics
knowledge-point: 力学
error-type: 审题错误
created: 2026-04-01
due-date: 2026-04-02
review-round: 0
difficulty: ⭐⭐
status: 待复习
---

# 题目

物理题。
""",
            encoding="utf-8"
        )
        
        yield base_dir
        
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_student_dir: Path) -> ReportService:
        """创建 ReportService 实例"""
        return ReportService("PDF 测试学生", base_dir=temp_student_dir)
    
    def test_pdf_engine_supports_images(self, tmp_path: Path):
        """测试 PDFEngine 支持图片嵌入"""
        pdf_engine = PDFEngine()
        
        # 创建测试图片
        chart_engine = ChartEngine()
        chart_path = tmp_path / "test_chart.png"
        chart_engine.pie_chart(
            data={"A": 50, "B": 30, "C": 20},
            title="测试",
            output_path=chart_path
        )
        
        # 创建包含图片的 Markdown
        markdown_content = f"""# 测试报告

![测试图表]({chart_path})

这是包含图片的测试报告。
"""
        
        output_path = tmp_path / "test_with_image.pdf"
        
        # 生成 PDF（应该不抛出异常）
        pdf_engine.markdown_to_pdf(
            markdown_content,
            output_path=output_path,
            base_dir=tmp_path
        )
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    
    def test_analysis_report_to_pdf_with_chart(self, service: ReportService, tmp_path: Path):
        """测试分析报告生成 PDF 包含饼图"""
        # 先生成分析报告（包含饼图）
        report_output_dir = tmp_path / "reports"
        report_output_dir.mkdir(parents=True)
        markdown_path = report_output_dir / "analysis.md"
        
        report = service.generate_analysis_report(output_path=markdown_path)
        
        # 验证饼图已生成
        chart_files = list(report_output_dir.glob("subject_distribution_*.png"))
        assert len(chart_files) > 0
        chart_path = chart_files[0]
        
        # 生成 PDF
        pdf_engine = PDFEngine()
        pdf_path = tmp_path / "analysis_report.pdf"
        
        pdf_engine.markdown_to_pdf(
            report.content,
            output_path=pdf_path,
            title=report.title,
            base_dir=report_output_dir
        )
        
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0
        # PDF 应该比纯文本大（因为包含图片）
        assert pdf_path.stat().st_size > 1000


class TestEdgeCases:
    """测试边界情况"""
    
    @pytest.fixture
    def temp_student_dir(self) -> Path:
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        base_dir = Path(temp_dir) / "students"
        base_dir.mkdir(parents=True, exist_ok=True)
        yield base_dir
        shutil.rmtree(temp_dir)
    
    def test_no_pie_chart_when_no_data(self, temp_student_dir: Path):
        """测试无错题数据时不生成饼图"""
        service = ReportService("空学生", base_dir=temp_student_dir)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "analysis.md"
            report = service.generate_analysis_report(output_path=output_path)
            
            # 无数据时不应生成饼图
            chart_files = list(output_path.parent.glob("subject_distribution_*.png"))
            assert len(chart_files) == 0
            
            # 报告内容不应包含图片引用
            assert "![学科分布饼图]" not in report.content
    
    def test_single_subject_no_chart_needed(self, temp_student_dir: Path):
        """测试单学科时饼图生成"""
        student_dir = temp_student_dir / "单学科学生"
        student_dir.mkdir(parents=True)
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir(parents=True)
        
        # 只创建数学错题
        for i in range(3):
            math_dir = mistakes_dir / f"math-{i:03d}"
            math_dir.mkdir(parents=True)
            (math_dir / "mistake.md").write_text(
                f"""---
id: math-{i:03d}
student: 单学科学生
subject: math
knowledge-point: 知识点{i}
error-type: 概念不清
created: 2026-04-0{i+1}
due-date: 2026-04-0{i+2}
review-round: 0
---

# 题目
""",
                encoding="utf-8"
            )
        
        service = ReportService("单学科学生", base_dir=temp_student_dir)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "analysis.md"
            report = service.generate_analysis_report(output_path=output_path)
            
            # 单学科也会生成饼图（虽然只有一个扇区）
            chart_files = list(output_path.parent.glob("subject_distribution_*.png"))
            assert len(chart_files) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
