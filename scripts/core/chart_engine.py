"""
图表引擎 - 使用 Plotly 生成统计图表。

提供 ChartEngine 类，封装饼图、柱状图、折线图的生成逻辑，
支持导出为 PNG 格式，供错题统计分析和报告生成使用。
"""

from __future__ import annotations

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
