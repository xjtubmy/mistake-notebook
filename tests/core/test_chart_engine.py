"""
ChartEngine 单元测试。

测试图表引擎的核心功能，包括初始化、饼图、柱状图、折线图、热力图生成
以及 PNG 文件导出验证。
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

from scripts.core.chart_engine import ChartEngine


class TestChartEngineInit:
    """测试 ChartEngine 初始化。"""

    def test_init_with_no_output_dir(self) -> None:
        """测试不提供输出目录时使用当前工作目录。"""
        engine = ChartEngine()
        assert engine.output_dir == Path.cwd()

    def test_init_with_custom_output_dir(self, tmp_path: Path) -> None:
        """测试提供自定义输出目录。"""
        engine = ChartEngine(output_dir=tmp_path)
        assert engine.output_dir == tmp_path

    def test_init_creates_directory_if_needed(self, tmp_path: Path) -> None:
        """测试初始化时不会主动创建目录（目录在保存时创建）。"""
        new_dir = tmp_path / "new_charts"
        engine = ChartEngine(output_dir=new_dir)
        assert engine.output_dir == new_dir
        # 目录尚未创建，直到实际保存文件


class TestPieChart:
    """测试饼图生成功能。"""

    def test_pie_chart_basic(self, tmp_path: Path) -> None:
        """测试基本饼图生成。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: Dict[str, float] = {"代数": 10.0, "几何": 15.0, "概率": 5.0}
        output_path = tmp_path / "pie_test.png"

        result_path = engine.pie_chart(data, title="错题类型分布", output_path=output_path)

        assert result_path.exists()
        assert result_path.is_file()
        assert result_path.suffix.lower() == ".png"
        assert result_path.stat().st_size > 0

    def test_pie_chart_single_category(self, tmp_path: Path) -> None:
        """测试单分类饼图。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: Dict[str, float] = {"代数": 100.0}
        output_path = tmp_path / "pie_single.png"

        result_path = engine.pie_chart(data, title="单一类型", output_path=output_path)

        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_pie_chart_creates_parent_dirs(self, tmp_path: Path) -> None:
        """测试饼图保存时自动创建父目录。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: Dict[str, float] = {"A": 1.0, "B": 2.0}
        output_path = tmp_path / "subdir" / "nested" / "pie.png"

        result_path = engine.pie_chart(data, title="嵌套目录", output_path=output_path)

        assert result_path.exists()
        assert result_path.parent.exists()


class TestBarChart:
    """测试柱状图生成功能。"""

    def test_bar_chart_basic(self, tmp_path: Path) -> None:
        """测试基本柱状图生成。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: Dict[str, float] = {"周一": 5.0, "周二": 8.0, "周三": 3.0, "周四": 10.0}
        output_path = tmp_path / "bar_test.png"

        result_path = engine.bar_chart(data, title="周错题数量", output_path=output_path)

        assert result_path.exists()
        assert result_path.is_file()
        assert result_path.suffix.lower() == ".png"
        assert result_path.stat().st_size > 0

    def test_bar_chart_empty_data(self, tmp_path: Path) -> None:
        """测试空数据柱状图（应能正常生成但无内容）。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: Dict[str, float] = {}
        output_path = tmp_path / "bar_empty.png"

        result_path = engine.bar_chart(data, title="空数据", output_path=output_path)

        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_bar_chart_many_categories(self, tmp_path: Path) -> None:
        """测试多分类柱状图。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: Dict[str, float] = {
            f"知识点{i}": float(i * 2) for i in range(1, 11)
        }
        output_path = tmp_path / "bar_many.png"

        result_path = engine.bar_chart(data, title="多知识点", output_path=output_path)

        assert result_path.exists()
        assert result_path.stat().st_size > 0


class TestLineChart:
    """测试折线图生成功能。"""

    def test_line_chart_basic(self, tmp_path: Path) -> None:
        """测试基本折线图生成。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: List[Tuple[str, float]] = [
            ("第 1 周", 10.0),
            ("第 2 周", 15.0),
            ("第 3 周", 12.0),
            ("第 4 周", 20.0),
        ]
        output_path = tmp_path / "line_test.png"

        result_path = engine.line_chart(data, title="错题趋势", output_path=output_path)

        assert result_path.exists()
        assert result_path.is_file()
        assert result_path.suffix.lower() == ".png"
        assert result_path.stat().st_size > 0

    def test_line_chart_single_point(self, tmp_path: Path) -> None:
        """测试单数据点折线图。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: List[Tuple[str, float]] = [("第 1 周", 10.0)]
        output_path = tmp_path / "line_single.png"

        result_path = engine.line_chart(data, title="单周数据", output_path=output_path)

        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_line_chart_trend_data(self, tmp_path: Path) -> None:
        """测试趋势数据折线图。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: List[Tuple[str, float]] = [
            ("1 月", 50.0),
            ("2 月", 55.0),
            ("3 月", 48.0),
            ("4 月", 60.0),
            ("5 月", 65.0),
            ("6 月", 70.0),
        ]
        output_path = tmp_path / "line_trend.png"

        result_path = engine.line_chart(data, title="月度趋势", output_path=output_path)

        assert result_path.exists()
        assert result_path.stat().st_size > 0


class TestSaveAsPng:
    """测试 PNG 保存功能。"""

    def test_save_as_png_invalid_extension(self, tmp_path: Path) -> None:
        """测试非 PNG 扩展名抛出异常。"""
        engine = ChartEngine(output_dir=tmp_path)
        import plotly.graph_objects as go

        fig = go.Figure()
        output_path = tmp_path / "chart.jpg"

        with pytest.raises(ValueError, match="PNG"):
            engine.save_as_png(fig, output_path)

    def test_save_as_png_creates_directory(self, tmp_path: Path) -> None:
        """测试保存时自动创建目录。"""
        engine = ChartEngine(output_dir=tmp_path)
        import plotly.graph_objects as go

        fig = go.Figure()
        output_path = tmp_path / "deep" / "nested" / "path" / "chart.png"

        result_path = engine.save_as_png(fig, output_path)

        assert result_path.exists()
        assert result_path.parent.exists()

    def test_save_as_png_returns_absolute_path(self, tmp_path: Path) -> None:
        """测试返回绝对路径。"""
        engine = ChartEngine(output_dir=tmp_path)
        import plotly.graph_objects as go

        fig = go.Figure()
        output_path = tmp_path / "chart.png"

        result_path = engine.save_as_png(fig, output_path)

        assert result_path.is_absolute()


class TestCalendarHeatmap:
    """测试日历热力图生成功能。"""

    def test_calendar_heatmap_basic(self, tmp_path: Path) -> None:
        """测试基本日历热力图生成。"""
        engine = ChartEngine(output_dir=tmp_path)
        data = [
            {"date": "2026-04-01", "value": 5, "subject": "math"},
            {"date": "2026-04-02", "value": 3, "subject": "chinese"},
            {"date": "2026-04-03", "value": 7, "subject": "math"},
            {"date": "2026-04-05", "value": 2, "subject": "english"},
        ]
        output_path = tmp_path / "heatmap_test.png"

        result_path = engine.calendar_heatmap(
            data=data, title="复习热力图", output_path=output_path
        )

        assert result_path.exists()
        assert result_path.is_file()
        assert result_path.suffix.lower() == ".png"
        assert result_path.stat().st_size > 0

    def test_calendar_heatmap_empty_data(self, tmp_path: Path) -> None:
        """测试空数据热力图。"""
        engine = ChartEngine(output_dir=tmp_path)
        data: List[Dict[str, any]] = []
        output_path = tmp_path / "heatmap_empty.png"

        result_path = engine.calendar_heatmap(
            data=data, title="空数据", output_path=output_path
        )

        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_calendar_heatmap_year_filter(self, tmp_path: Path) -> None:
        """测试年份过滤。"""
        engine = ChartEngine(output_dir=tmp_path)
        data = [
            {"date": "2025-04-01", "value": 5, "subject": "math"},
            {"date": "2026-04-02", "value": 3, "subject": "chinese"},
            {"date": "2026-04-03", "value": 7, "subject": "math"},
        ]
        output_path = tmp_path / "heatmap_year.png"

        # 只保留 2026 年的数据
        result_path = engine.calendar_heatmap(
            data=data, title="2026 年热力图", output_path=output_path, year=2026
        )

        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_calendar_heatmap_date_objects(self, tmp_path: Path) -> None:
        """测试使用 date 对象作为日期。"""
        engine = ChartEngine(output_dir=tmp_path)
        data = [
            {"date": date(2026, 4, 1), "value": 5, "subject": "math"},
            {"date": date(2026, 4, 2), "value": 3, "subject": "chinese"},
        ]
        output_path = tmp_path / "heatmap_date_obj.png"

        result_path = engine.calendar_heatmap(
            data=data, title="日期对象测试", output_path=output_path
        )

        assert result_path.exists()
        assert result_path.stat().st_size > 0

    def test_calendar_heatmap_creates_parent_dirs(self, tmp_path: Path) -> None:
        """测试热力图保存时自动创建父目录。"""
        engine = ChartEngine(output_dir=tmp_path)
        data = [
            {"date": "2026-04-01", "value": 5, "subject": "math"},
        ]
        output_path = tmp_path / "subdir" / "nested" / "heatmap.png"

        result_path = engine.calendar_heatmap(
            data=data, title="嵌套目录", output_path=output_path
        )

        assert result_path.exists()
        assert result_path.parent.exists()

    def test_calendar_heatmap_multiple_subjects(self, tmp_path: Path) -> None:
        """测试多学科热力图。"""
        engine = ChartEngine(output_dir=tmp_path)
        data = [
            {"date": "2026-04-01", "value": 2, "subject": "math"},
            {"date": "2026-04-01", "value": 3, "subject": "chinese"},
            {"date": "2026-04-02", "value": 1, "subject": "english"},
            {"date": "2026-04-02", "value": 4, "subject": "math"},
            {"date": "2026-04-03", "value": 2, "subject": "chinese"},
        ]
        output_path = tmp_path / "heatmap_multi_subj.png"

        result_path = engine.calendar_heatmap(
            data=data, title="多学科热力图", output_path=output_path
        )

        assert result_path.exists()
        assert result_path.stat().st_size > 0
