"""
图表引擎 - 使用 Plotly 生成统计图表。

提供 ChartEngine 类，封装饼图、柱状图、折线图、热力图的生成逻辑，
支持导出为 PNG 格式，供错题统计分析和报告生成使用。
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import plotly.graph_objects as go
from plotly.io import to_image


class ChartEngine:
    """
    图表引擎。

    使用 Plotly 库生成各类统计图表，支持饼图、柱状图、折线图，
    并可导出为 PNG 格式用于报告和文档。

    Attributes:
        output_dir: 默认输出目录，用于存储生成的图表文件。
    """

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        """
        初始化图表引擎。

        Args:
            output_dir: 默认输出目录。如果为 None，则使用当前工作目录。
        """
        self.output_dir = output_dir or Path.cwd()

    def pie_chart(
        self, data: Dict[str, float], title: str, output_path: Path
    ) -> Path:
        """
        生成饼图。

        适用于展示分类数据的占比分布，如错题类型分布、知识点分布等。

        Args:
            data: 字典格式数据，键为分类标签，值为数值。
            title: 图表标题。
            output_path: 输出文件路径（PNG 格式）。

        Returns:
            生成的 PNG 文件的绝对路径。
        """
        labels = list(data.keys())
        values = list(data.values())

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    textinfo="label+percent",
                    textfont_size=12,
                )
            ]
        )
        fig.update_layout(
            title={"text": title, "x": 0.5, "font_size": 16},
            legend={"orientation": "h", "y": -0.1},
            margin={"t": 60, "b": 40, "l": 20, "r": 20},
        )

        return self.save_as_png(fig, output_path)

    def bar_chart(
        self, data: Dict[str, float], title: str, output_path: Path
    ) -> Path:
        """
        生成柱状图。

        适用于展示分类数据的对比，如各科目错题数量对比、周错题趋势等。

        Args:
            data: 字典格式数据，键为分类标签，值为数值。
            title: 图表标题。
            output_path: 输出文件路径（PNG 格式）。

        Returns:
            生成的 PNG 文件的绝对路径。
        """
        labels = list(data.keys())
        values = list(data.values())

        fig = go.Figure(
            data=[go.Bar(x=labels, y=values, marker_color="steelblue", text=values)]
        )
        fig.update_layout(
            title={"text": title, "x": 0.5, "font_size": 16},
            xaxis={"title": "类别", "tickangle": -45},
            yaxis={"title": "数量"},
            showlegend=False,
            margin={"t": 60, "b": 80, "l": 60, "r": 20},
        )

        return self.save_as_png(fig, output_path)

    def line_chart(
        self, data: List[Tuple[str, float]], title: str, output_path: Path
    ) -> Path:
        """
        生成折线图。

        适用于展示时间序列数据的趋势变化，如错题数量周趋势、正确率变化等。

        Args:
            data: 列表格式数据，每个元素为 (x 轴标签，y 轴数值) 的元组。
            title: 图表标题。
            output_path: 输出文件路径（PNG 格式）。

        Returns:
            生成的 PNG 文件的绝对路径。
        """
        x_values = [item[0] for item in data]
        y_values = [item[1] for item in data]

        fig = go.Figure(
            data=[
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode="lines+markers",
                    line={"width": 3, "color": "steelblue"},
                    marker={"size": 8},
                    text=y_values,
                    textposition="top center",
                )
            ]
        )
        fig.update_layout(
            title={"text": title, "x": 0.5, "font_size": 16},
            xaxis={"title": "时间", "tickangle": -45},
            yaxis={"title": "数值"},
            showlegend=False,
            margin={"t": 60, "b": 80, "l": 60, "r": 20},
        )

        return self.save_as_png(fig, output_path)

    def calendar_heatmap(
        self,
        data: List[Dict[str, any]],
        title: str,
        output_path: Path,
        year: Optional[int] = None
    ) -> Path:
        """
        生成日历热力图。

        适用于展示复习进度、错题录入频率等时间分布数据。
        使用 Plotly 的 Calendar Heatmap 实现。

        Args:
            data: 列表格式数据，每个元素为字典，包含：
                  - date: 日期字符串 (YYYY-MM-DD) 或 date 对象
                  - value: 数值（如复习次数、错题数量）
                  - subject: 学科（可选，用于颜色分类）
            title: 图表标题。
            output_path: 输出文件路径（PNG 格式）。
            year: 指定年份，默认为当前年份。

        Returns:
            生成的 PNG 文件的绝对路径。

        Example:
            >>> engine = ChartEngine()
            >>> data = [
            ...     {"date": "2026-04-01", "value": 5, "subject": "math"},
            ...     {"date": "2026-04-02", "value": 3, "subject": "chinese"},
            ... ]
            >>> engine.calendar_heatmap(data, "复习热力图", Path("heatmap.png"))
        """
        if year is None:
            year = date.today().year

        # 准备数据
        dates = []
        values = []
        subjects = []

        for item in data:
            date_val = item.get('date')
            if isinstance(date_val, str):
                try:
                    date_val = date.fromisoformat(date_val)
                except ValueError:
                    continue
            elif isinstance(date_val, date):
                pass
            else:
                continue

            # 只保留指定年份的数据
            if date_val.year != year:
                continue

            dates.append(date_val)
            values.append(item.get('value', 0))
            subjects.append(item.get('subject', 'unknown'))

        if not dates:
            # 无数据时生成空图表
            fig = go.Figure()
            fig.add_annotation(
                text="暂无数据",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font_size=20
            )
            fig.update_layout(
                title={"text": title, "x": 0.5, "font_size": 16},
                xaxis={"visible": False},
                yaxis={"visible": False},
            )
            return self.save_as_png(fig, output_path)

        # 按学科分组计算最大值为颜色标尺
        subject_values: Dict[str, List[float]] = {}
        for i, subj in enumerate(subjects):
            if subj not in subject_values:
                subject_values[subj] = []
            subject_values[subj].append(values[i])

        # 使用连续颜色标尺（绿色系表示复习强度）
        # 颜色映射：值越高颜色越深
        max_value = max(values) if values else 1
        min_value = min(values) if values else 0

        # 创建日历热力图
        fig = go.Figure(
            data=go.Heatmap(
                x=[d.strftime('%Y-%m-%d') for d in dates],
                y=[subj_map.get(s, s) for s, subj_map in zip(subjects, [{}]*len(subjects))],
                z=values,
                colorscale='Greens',
                showscale=True,
                colorbar={"title": "数量"},
            )
        )

        # 更简单的实现：使用散点图模拟日历热力图
        # 因为 Plotly 的 calendar heatmap 需要特定格式
        # 改用：按日期分组的柱状图或简单的热力图

        # 重新实现：使用简单的日期 vs 学科热力图
        # 先聚合数据：按日期和学科统计
        date_subject_values: Dict[Tuple[str, str], float] = {}
        all_dates = set()
        all_subjects = set()

        for i, d in enumerate(dates):
            date_str = d.strftime('%m-%d')
            subj = subjects[i]
            key = (date_str, subj)
            date_subject_values[key] = date_subject_values.get(key, 0) + values[i]
            all_dates.add(date_str)
            all_subjects.add(subj)

        # 排序
        sorted_dates = sorted(all_dates)
        sorted_subjects = sorted(all_subjects)

        # 构建热力图矩阵
        z_data = []
        for subj in sorted_subjects:
            row = []
            for d in sorted_dates:
                row.append(date_subject_values.get((d, subj), 0))
            z_data.append(row)

        fig = go.Figure(
            data=go.Heatmap(
                z=z_data,
                x=sorted_dates,
                y=sorted_subjects,
                colorscale='YlGn',
                showscale=True,
                colorbar={"title": "复习量"},
                text=z_data,
                texttemplate="%{text}",
                textfont={"size": 10},
            )
        )

        fig.update_layout(
            title={"text": title, "x": 0.5, "font_size": 16},
            xaxis={"title": "日期", "tickangle": -45},
            yaxis={"title": "学科"},
            margin={"t": 60, "b": 80, "l": 80, "r": 40},
        )

        return self.save_as_png(fig, output_path)

    def save_as_png(self, fig: go.Figure, output_path: Path) -> Path:
        """
        将 Plotly 图表保存为 PNG 文件。

        使用 kaleido 引擎进行静态图片导出，确保中文字体正常渲染。

        Args:
            fig: Plotly Figure 对象。
            output_path: 输出文件路径。

        Returns:
            生成的 PNG 文件的绝对路径。

        Raises:
            ValueError: 当输出路径不是 PNG 格式时。
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix.lower() != ".png":
            raise ValueError(f"输出路径必须是 PNG 格式：{output_path}")

        img_bytes = to_image(fig, format="png", width=800, height=600, scale=2)
        output_path.write_bytes(img_bytes)

        resolved = str(output_path.resolve())
        print(f"✅ 已生成图表：{resolved}")
        print(f"OUTPUT_PATH={resolved}")

        return output_path.resolve()
