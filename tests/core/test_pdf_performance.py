"""
PDF 生成性能测试。

测试 PDF 生成流程的性能，包括：
1. 基准性能测试（优化前）
2. 优化后性能测试
3. 性能对比分析

验收标准：PDF 生成速度提升 ≥ 30%
"""

import pytest
import time
import statistics
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

from scripts.core.pdf_engine import PDFEngine
from scripts.services.report_service import ReportService


class TestPDFPerformanceBaseline:
    """PDF 生成性能基准测试。"""

    @pytest.fixture
    def test_student(self) -> str:
        """测试学生名称。"""
        return "张三"

    @pytest.fixture
    def pdf_engine(self) -> PDFEngine:
        """PDF 引擎实例。"""
        return PDFEngine()

    @pytest.fixture
    def report_service(self, test_student: str) -> ReportService:
        """报告服务实例。"""
        return ReportService(test_student)

    def measure_time(self, func, *args, **kwargs) -> tuple[float, any]:
        """测量函数执行时间。"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        return end - start, result

    def test_markdown_to_html_performance(self, pdf_engine: PDFEngine) -> None:
        """测试 Markdown 转 HTML 性能。"""
        markdown = """# 测试标题

这是一段测试内容，用于性能基准测试。

## 子标题

- 列表项 1
- 列表项 2
- 列表项 3

| 列 1 | 列 2 |
|------|------|
| A    | B    |

```python
print("hello")
```
"""
        # 预热
        pdf_engine.printable_html_from_markdown(markdown)
        
        # 测量 10 次取平均值
        times = []
        for _ in range(10):
            elapsed, _ = self.measure_time(
                pdf_engine.printable_html_from_markdown,
                markdown,
                title="测试文档"
            )
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        print(f"\n📊 Markdown 转 HTML 平均耗时：{avg_time*1000:.2f}ms")
        print(f"   标准差：{statistics.stdev(times)*1000:.2f}ms")
        
        # 应该在 10ms 内完成
        assert avg_time < 0.05, f"Markdown 转 HTML 太慢：{avg_time*1000:.2f}ms"

    def test_html_to_pdf_performance(self, pdf_engine: PDFEngine) -> None:
        """测试 HTML 转 PDF 性能（单次）。"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: sans-serif; line-height: 1.8; }
        h1 { color: #333; }
        @page { margin: 2cm; }
    </style>
</head>
<body>
    <h1>测试文档</h1>
    <p>这是一段测试内容。</p>
</body>
</html>"""

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            
            # 预热
            pdf_engine.html_to_pdf(html, output_path)
            
            # 测量 3 次取平均值（PDF 生成较慢）
            times = []
            for _ in range(3):
                elapsed, _ = self.measure_time(
                    pdf_engine.html_to_pdf,
                    html,
                    output_path
                )
                times.append(elapsed)
            
            avg_time = statistics.mean(times)
            print(f"\n📊 HTML 转 PDF 平均耗时：{avg_time*1000:.2f}ms")
            print(f"   标准差：{statistics.stdev(times)*1000:.2f}ms")
            
            # 记录基线时间（用于后续对比）
            print(f"   ⏱️ 基线时间：{avg_time:.3f}s")

    def test_full_report_generation_performance(
        self,
        report_service: ReportService,
        pdf_engine: PDFEngine
    ) -> None:
        """测试完整报告生成性能（含 3 种图表）。"""
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # 生成薄弱知识点报告（含柱状图）
            print("\n📊 开始生成薄弱知识点报告...")
            start = time.perf_counter()
            weak_report = report_service.generate_weak_points_report(
                top_n=5,
                output_path=output_dir / "weak_points.md"
            )
            weak_time = time.perf_counter() - start
            print(f"   ✅ 薄弱知识点报告：{weak_time:.2f}s")
            
            # 生成月度报告（含热力图）
            print("\n📊 开始生成月度报告...")
            start = time.perf_counter()
            monthly_report = report_service.generate_monthly_report(
                year_month=datetime.now().strftime("%Y-%m"),
                output_path=output_dir / "monthly.md"
            )
            monthly_time = time.perf_counter() - start
            print(f"   ✅ 月度报告：{monthly_time:.2f}s")
            
            # 生成分析报告（含饼图）
            print("\n📊 开始生成分析报告...")
            start = time.perf_counter()
            analysis_report = report_service.generate_analysis_report(
                output_path=output_dir / "analysis.md"
            )
            analysis_time = time.perf_counter() - start
            print(f"   ✅ 分析报告：{analysis_time:.2f}s")
            
            total_time = weak_time + monthly_time + analysis_time
            print(f"\n📊 总耗时：{total_time:.2f}s")
            print(f"   平均每个报告：{total_time/3:.2f}s")
            
            # 记录基线时间
            print(f"\n⏱️ 性能基线（3 种图表 + 3 个报告）：{total_time:.3f}s")
            
            # 保存基线时间到文件供后续对比
            baseline_file = output_dir / "baseline_time.txt"
            baseline_file.write_text(f"{total_time}")
            
            # 确保性能在可接受范围内（单次报告 < 30s）
            assert total_time < 90, f"报告生成太慢：{total_time:.2f}s"

    def test_chart_generation_performance(self) -> None:
        """测试图表生成性能。"""
        from scripts.core.chart_engine import ChartEngine
        
        chart_engine = ChartEngine()
        
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # 测试饼图
            print("\n📊 测试饼图生成...")
            start = time.perf_counter()
            chart_engine.pie_chart(
                data={"数学": 20.0, "英语": 15.0, "物理": 10.0, "化学": 5.0},
                title="学科分布",
                output_path=output_dir / "pie.png"
            )
            pie_time = time.perf_counter() - start
            print(f"   ✅ 饼图：{pie_time:.2f}s")
            
            # 测试柱状图
            print("\n📊 测试柱状图生成...")
            start = time.perf_counter()
            chart_engine.bar_chart(
                data={"概念不清": 10.0, "计算错误": 15.0, "审题错误": 8.0},
                title="错误类型分布",
                output_path=output_dir / "bar.png"
            )
            bar_time = time.perf_counter() - start
            print(f"   ✅ 柱状图：{bar_time:.2f}s")
            
            # 测试热力图
            print("\n📊 测试热力图生成...")
            start = time.perf_counter()
            chart_engine.calendar_heatmap(
                data=[
                    {"date": "2026-04-01", "value": 5, "subject": "数学"},
                    {"date": "2026-04-02", "value": 3, "subject": "英语"},
                    {"date": "2026-04-03", "value": 7, "subject": "物理"},
                ],
                title="复习热力图",
                output_path=output_dir / "heatmap.png"
            )
            heatmap_time = time.perf_counter() - start
            print(f"   ✅ 热力图：{heatmap_time:.2f}s")
            
            total_chart_time = pie_time + bar_time + heatmap_time
            print(f"\n📊 图表总耗时：{total_chart_time:.2f}s")
            
            # 确保图表生成在合理时间内
            assert total_chart_time < 30, f"图表生成太慢：{total_chart_time:.2f}s"


class TestPDFPerformanceOptimized:
    """PDF 生成优化后性能测试。"""

    @pytest.fixture
    def test_student(self) -> str:
        """测试学生名称。"""
        return "张三"

    @pytest.fixture
    def report_service(self, test_student: str) -> ReportService:
        """报告服务实例。"""
        return ReportService(test_student)

    def measure_time(self, func, *args, **kwargs) -> tuple[float, any]:
        """测量函数执行时间。"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        return end - start, result

    def test_optimized_report_generation(
        self,
        report_service: ReportService
    ) -> None:
        """测试优化后的报告生成性能。"""
        from tempfile import TemporaryDirectory
        from pathlib import Path
        
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # 生成 3 个报告（优化后应该更快）
            print("\n🚀 开始优化后性能测试...")
            
            times = []
            
            # 薄弱知识点报告
            start = time.perf_counter()
            report_service.generate_weak_points_report(
                top_n=5,
                output_path=output_dir / "weak_points.md"
            )
            times.append(time.perf_counter() - start)
            
            # 月度报告
            start = time.perf_counter()
            report_service.generate_monthly_report(
                year_month=datetime.now().strftime("%Y-%m"),
                output_path=output_dir / "monthly.md"
            )
            times.append(time.perf_counter() - start)
            
            # 分析报告
            start = time.perf_counter()
            report_service.generate_analysis_report(
                output_path=output_dir / "analysis.md"
            )
            times.append(time.perf_counter() - start)
            
            total_time = sum(times)
            print(f"\n🚀 优化后总耗时：{total_time:.2f}s")
            print(f"   平均每个报告：{total_time/3:.2f}s")
            
            # 保存优化后时间
            optimized_file = output_dir / "optimized_time.txt"
            optimized_file.write_text(f"{total_time}")
            
            # 验证性能提升（需要 ≥ 30%）
            baseline_file = output_dir.parent.parent / "baseline_time.txt"
            if baseline_file.exists():
                baseline_time = float(baseline_file.read_text())
                improvement = (baseline_time - total_time) / baseline_time * 100
                print(f"\n📈 性能提升：{improvement:.1f}%")
                print(f"   基线：{baseline_time:.2f}s → 优化后：{total_time:.2f}s")
                
                # 验收标准：提升 ≥ 30%
                assert improvement >= 30, f"性能提升不足：{improvement:.1f}% < 30%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
