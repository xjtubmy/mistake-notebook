"""
报告服务模块 - 错题本报告生成服务层

提供统一的报告生成接口，封装薄弱知识点分析、月度总结、
综合分析报告的生成逻辑。
"""

from __future__ import annotations

import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from scripts.core.file_ops import find_mistake_files, get_student_dir, parse_frontmatter
from scripts.core import srs
from scripts.core.chart_engine import ChartEngine
from scripts.services.review_service import ReviewService
from scripts import output_naming as out_names


@dataclass
class Report:
    """
    报告数据模型。
    
    表示生成的分析报告，包含元数据和完整内容。
    
    Attributes:
        title: 报告标题
        student: 学生姓名
        report_type: 报告类型（weak-points | monthly | analysis）
        content: 完整的 Markdown 报告内容
        metadata: 报告元数据字典
        generated_at: 报告生成时间
        output_path: 默认输出路径（可选）
    
    Example:
        >>> report = Report(title="分析报告", student="张三", report_type="analysis", content="# 报告内容")
        >>> report.title
        '分析报告'
        >>> report.student
        '张三'
    """
    title: str
    student: str
    report_type: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)
    output_path: Optional[Path] = None
    
    def save(self, output_path: Optional[Path] = None) -> Path:
        """
        保存报告到文件。
        
        Args:
            output_path: 输出路径，如果为 None 则使用默认路径
        
        Returns:
            保存的文件路径
        
        Raises:
            IOError: 写入失败时抛出
        """
        path = output_path or self.output_path
        if path is None:
            raise ValueError("未指定输出路径")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.content, encoding="utf-8")
        return path


@dataclass
class KnowledgePointStats:
    """
    知识点统计数据。
    
    用于薄弱知识点分析，记录单个知识点的详细统计信息。
    
    Attributes:
        name: 知识点名称
        mistake_count: 错题数量
        subjects: 涉及的学科集合
        error_types: 错误类型分布字典
        mistakes: 错题列表（包含详细信息）
    
    Example:
        >>> stats = KnowledgePointStats(name="二次函数", mistake_count=5)
        >>> stats.name
        '二次函数'
        >>> stats.mistake_count
        5
    """
    name: str
    mistake_count: int = 0
    subjects: set = field(default_factory=set)
    error_types: Dict[str, int] = field(default_factory=dict)
    mistakes: List[Dict[str, Any]] = field(default_factory=list)


class ReportService:
    """
    报告生成服务类。
    
    提供错题本各类分析报告的生成服务，包括薄弱知识点分析、
    月度总结报告、综合分析报告等。
    
    Attributes:
        student_name: 学生姓名
        base_dir: 基础目录路径（可选，默认为 data/mistake-notebook/students）
        student_dir: 学生目录路径（自动计算）
    
    Example:
        >>> service = ReportService("张三")
        >>> report = service.generate_weak_points_report(top_n=5)
        >>> print(report.title)
        '薄弱知识点分析报告'
    """
    
    def __init__(self, student_name: str, base_dir: Optional[Path] = None):
        """
        初始化报告服务。
        
        Args:
            student_name: 学生姓名
            base_dir: 基础目录路径，默认为 data/mistake-notebook/students
        
        Example:
            >>> service = ReportService("张三")
            >>> service.student_name
            '张三'
        """
        self.student_name = student_name
        if base_dir is None:
            # 尝试多个可能的数据目录
            possible_paths = [
                Path('/home/ubuntu/clawd/data/mistake-notebook'),
                Path(__file__).parent.parent.parent / 'data' / 'mistake-notebook',
                Path.cwd() / 'data' / 'mistake-notebook',
            ]
            for p in possible_paths:
                if (p / 'students' / student_name).exists():
                    self.base_dir = p
                    break
            else:
                self.base_dir = possible_paths[0]
        else:
            self.base_dir = base_dir
        self.student_dir = get_student_dir(student_name, self.base_dir)
    
    @staticmethod
    def _generate_chart_parallel(
        chart_engine: ChartEngine,
        chart_func: Callable[..., Path],
        data: Any,
        title: str,
        output_path: Path
    ) -> Optional[Path]:
        """
        并行生成单个图表（用于 ThreadPoolExecutor）。
        
        Args:
            chart_engine: 图表引擎实例
            chart_func: 图表生成方法（bar_chart, pie_chart 等）
            data: 图表数据
            title: 图表标题
            output_path: 输出路径
        
        Returns:
            生成的图表路径，失败时返回 None
        """
        try:
            result = chart_func(data=data, title=title, output_path=output_path)
            return result if isinstance(result, Path) else None
        except Exception as e:
            print(f"⚠️ 图表生成失败 {output_path}: {e}")
            return None
    
    def _load_all_mistakes(self, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        加载所有错题数据。
        
        扫描学生目录下的所有错题文件，解析 frontmatter 返回结构化数据。
        
        Args:
            subject: 按学科筛选（可选）
        
        Returns:
            错题数据列表，每项包含 frontmatter 和文件路径信息
        
        Example:
            >>> service = ReportService("张三")
            >>> mistakes = service._load_all_mistakes()
            >>> len(mistakes) >= 0
            True
        """
        mistakes_dir = self.student_dir / "mistakes"
        if not mistakes_dir.exists():
            return []
        
        result: List[Dict[str, Any]] = []
        
        for mistake_file in find_mistake_files(self.student_dir, subject=subject):
            try:
                content = mistake_file.read_text(encoding="utf-8")
                fm = parse_frontmatter(content)
                
                # 添加文件路径信息
                fm['_path'] = mistake_file
                fm['_content'] = content
                result.append(fm)
            except (OSError, UnicodeDecodeError):
                continue
        
        return result
    
    def _analyze_knowledge_points(
        self,
        mistakes: List[Dict[str, Any]]
    ) -> Dict[str, KnowledgePointStats]:
        """
        分析知识点统计数据。
        
        遍历错题列表，按知识点分组统计错题数量、学科分布、错误类型等。
        
        Args:
            mistakes: 错题数据列表
        
        Returns:
            知识点名称到统计数据的映射字典
        
        Example:
            >>> service = ReportService("张三")
            >>> mistakes = service._load_all_mistakes()
            >>> stats = service._analyze_knowledge_points(mistakes)
            >>> isinstance(stats, dict)
            True
        """
        kp_stats: Dict[str, KnowledgePointStats] = {}
        
        for m in mistakes:
            kp = m.get('knowledge-point', '未知')
            subject = m.get('subject', 'unknown')
            error_type = m.get('error-type', '未分类')
            
            if kp not in kp_stats:
                kp_stats[kp] = KnowledgePointStats(name=kp)
            
            stats = kp_stats[kp]
            stats.mistake_count += 1
            stats.subjects.add(subject)
            stats.error_types[error_type] = stats.error_types.get(error_type, 0) + 1
            stats.mistakes.append(m)
        
        return kp_stats
    
    def _get_suggestion_for_count(self, count: int) -> str:
        """
        根据错题数量给出建议等级。
        
        Args:
            count: 错题数量
        
        Returns:
            建议字符串
        
        Example:
            >>> service = ReportService("张三")
            >>> service._get_suggestion_for_count(5)
            '🔴 立即专项突破'
        """
        if count >= 5:
            return "🔴 立即专项突破"
        elif count >= 3:
            return "🟠 重点加强练习"
        else:
            return "🟡 正常复习巩固"
    
    def _get_learning_suggestions(self, error_types: Dict[str, int]) -> List[str]:
        """
        根据错误类型生成学习建议。
        
        Args:
            error_types: 错误类型分布字典
        
        Returns:
            建议列表
        
        Example:
            >>> service = ReportService("张三")
            >>> suggestions = service._get_learning_suggestions({'概念不清': 2})
            >>> len(suggestions) > 0
            True
        """
        suggestions: List[str] = []
        
        if '概念不清' in error_types:
            suggestions.append("📖 回归课本，重新学习相关概念定义")
        if '计算错误' in error_types:
            suggestions.append("✏️ 每天 5 分钟计算练习，养成验算习惯")
        if '审题错误' in error_types:
            suggestions.append("🔍 读题时圈画关键词，读完复述题意")
        if '逻辑错误' in error_types:
            suggestions.append("🧠 画图辅助理解，建立解题模板")
        if '公式错误' in error_types:
            suggestions.append("📝 整理公式卡片，强化记忆和应用")
        if '书写错误' in error_types:
            suggestions.append("✍️ 规范答题格式，注意步骤完整性")
        
        return suggestions
    
    def generate_weak_points_report(
        self,
        top_n: int = 5,
        output_path: Optional[Path] = None
    ) -> Report:
        """
        生成薄弱知识点分析报告。
        
        分析所有错题，找出最薄弱的知识点 TOP N，给出针对性学习建议。
        
        Args:
            top_n: 显示前 N 个薄弱知识点，默认为 5
            output_path: 输出路径（可选）
        
        Returns:
            Report 对象，包含完整的报告内容和元数据
        
        Example:
            >>> service = ReportService("张三")
            >>> report = service.generate_weak_points_report(top_n=5)
            >>> report.report_type
            'weak-points'
            >>> '薄弱知识点' in report.title
            True
        """
        # 加载并分析错题
        mistakes = self._load_all_mistakes()
        if not mistakes:
            # 无错题时返回空报告
            content = f"""---
type: weak-points-report
student: {self.student_name}
generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 🎯 薄弱知识点分析报告

**学生**：{self.student_name}  
**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}  

⚠️ 暂无错题数据，请先录入错题。
"""
            return Report(
                title="薄弱知识点分析报告",
                student=self.student_name,
                report_type="weak-points",
                content=content,
                metadata={'top_n': top_n, 'total_mistakes': 0},
                output_path=output_path or out_names.default_weak_points_path(self.student_name, top_n)
            )
        
        kp_stats = self._analyze_knowledge_points(mistakes)
        sorted_kp = sorted(kp_stats.values(), key=lambda x: -x.mistake_count)[:top_n]
        
        # 生成错误类型柱状图
        chart_path: Optional[Path] = None
        error_type_total: Dict[str, int] = {}
        for stats in kp_stats.values():
            for err_type, count in stats.error_types.items():
                error_type_total[err_type] = error_type_total.get(err_type, 0) + count
        
        if error_type_total:
            # 优化：启用缓存，指定输出目录
            chart_output_dir = output_path.parent if output_path else self.student_dir / "reports"
            chart_output_dir.mkdir(parents=True, exist_ok=True)
            chart_engine = ChartEngine(output_dir=chart_output_dir, use_cache=True)
            chart_filename = f"error_type_bar_{self.student_name}.png"
            chart_path = chart_output_dir / chart_filename
            
            error_type_data = {k: float(v) for k, v in error_type_total.items()}
            chart_engine.bar_chart(
                data=error_type_data,
                title="错误类型分布",
                output_path=chart_path
            )
        
        # 生成报告
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        total_mistakes = sum(s.mistake_count for s in kp_stats.values())
        
        report_lines = [
            f"""---
type: weak-points-report
student: {self.student_name}
generated: {now_str}
---

# 🎯 薄弱知识点分析报告

**学生**：{self.student_name}  
**生成时间**：{now_str}  
**分析错题数**：{total_mistakes} 道

---

## 📊 薄弱知识点 TOP {top_n}

| 排名 | 知识点 | 错题数 | 涉及学科 | 建议 |
|------|--------|--------|---------|------|
""",
        ]
        
        for i, stats in enumerate(sorted_kp, 1):
            subject_str = ', '.join(sorted(stats.subjects))
            suggestion = self._get_suggestion_for_count(stats.mistake_count)
            report_lines.append(
                f"| {i} | {stats.name} | {stats.mistake_count} | {subject_str} | {suggestion} |"
            )
        
        report_lines.append("""
---

## 💡 详细分析

""")
        
        for i, stats in enumerate(sorted_kp, 1):
            report_lines.append(f"""### {i}. {stats.name}

**错题数量**：{stats.mistake_count} 道

**涉及学科**：{', '.join(sorted(stats.subjects))}

**错误类型分布**：
""")
            
            for err_type, count in sorted(stats.error_types.items(), key=lambda x: -x[1]):
                report_lines.append(f"- {err_type}：{count} 道")
            
            report_lines.append("\n**学习建议**：\n")
            suggestions = self._get_learning_suggestions(stats.error_types)
            for sug in suggestions:
                report_lines.append(f"- {sug}")
            
            report_lines.append(f"""
**推荐练习**：
- 找 5-10 道同类题目集中练习
- 整理该知识点的解题思路模板
- 一周后重做这些错题

---

""")
        
        # 添加错误类型柱状图到报告
        if chart_path and chart_path.exists():
            report_lines.append(f"""
## 📊 错误类型分布

![错误类型柱状图]({chart_path})

""")
        
        report_lines.append(f"""## 📅 突破计划

| 周次 | 目标 | 完成标记 |
|------|------|---------|
| 第 1 周 | 攻克第 1 名知识点 | [ ] |
| 第 2 周 | 攻克第 2 名知识点 | [ ] |
| 第 3 周 | 攻克第 3 名知识点 | [ ] |
| 第 4 周 | 巩固复习 | [ ] |

---

**生成于**：{now_str} · mistake-notebook
""")
        
        content = '\n'.join(report_lines)
        
        return Report(
            title="薄弱知识点分析报告",
            student=self.student_name,
            report_type="weak-points",
            content=content,
            metadata={
                'top_n': top_n,
                'total_mistakes': total_mistakes,
                'knowledge_points_count': len(kp_stats),
                'error_type_chart_path': str(chart_path) if chart_path else None
            },
            output_path=output_path or out_names.default_weak_points_path(self.student_name, top_n)
        )
    
    def generate_monthly_report(
        self,
        year_month: str,
        subject: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Report:
        """
        生成月度错题总结报告。
        
        统计指定月份的错题数量、学科分布、错误类型等，生成月度学习报告。
        
        Args:
            year_month: 年月（YYYY-MM 格式）
            subject: 学科筛选（可选）
            output_path: 输出路径（可选）
        
        Returns:
            Report 对象，包含完整的报告内容和元数据
        
        Example:
            >>> service = ReportService("张三")
            >>> report = service.generate_monthly_report("2026-04")
            >>> report.report_type
            'monthly'
            >>> '月度' in report.title
            True
        """
        # 加载错题（按月筛选）
        all_mistakes = self._load_all_mistakes(subject)
        
        # 按月筛选
        mistakes = []
        for m in all_mistakes:
            created = m.get('created', '')
            if created.startswith(year_month):
                mistakes.append(m)
        
        # 统计数据
        total = len(mistakes)
        by_subject: Dict[str, int] = defaultdict(int)
        by_error_type: Dict[str, int] = defaultdict(int)
        by_knowledge_point: Dict[str, int] = defaultdict(int)
        by_difficulty: Dict[str, int] = defaultdict(int)
        
        for m in mistakes:
            by_subject[m.get('subject', 'unknown')] += 1
            by_error_type[m.get('error-type', '未分类')] += 1
            by_knowledge_point[m.get('knowledge-point', '未知')] += 1
            by_difficulty[m.get('difficulty', '⭐')] += 1
        
        # 生成报告
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        ym_label = out_names.chinese_year_month(year_month)
        subject_label = out_names.subject_label_for_filename(subject) if subject else "全科"
        
        report_lines = [
            f"""---
type: monthly-report
student: {self.student_name}
month: {year_month}
subject: {subject if subject else 'all'}
generated: {now_str}
---

# 📊 {ym_label}月度错题总结报告

**学生**：{self.student_name}  
**月份**：{ym_label}  
**学科**：{subject_label}  
**生成时间**：{now_str}

---

## 📈 总体统计

| 指标 | 数值 |
|------|------|
| 错题总数 | {total} |
| 涉及学科 | {len(by_subject)} |
| 平均每日错题 | {total/30:.1f} |

---

## 📚 按学科分布

| 学科 | 错题数 | 占比 |
|------|--------|------|
""",
        ]
        
        for subj, count in sorted(by_subject.items(), key=lambda x: -x[1]):
            pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
            report_lines.append(f"| {subj} | {count} | {pct} |")
        
        report_lines.append("""
---

## ❌ 错误类型分布

| 错误类型 | 数量 | 占比 |
|---------|------|------|
""")
        
        for err_type, count in sorted(by_error_type.items(), key=lambda x: -x[1]):
            pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
            report_lines.append(f"| {err_type} | {count} | {pct} |")
        
        report_lines.append("""
---

## 🎯 知识点掌握情况

| 知识点 | 错题数 | 掌握建议 |
|--------|--------|---------|
""")
        
        for kp, count in sorted(by_knowledge_point.items(), key=lambda x: -x[1])[:10]:
            suggestion = "重点复习" if count >= 3 else ("加强练习" if count >= 2 else "正常")
            report_lines.append(f"| {kp} | {count} | {suggestion} |")
        
        report_lines.append("""
---

## ⭐ 难度分布

| 难度 | 数量 |
|------|------|
""")
        
        for diff in ['⭐⭐⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐', '⭐⭐', '⭐']:
            if by_difficulty.get(diff, 0) > 0:
                report_lines.append(f"| {diff} | {by_difficulty[diff]} |")
        
        # 学习建议
        report_lines.append("""
---

## 💡 学习建议

### 重点突破
""")
        
        top_weak = sorted(by_knowledge_point.items(), key=lambda x: -x[1])[:3]
        if top_weak:
            report_lines.append("")
            for kp, count in top_weak:
                report_lines.append(f"- **{kp}**：{count} 道错题，建议专项练习")
        
        report_lines.append("""
### 错误类型改进
""")
        
        top_error = sorted(by_error_type.items(), key=lambda x: -x[1])[:2]
        if top_error:
            report_lines.append("")
            for err_type, count in top_error:
                if '审题' in err_type:
                    report_lines.append(f"- **{err_type}**：建议读题时圈画关键词")
                elif '计算' in err_type:
                    report_lines.append(f"- **{err_type}**：建议每天 5 分钟计算练习")
                elif '概念' in err_type:
                    report_lines.append(f"- **{err_type}**：建议回归课本，重新学习概念")
                else:
                    report_lines.append(f"- **{err_type}**：针对性练习")
        
        # 生成复习热力图
        heatmap_path: Optional[Path] = None
        try:
            review_service = ReviewService(self.student_name, base_dir=self.base_dir)
            # 获取当月的复习历史
            history = review_service.get_review_history(period=year_month)
            
            if history:
                # 准备热力图数据
                heatmap_data = []
                for entry in history:
                    heatmap_data.append({
                        'date': entry.date.strftime('%Y-%m-%d'),
                        'value': 1,  # 每次复习计数为 1
                        'subject': entry.subject,
                    })
                
                # 生成热力图
                chart_output_dir = output_path.parent if output_path else self.student_dir / "reports"
                chart_output_dir.mkdir(parents=True, exist_ok=True)
                chart_engine = ChartEngine(output_dir=chart_output_dir, use_cache=True)
                heatmap_filename = f"review_heatmap_{year_month}_{self.student_name}.png"
                heatmap_path = chart_output_dir / heatmap_filename
                
                chart_engine.calendar_heatmap(
                    data=heatmap_data,
                    title=f"{ym_label}复习进度热力图",
                    output_path=heatmap_path,
                )
        except Exception:
            # 热力图生成失败不影响报告主体
            pass
        
        report_lines.append(f"""
---

## 📅 下月目标

- [ ] 减少 {top_error[0][0] if top_error else '错误'} 的发生
- [ ] 重点攻克 {top_weak[0][0] if top_weak else '薄弱知识点'}
- [ ] 建立错题复习习惯，每周复习 1 次

---

## 🔥 复习热力图

""")
        
        if heatmap_path and heatmap_path.exists():
            report_lines.append(f"![复习热力图]({heatmap_path})")
        else:
            report_lines.append("💡 暂无复习数据，开始你的第一次复习吧！")
        
        report_lines.append(f"""

---

**生成于**：{now_str} · mistake-notebook
""")
        
        content = '\n'.join(report_lines)
        
        return Report(
            title=f"{ym_label}月度错题总结报告",
            student=self.student_name,
            report_type="monthly",
            content=content,
            metadata={
                'year_month': year_month,
                'subject': subject,
                'total_mistakes': total,
                'heatmap_generated': heatmap_path is not None
            },
            output_path=output_path or out_names.default_monthly_report_path(
                self.student_name, year_month, subject
            )
        )
    
    def generate_analysis_report(
        self,
        subject: Optional[str] = None,
        output_path: Optional[Path] = None
    ) -> Report:
        """
        生成综合分析报告。
        
        扫描所有错题，生成多维度统计分析报告，包括学科分布、
        错误类型、知识点 TOP10、待复习题目等。
        
        Args:
            subject: 学科筛选（可选）
            output_path: 输出路径（可选）
        
        Returns:
            Report 对象，包含完整的报告内容和元数据
        
        Example:
            >>> service = ReportService("张三")
            >>> report = service.generate_analysis_report()
            >>> report.report_type
            'analysis'
            >>> '分析' in report.title
            True
        """
        mistakes = self._load_all_mistakes(subject)
        
        # 统计数据
        total = len(mistakes)
        by_subject: Dict[str, int] = defaultdict(int)
        by_error_type: Dict[str, int] = defaultdict(int)
        by_knowledge_point: Dict[str, int] = defaultdict(int)
        by_unit: Dict[str, int] = defaultdict(int)
        by_status: Dict[str, int] = defaultdict(int)
        by_difficulty: Dict[str, int] = defaultdict(int)
        due_reviews: List[Dict[str, Any]] = []
        
        for m in mistakes:
            by_subject[m.get('subject', 'unknown')] += 1
            by_error_type[m.get('error-type', '未分类')] += 1
            by_knowledge_point[m.get('knowledge-point', '未分类')] += 1
            
            unit_key = f"{m.get('grade', '')}-{m.get('semester', '')}-{m.get('unit', '')}"
            by_unit[unit_key] += 1
            
            by_status[m.get('status', 'unknown')] += 1
            by_difficulty[m.get('difficulty', '⭐')] += 1
            
            # 待复习判断（与 update-review / daily-reminder 一致）
            content = m.get('_content', '')
            fm_sched = srs.parse_frontmatter(content)
            if not srs.due_date_is_scheduled(fm_sched):
                continue
            due_date_str = srs.effective_due_date_for_queue(fm_sched)
            now_str = datetime.now().strftime('%Y-%m-%d')
            if not srs.is_effective_due_on_or_before(due_date_str, now_str):
                continue
            
            due_reviews.append({
                'id': m.get('id', 'unknown'),
                'knowledge_point': m.get('knowledge-point', ''),
                'due_date': due_date_str,
                'review_round': m.get('review-round', 0),
                'path': m.get('_path'),
            })
        
        # 生成学科分布饼图
        chart_path: Optional[Path] = None
        if by_subject and total > 0:
            chart_output_dir = output_path.parent if output_path else self.student_dir / "reports"
            chart_output_dir.mkdir(parents=True, exist_ok=True)
            chart_engine = ChartEngine(output_dir=chart_output_dir, use_cache=True)
            chart_filename = f"subject_distribution_{self.student_name}.png"
            chart_path = chart_output_dir / chart_filename
            
            subject_data = {subj: float(count) for subj, count in by_subject.items()}
            chart_engine.pie_chart(
                data=subject_data,
                title="学科分布",
                output_path=chart_path
            )
        
        # 生成报告
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        subject_label = out_names.subject_label_for_filename(subject) if subject else "全科"
        
        report_lines = [
            f"""---
type: analysis-report
student: {self.student_name}
subject: {subject if subject else 'all'}
generated: {now_str}
---

# 📊 错题分析报告

**学生**：[[../profile|{self.student_name}]]  
**生成时间**：{now_str}  
**筛选条件**：{subject_label}

---

## 📈 总体统计

| 指标 | 数值 |
|------|------|
| 错题总数 | {total} |
| 待复习 | {by_status.get('待复习', 0)} |
| 复习中 | {by_status.get('复习中', 0)} |
| 已掌握 | {by_status.get('已掌握', 0)} |

---

## 📚 按学科分布

| 学科 | 错题数 | 占比 |
|------|--------|------|
""",
        ]
        
        for subj, count in sorted(by_subject.items(), key=lambda x: -x[1]):
            pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
            report_lines.append(f"| {subj} | {count} | {pct} |")
        
        # 添加饼图到报告
        if chart_path and chart_path.exists():
            report_lines.append(f"""
![学科分布饼图]({chart_path})

""")
        
        report_lines.append("""
---

## ❌ 错误类型分布

| 错误类型 | 数量 | 占比 |
|---------|------|------|
""")
        
        for err_type, count in sorted(by_error_type.items(), key=lambda x: -x[1]):
            pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
            report_lines.append(f"| {err_type} | {count} | {pct} |")
        
        report_lines.append("""
---

## 🎯 知识点 TOP10

| 知识点 | 错题数 |
|--------|--------|
""")
        
        for kp, count in sorted(by_knowledge_point.items(), key=lambda x: -x[1])[:10]:
            report_lines.append(f"| {kp} | {count} |")
        
        # 今日待复习
        report_lines.append(f"""
---

## ⏰ 今日待复习 ({len(due_reviews)} 道)

""")
        
        if due_reviews:
            report_lines.append("""| 错题 ID | 知识点 | 复习轮次 | 到期日期 | 链接 |
|--------|--------|---------|---------|------|
""")
            for r in due_reviews[:20]:  # 最多显示 20 道
                path = r.get('path')
                if path:
                    try:
                        rel_path = path.relative_to(
                            Path(f'data/mistake-notebook/students/{self.student_name}')
                        )
                        link = f"[[{rel_path}]]"
                    except ValueError:
                        link = str(path)
                else:
                    link = ""
                report_lines.append(
                    f"| {r['id']} | {r['knowledge_point']} | 第{int(r['review_round'])+1}轮 | {r['due_date']} | {link} |"
                )
        else:
            report_lines.append("🎉 暂无待复习的错题！")
        
        # 难度分布
        report_lines.append("""
---

## ⭐ 难度分布

| 难度 | 数量 |
|------|------|
""")
        
        for diff in ['⭐⭐⭐⭐⭐', '⭐⭐⭐⭐', '⭐⭐⭐', '⭐⭐', '⭐']:
            if by_difficulty.get(diff, 0) > 0:
                report_lines.append(f"| {diff} | {by_difficulty[diff]} |")
        
        report_lines.append("""
---

## 📁 按单元分布

| 单元 | 错题数 |
|------|--------|
""")
        
        for unit, count in sorted(by_unit.items(), key=lambda x: -x[1]):
            report_lines.append(f"| {unit} | {count} |")
        
        report_lines.append(f"""
---

## 🔗 快速链接

- [[../profile|返回学生主页]]
- {f'[[./{subject}/README|返回 {subject_label}]]' if subject else ''}
- [[./README|返回错题总览]]

---

**报告生成时间**：{now_str}
""")
        
        content = '\n'.join(report_lines)
        
        return Report(
            title=f"错题分析报告",
            student=self.student_name,
            report_type="analysis",
            content=content,
            metadata={
                'subject': subject,
                'total_mistakes': total,
                'due_reviews_count': len(due_reviews)
            },
            output_path=output_path or out_names.default_analysis_report_path(
                self.student_name, subject
            )
        )


# 模块级便利函数
def create_report_service(student_name: str, base_dir: Optional[Path] = None) -> ReportService:
    """
    创建报告服务实例的便利函数。
    
    Args:
        student_name: 学生姓名
        base_dir: 基础目录路径（可选）
    
    Returns:
        ReportService 实例
    
    Example:
        >>> service = create_report_service("张三")
        >>> isinstance(service, ReportService)
        True
    """
    return ReportService(student_name, base_dir)
