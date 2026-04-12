#!/usr/bin/env python3
"""
PDF 生成性能基准测试脚本。

用于测量优化前后的 PDF 生成性能，记录基线数据。
"""

import time
import statistics
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime

# 添加项目路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.core.pdf_engine import PDFEngine
from scripts.core.chart_engine import ChartEngine
from scripts.services.report_service import ReportService


from typing import Any, Callable

def measure_time(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[float, Any]:
    """测量函数执行时间（秒）。"""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    return end - start, result


def benchmark_chart_engine() -> dict[str, float]:
    """基准测试：图表引擎性能。"""
    print("\n" + "="*60)
    print("📊 图表引擎性能测试")
    print("="*60)
    
    chart_engine = ChartEngine()
    results = {}
    
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # 饼图
        print("\n测试饼图生成...")
        times = []
        for _ in range(3):
            elapsed, _ = measure_time(
                chart_engine.pie_chart,
                data={"数学": 20.0, "英语": 15.0, "物理": 10.0, "化学": 5.0},
                title="学科分布",
                output_path=output_dir / "pie.png"
            )
            times.append(elapsed)
        avg = statistics.mean(times)
        results['pie_chart'] = avg
        print(f"   ✅ 饼图：{avg*1000:.0f}ms (n=3)")
        
        # 柱状图
        print("\n测试柱状图生成...")
        times = []
        for _ in range(3):
            elapsed, _ = measure_time(
                chart_engine.bar_chart,
                data={"概念不清": 10.0, "计算错误": 15.0, "审题错误": 8.0},
                title="错误类型分布",
                output_path=output_dir / "bar.png"
            )
            times.append(elapsed)
        avg = statistics.mean(times)
        results['bar_chart'] = avg
        print(f"   ✅ 柱状图：{avg*1000:.0f}ms (n=3)")
        
        # 热力图
        print("\n测试热力图生成...")
        times = []
        for _ in range(3):
            elapsed, _ = measure_time(
                chart_engine.calendar_heatmap,
                data=[
                    {"date": "2026-04-01", "value": 5, "subject": "数学"},
                    {"date": "2026-04-02", "value": 3, "subject": "英语"},
                    {"date": "2026-04-03", "value": 7, "subject": "物理"},
                ],
                title="复习热力图",
                output_path=output_dir / "heatmap.png"
            )
            times.append(elapsed)
        avg = statistics.mean(times)
        results['heatmap'] = avg
        print(f"   ✅ 热力图：{avg*1000:.0f}ms (n=3)")
    
    total_chart = sum(results.values())
    print(f"\n📊 图表总耗时：{total_chart*1000:.0f}ms")
    return results


def benchmark_pdf_engine() -> dict[str, float]:
    """基准测试：PDF 引擎性能。"""
    print("\n" + "="*60)
    print("📄 PDF 引擎性能测试")
    print("="*60)
    
    pdf_engine = PDFEngine()
    results = {}
    
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
    <p>这是一段测试内容，用于性能基准测试。</p>
    <table>
        <tr><th>列 1</th><th>列 2</th></tr>
        <tr><td>A</td><td>B</td></tr>
    </table>
</body>
</html>"""
    
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # HTML 转 PDF
        print("\n测试 HTML 转 PDF...")
        times = []
        for i in range(3):
            output_path = output_dir / f"test_{i}.pdf"
            elapsed, _ = measure_time(
                pdf_engine.html_to_pdf,
                html,
                output_path
            )
            times.append(elapsed)
        avg = statistics.mean(times)
        results['html_to_pdf'] = avg
        print(f"   ✅ HTML 转 PDF：{avg*1000:.0f}ms (n=3)")
        
        # Markdown 转 PDF
        print("\n测试 Markdown 转 PDF...")
        markdown = """# 测试标题

这是一段测试内容。

## 子标题

- 列表项 1
- 列表项 2
"""
        times = []
        for i in range(3):
            output_path = output_dir / f"md_{i}.pdf"
            elapsed, _ = measure_time(
                pdf_engine.markdown_to_pdf,
                markdown,
                output_path,
                title="测试"
            )
            times.append(elapsed)
        avg = statistics.mean(times)
        results['markdown_to_pdf'] = avg
        print(f"   ✅ Markdown 转 PDF：{avg*1000:.0f}ms (n=3)")
    
    return results


def benchmark_report_service() -> dict[str, float]:
    """基准测试：报告服务性能（含图表生成）。"""
    print("\n" + "="*60)
    print("📋 报告服务性能测试（含 3 种图表）")
    print("="*60)
    
    report_service = ReportService("张三")
    results = {}
    
    with TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # 薄弱知识点报告（含柱状图）
        print("\n生成薄弱知识点报告...")
        elapsed, report = measure_time(
            report_service.generate_weak_points_report,
            top_n=5,
            output_path=output_dir / "weak_points.md"
        )
        results['weak_points'] = elapsed
        chart_path = report.metadata.get('error_type_chart_path')
        has_chart = chart_path and Path(chart_path).exists()
        print(f"   ✅ 薄弱知识点报告：{elapsed*1000:.0f}ms")
        print(f"      图表：{'✅ 已生成' if has_chart else '❌ 未生成'}")
        
        # 月度报告（含热力图）
        print("\n生成月度报告...")
        elapsed, report = measure_time(
            report_service.generate_monthly_report,
            year_month=datetime.now().strftime("%Y-%m"),
            output_path=output_dir / "monthly.md"
        )
        results['monthly'] = elapsed
        print(f"   ✅ 月度报告：{elapsed*1000:.0f}ms")
        
        # 分析报告（含饼图）
        print("\n生成分析报告...")
        elapsed, report = measure_time(
            report_service.generate_analysis_report,
            output_path=output_dir / "analysis.md"
        )
        results['analysis'] = elapsed
        chart_path = report.metadata.get('subject_chart_path') or report.content.find('subject_distribution')
        print(f"   ✅ 分析报告：{elapsed*1000:.0f}ms")
    
    total_report = sum(results.values())
    print(f"\n📊 报告生成总耗时：{total_report*1000:.0f}ms")
    return results


def main() -> dict[str, Any]:
    """运行所有基准测试。"""
    print("\n" + "="*60)
    print("🚀 PDF 生成性能基准测试")
    print("="*60)
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    overall_start = time.perf_counter()
    
    # 运行测试
    chart_results = benchmark_chart_engine()
    pdf_results = benchmark_pdf_engine()
    report_results = benchmark_report_service()
    
    overall_time = time.perf_counter() - overall_start
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 性能基准汇总")
    print("="*60)
    
    print("\n图表引擎:")
    for name, time_s in chart_results.items():
        print(f"   {name}: {time_s*1000:.0f}ms")
    
    print("\nPDF 引擎:")
    for name, time_s in pdf_results.items():
        print(f"   {name}: {time_s*1000:.0f}ms")
    
    print("\n报告服务:")
    for name, time_s in report_results.items():
        print(f"   {name}: {time_s*1000:.0f}ms")
    
    total_chart = sum(chart_results.values())
    total_report = sum(report_results.values())
    
    print(f"\n⏱️  总耗时：{overall_time:.2f}s")
    print(f"   图表生成：{total_chart*1000:.0f}ms")
    print(f"   报告生成：{total_report*1000:.0f}ms")
    
    # 保存基线数据
    baseline_file = Path(__file__).parent.parent / "tests" / "core" / "baseline_performance.json"
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    baseline_data = {
        "timestamp": datetime.now().isoformat(),
        "chart_engine": {k: v*1000 for k, v in chart_results.items()},  # 转为 ms
        "pdf_engine": {k: v*1000 for k, v in pdf_results.items()},
        "report_service": {k: v*1000 for k, v in report_results.items()},
        "total_ms": overall_time * 1000,
    }
    baseline_file.write_text(json.dumps(baseline_data, indent=2))
    print(f"\n💾 基线数据已保存：{baseline_file}")
    
    return baseline_data


if __name__ == "__main__":
    main()
