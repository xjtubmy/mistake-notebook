#!/usr/bin/env python3
"""
WikiService 服务层 - 知识库页面管理服务

提供知识点页面的创建、迁移、检查等功能，
封装 migrate-to-wiki 和 lint-wiki 的核心逻辑。
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from collections import defaultdict
import re

from scripts.core.models import Mistake, Subject
from scripts.core.file_ops import find_mistake_files, get_student_dir, read_mistake_file


@dataclass
class MigrationResult:
    """迁移结果数据类
    
    记录批量迁移操作的统计信息和详细结果。
    
    Attributes:
        total_mistakes: 扫描的错题总数
        total_concepts: 涉及的知识点数量
        created_pages: 创建的知识点页面数
        added_links: 添加的链接数
        skipped: 跳过的错题数（已关联）
        concept_details: 各知识点的详细统计
        report_path: 生成的报告路径
        success: 迁移是否成功
        error_message: 错误信息（如果有）
    """
    total_mistakes: int = 0
    total_concepts: int = 0
    created_pages: int = 0
    added_links: int = 0
    skipped: int = 0
    concept_details: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    report_path: Optional[Path] = None
    success: bool = True
    error_message: str = ""


@dataclass
class LintIssue:
    """检查问题数据类
    
    表示知识库健康检查中发现的单个问题。
    
    Attributes:
        issue_type: 问题类型（orphan, unlinked, outdated, missing_frontmatter）
        path: 相关文件路径
        message: 问题描述
        severity: 严重程度（error, warning, info）
        suggestion: 修复建议
    """
    issue_type: str
    path: Path
    message: str
    severity: str = "warning"
    suggestion: str = ""


@dataclass
class LintReport:
    """知识库检查报告数据类
    
    汇总知识库健康检查的所有结果。
    
    Attributes:
        student: 学生姓名
        check_time: 检查时间
        issues: 所有发现的问题列表
        orphans: 孤儿页面列表
        unlinked: 未关联错题列表
        outdated: 过期页面列表
        missing_frontmatter: 缺失 frontmatter 的文件列表
        health_score: 健康评分（0-100）
        summary: 摘要统计
    """
    student: str = ""
    check_time: datetime = field(default_factory=datetime.now)
    issues: List[LintIssue] = field(default_factory=list)
    orphans: List[Path] = field(default_factory=list)
    unlinked: List[Path] = field(default_factory=list)
    outdated: List[Path] = field(default_factory=list)
    missing_frontmatter: List[Path] = field(default_factory=list)
    health_score: float = 100.0
    summary: Dict[str, Any] = field(default_factory=dict)


# 知识点→学科映射（用于自动分类）
KNOWLEDGE_SUBJECT_MAP: Dict[str, str] = {
    # 物理
    '力的合成': 'physics',
    '牛顿第一定律': 'physics',
    '惯性': 'physics',
    '欧姆定律': 'physics',
    '浮力': 'physics',
    '压强': 'physics',
    '杠杆': 'physics',
    '电功率': 'physics',
    # 数学
    '一元一次方程': 'math',
    '二次函数': 'math',
    '勾股定理': 'math',
    '三角形全等': 'math',
    '全等三角形': 'math',
    '平行四边形': 'math',
    # 英语
    '现在完成时': 'english',
    '一般过去时': 'english',
    '定语从句': 'english',
    '被动语态': 'english',
    # 化学
    '化学方程式': 'chemistry',
}

# 知识点页面模板
CONCEPT_TEMPLATE = """---
type: concept
title: {title}
subject: {subject}
stage: middle
grade: {grade}
confidence: low
created: {created}
updated: {updated}
tags:
  - 知识点
  - {subject}
---

# 概念：{title}

## 📌 TLDR
{tldr}

---

## 📖 核心定义

（待补充：核心概念定义、公式、定理）

---

## 🔑 解题步骤

（待补充：典型解题方法和步骤）

---

## ❌ 常见错误

| 错误类型 | 表现 | 纠正 |
|---------|------|------|
| 概念不清 | 对基本概念理解错误 | 回归课本，重新学习概念定义 |
| 计算错误 | 计算过程出错 | 每天 5 分钟练习，养成验算习惯 |

---

## 📚 关联题目

{questions}

---

## 🎯 变式练习

**生成命令**：
```bash
python3 scripts/generate-practice.py --student {student} --knowledge "{title}" --count 3
```

---

## 📅 学习轨迹

| 日期 | 事件 | 掌握程度 |
|------|------|---------|
| {created} | 建立概念页面 | 🟡 初步理解 |

---

## 🔗 相关链接

- [[../../mistakes/README|返回错题总览]]
- [[../index|回到知识库首页]]

---

*最后更新：{updated}*
*本页面由 WikiService 自动创建*
"""


class WikiService:
    """知识库服务类
    
    提供知识点页面的创建、迁移、检查等核心功能。
    
    Attributes:
        student_name: 学生姓名
        base_dir: 学生目录基路径
        student_dir: 学生目录完整路径
        wiki_dir: Wiki 目录路径
        concepts_dir: 知识点页面目录路径
        mistakes_dir: 错题目录路径
    
    Example:
        >>> service = WikiService("张三")
        >>> result = service.migrate_to_wiki()
        >>> report = service.lint_wiki()
    """
    
    def __init__(self, student_name: str, base_dir: Optional[Path] = None) -> None:
        """初始化 WikiService
        
        Args:
            student_name: 学生姓名
            base_dir: 学生目录基路径，默认为
                     /home/ubuntu/clawd/data/mistake-notebook/students
        """
        self.student_name = student_name
        
        if base_dir is None:
            base_dir = Path("/home/ubuntu/clawd/data/mistake-notebook/students")
        else:
            base_dir = Path(base_dir)
        
        self.base_dir = base_dir
        self.student_dir = base_dir / student_name
        self.wiki_dir = self.student_dir / "wiki"
        self.concepts_dir = self.wiki_dir / "concepts"
        self.mistakes_dir = self.student_dir / "mistakes"
    
    def _parse_frontmatter(self, content: str) -> Dict[str, str]:
        """解析 YAML frontmatter
        
        Args:
            content: Markdown 文件内容
        
        Returns:
            Dict[str, str]: 解析后的 frontmatter 字典
        """
        meta: Dict[str, str] = {}
        in_frontmatter = False
        
        for line in content.split('\n'):
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break
            
            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                meta[key.strip()] = value.strip()
        
        return meta
    
    def _find_all_mistakes(self, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        """扫描所有错题文件
        
        Args:
            subject: 学科筛选（可选）
        
        Returns:
            List[Dict[str, Any]]: 错题信息列表，每项包含 path, meta, content
        """
        mistakes: List[Dict[str, Any]] = []
        
        if not self.mistakes_dir.exists():
            return mistakes
        
        for md_file in self.mistakes_dir.rglob("mistake.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                meta = self._parse_frontmatter(content)
                
                # 学科筛选
                if subject and meta.get('subject') != subject:
                    continue
                
                mistakes.append({
                    'path': md_file,
                    'meta': meta,
                    'content': content
                })
            except Exception:
                # 跳过无法读取的文件
                continue
        
        return mistakes
    
    def _group_by_knowledge(self, mistakes: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按知识点分组错题
        
        Args:
            mistakes: 错题列表
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: 按知识点分组的字典
        """
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        for m in mistakes:
            kp = m['meta'].get('knowledge-point', '未分类')
            if not kp or kp == '':
                kp = '未分类'
            groups[kp].append(m)
        
        return groups
    
    def _get_subject_for_knowledge(
        self, 
        knowledge: str, 
        default_meta: Optional[Dict[str, str]] = None
    ) -> str:
        """获取知识点对应的学科
        
        Args:
            knowledge: 知识点名称
            default_meta: 默认元数据（用于回退）
        
        Returns:
            str: 学科标识符
        """
        # 先查映射表
        if knowledge in KNOWLEDGE_SUBJECT_MAP:
            return KNOWLEDGE_SUBJECT_MAP[knowledge]
        
        # 再查错题元数据
        if default_meta:
            return default_meta.get('subject', 'unknown')
        
        return 'unknown'
    
    def _generate_tldr(self, knowledge: str) -> str:
        """生成知识点 TLDR 摘要
        
        Args:
            knowledge: 知识点名称
        
        Returns:
            str: TLDR 摘要文本
        """
        tldr_templates: Dict[str, str] = {
            '欧姆定律': '导体中的电流与电压成正比，与电阻成反比。公式：I = U/R',
            '浮力': '浸在液体中的物体受到向上的力，大小等于排开液体的重力。公式：F 浮 = ρ液 gV 排',
            '勾股定理': '直角三角形两直角边的平方和等于斜边的平方。公式：a² + b² = c²',
            '一元一次方程': '只含有一个未知数，且未知数的最高次数为 1 的方程。标准形式：ax + b = 0',
            '二次函数': '形如 y = ax² + bx + c 的函数，图像是抛物线',
            '现在完成时': '表示过去发生的动作对现在有影响，或从过去持续到现在的动作。结构：have/has + 过去分词',
            '定语从句': '用一个句子修饰名词或代词，被修饰的词叫先行词',
        }
        return tldr_templates.get(
            knowledge, 
            f'关于"{knowledge}"的核心概念和方法'
        )
    
    def _generate_questions_list(
        self, 
        mistakes: List[Dict[str, Any]]
    ) -> str:
        """生成关联题目列表（带 wikilink）
        
        Args:
            mistakes: 错题列表
        
        Returns:
            str: 格式化的题目列表文本
        """
        lines: List[str] = []
        for i, m in enumerate(mistakes[:10], 1):  # 最多显示 10 题
            try:
                rel_path = m['path'].relative_to(self.student_dir)
                kp = m['meta'].get('knowledge-point', '')
                subject = m['meta'].get('subject', '')
                unit = m['meta'].get('unit-name', '')
                
                # 生成 wikilink
                link = f"[[{rel_path.parent}|{kp}]]"
                lines.append(f"{i}. {link}（{subject}·{unit}）")
            except Exception:
                continue
        
        if len(mistakes) > 10:
            lines.append(f"\n*还有 {len(mistakes) - 10} 道题目，详见错题目录*")
        
        return '\n'.join(lines)
    
    def create_concept_page(
        self, 
        knowledge: str, 
        mistakes: List[Mistake]
    ) -> Path:
        """创建知识点页面
        
        根据给定的知识点和关联错题，创建或更新知识点页面。
        
        Args:
            knowledge: 知识点名称
            mistakes: 关联的错题列表
        
        Returns:
            Path: 创建的知识点页面路径
        
        Raises:
            ValueError: 如果学生目录不存在
            FileNotFoundError: 如果无法创建目录
        """
        if not self.student_dir.exists():
            raise ValueError(f"学生目录不存在：{self.student_dir}")
        
        # 确保目录存在
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        filename = f"{knowledge}.md"
        concept_path = self.concepts_dir / filename
        
        # 检查是否已存在
        if concept_path.exists():
            return concept_path
        
        # 获取学科（从第一个错题推断）
        subject = 'unknown'
        if mistakes:
            mistake = mistakes[0]
            subject = mistake.subject.value if isinstance(mistake.subject, Subject) else str(mistake.subject)
        
        # 生成页面内容
        now = datetime.now().strftime('%Y-%m-%d')
        
        # 构建题目列表
        question_lines: List[str] = []
        for i, mistake in enumerate(mistakes[:10], 1):
            kp = mistake.knowledge_point
            subj = mistake.subject.value if isinstance(mistake.subject, Subject) else str(mistake.subject)
            unit = mistake.unit or '未分类'
            link = f"[[../../mistakes/{mistake.id}|{kp}]]"
            question_lines.append(f"{i}. {link}（{subj}·{unit}）")
        
        if len(mistakes) > 10:
            question_lines.append(f"\n*还有 {len(mistakes) - 10} 道题目*")
        
        questions_text = '\n'.join(question_lines) if question_lines else '（暂无关联题目）'
        
        content = CONCEPT_TEMPLATE.format(
            title=knowledge,
            subject=subject,
            grade='八年级',  # 默认值
            created=now,
            updated=now,
            tldr=self._generate_tldr(knowledge),
            questions=questions_text,
            student=self.student_name,
        )
        
        concept_path.write_text(content, encoding='utf-8')
        return concept_path
    
    def _add_link_to_mistake(
        self, 
        mistake_info: Dict[str, Any], 
        knowledge: str
    ) -> bool:
        """在错题文件中添加知识点链接
        
        Args:
            mistake_info: 错题信息字典（包含 path, meta, content）
            knowledge: 知识点名称
        
        Returns:
            bool: 是否成功添加链接
        """
        content = mistake_info['content']
        
        # 检查是否已有链接
        if f'[[wiki/concepts/{knowledge}' in content or f'[[{knowledge}]]' in content:
            return False
        
        # 在 frontmatter 后添加 wikilink
        fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not fm_match:
            return False
        
        insert_pos = fm_match.end()
        link_text = f"\n**关联知识点**：[[wiki/concepts/{knowledge}|{knowledge}]]\n"
        
        new_content = content[:insert_pos] + link_text + content[insert_pos:]
        mistake_info['path'].write_text(new_content, encoding='utf-8')
        
        return True
    
    def migrate_to_wiki(self, subject: Optional[str] = None) -> MigrationResult:
        """批量迁移错题到 Wiki 模式
        
        扫描所有错题，按知识点分组，创建知识点页面，并建立双向链接。
        
        Args:
            subject: 学科筛选（可选），如 'math', 'physics'
        
        Returns:
            MigrationResult: 迁移结果，包含统计信息和详细报告
        
        Example:
            >>> service = WikiService("张三")
            >>> result = service.migrate_to_wiki()
            >>> print(f"创建 {result.created_pages} 个知识点页面")
        """
        result = MigrationResult()
        
        # 检查学生目录
        if not self.student_dir.exists():
            result.success = False
            result.error_message = f"学生目录不存在：{self.student_dir}"
            return result
        
        # 扫描错题
        mistakes = self._find_all_mistakes(subject)
        result.total_mistakes = len(mistakes)
        
        if not mistakes:
            return result
        
        # 按知识点分组
        groups = self._group_by_knowledge(mistakes)
        result.total_concepts = len(groups)
        
        # 处理每个知识点
        for knowledge, mistakes_list in sorted(groups.items()):
            # 获取学科
            subject_for_kp = self._get_subject_for_knowledge(
                knowledge, 
                mistakes_list[0]['meta'] if mistakes_list else None
            )
            
            # 创建知识点页面
            concept_path = self.concepts_dir / f"{knowledge}.md"
            page_created = False
            
            if not concept_path.exists():
                # 确保目录存在
                self.concepts_dir.mkdir(parents=True, exist_ok=True)
                
                # 创建页面
                now = datetime.now().strftime('%Y-%m-%d')
                question_lines: List[str] = []
                
                for i, m in enumerate(mistakes_list[:10], 1):
                    try:
                        rel_path = m['path'].relative_to(self.student_dir)
                        kp = m['meta'].get('knowledge-point', '')
                        subj = m['meta'].get('subject', '')
                        unit = m['meta'].get('unit-name', '')
                        link = f"[[{rel_path.parent}|{kp}]]"
                        question_lines.append(f"{i}. {link}（{subj}·{unit}）")
                    except Exception:
                        continue
                
                if len(mistakes_list) > 10:
                    question_lines.append(f"\n*还有 {len(mistakes_list) - 10} 道题目*")
                
                questions_text = '\n'.join(question_lines) if question_lines else '（暂无关联题目）'
                
                content = CONCEPT_TEMPLATE.format(
                    title=knowledge,
                    subject=subject_for_kp,
                    grade='八年级',
                    created=now,
                    updated=now,
                    tldr=self._generate_tldr(knowledge),
                    questions=questions_text,
                    student=self.student_name,
                )
                
                concept_path.write_text(content, encoding='utf-8')
                page_created = True
                result.created_pages += 1
            
            # 添加链接到错题
            for m in mistakes_list:
                if self._add_link_to_mistake(m, knowledge):
                    result.added_links += 1
                else:
                    result.skipped += 1
            
            # 记录详细信息
            result.concept_details[knowledge] = {
                'subject': subject_for_kp,
                'mistake_count': len(mistakes_list),
                'page_created': page_created,
                'page_path': str(concept_path),
            }
        
        # 生成报告
        report_dir = self.wiki_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"migration-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        
        report_content = self._generate_migration_report(result)
        report_path.write_text(report_content, encoding='utf-8')
        result.report_path = report_path
        
        return result
    
    def _generate_migration_report(self, result: MigrationResult) -> str:
        """生成迁移报告
        
        Args:
            result: 迁移结果
        
        Returns:
            str: Markdown 格式的报告内容
        """
        # 构建知识点表格
        table_rows: List[str] = []
        for knowledge, details in sorted(result.concept_details.items()):
            status = '✅ 已创建' if details['page_created'] else '⏭️ 已存在'
            table_rows.append(
                f"| {knowledge} | {details['mistake_count']} | "
                f"{details['subject']} | {status} |"
            )
        
        table_content = '\n'.join(table_rows) if table_rows else '无数据'
        
        report = f"""# Wiki 迁移报告

**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**学生**：{self.student_name}

## 📊 统计摘要

| 指标 | 数量 |
|------|------|
| 扫描错题总数 | {result.total_mistakes} |
| 涉及知识点数 | {result.total_concepts} |
| 创建知识点页面 | {result.created_pages} |
| 添加链接数 | {result.added_links} |
| 跳过（已关联） | {result.skipped} |

## 📚 知识点分布

| 知识点 | 题目数 | 学科 | 页面状态 |
|--------|--------|------|---------|
{table_content}

## ✅ 下一步建议

1. 检查新创建的知识点页面，补充核心定义和解题步骤
2. 运行 `lint_wiki()` 检查知识库健康状态
3. 在 Obsidian 中查看图谱，确认双向链接正常

---

*本报告由 WikiService 自动生成*
"""
        return report
    
    def _find_all_wikilinks(self, content: str) -> set:
        """找出文件中所有的 wiki 链接 [[xxx]]
        
        Args:
            content: Markdown 文件内容
        
        Returns:
            set: 链接目标集合
        """
        links: set = set()
        
        for line in content.split('\n'):
            start = 0
            while True:
                pos = line.find('[[', start)
                if pos == -1:
                    break
                end = line.find(']]', pos)
                if end == -1:
                    break
                link = line[pos+2:end]
                # 处理 [[xxx|yyy]] 格式
                if '|' in link:
                    link = link.split('|')[0]
                links.add(link.strip())
                start = end + 2
        
        return links
    
    def _check_orphan_pages(self) -> List[Path]:
        """检查孤儿知识点页面（没有题目链接指向）
        
        Returns:
            List[Path]: 孤儿页面路径列表
        """
        orphans: List[Path] = []
        
        if not self.concepts_dir.exists():
            return orphans
        
        # 收集所有知识点页面
        concept_files: Dict[str, Path] = {}
        for md_file in self.concepts_dir.glob("*.md"):
            if md_file.name == "README.md":
                continue
            meta = self._parse_frontmatter(md_file.read_text(encoding='utf-8'))
            title = meta.get('title', md_file.stem)
            concept_files[title] = md_file
            concept_files[md_file.stem] = md_file
            concept_files[md_file.name] = md_file
        
        # 扫描所有错题，收集引用
        referenced: set = set()
        for mistake_file in self.mistakes_dir.rglob("*.md"):
            try:
                content = mistake_file.read_text(encoding='utf-8')
                links = self._find_all_wikilinks(content)
                for link in links:
                    if 'concepts/' in link:
                        fname = link.split('/')[-1].replace('.md', '')
                        referenced.add(fname)
                    if link in concept_files:
                        referenced.add(link)
            except Exception:
                continue
        
        # 找出未被引用的知识点
        checked: set = set()
        for title, path in concept_files.items():
            if path in checked:
                continue
            checked.add(path)
            
            if title in referenced or path.stem in referenced or path.name in referenced:
                continue
            orphans.append(path)
        
        return orphans
    
    def _check_unlinked_mistakes(self) -> List[Path]:
        """检查未关联到知识点的错题
        
        Returns:
            List[Path]: 未关联错题路径列表
        """
        unlinked: List[Path] = []
        
        if not self.concepts_dir.exists():
            return unlinked
        
        # 收集所有知识点名称
        concepts: set = set()
        for md_file in self.concepts_dir.glob("*.md"):
            if md_file.name == "README.md":
                continue
            meta = self._parse_frontmatter(md_file.read_text(encoding='utf-8'))
            title = meta.get('title', md_file.stem)
            concepts.add(title)
        
        # 检查错题是否关联到知识点
        for mistake_file in self.mistakes_dir.rglob("mistake.md"):
            try:
                content = mistake_file.read_text(encoding='utf-8')
                meta = self._parse_frontmatter(content)
                
                knowledge_point = meta.get('knowledge-point', '')
                has_link = any(concept in content for concept in concepts)
                
                if not has_link and knowledge_point:
                    if knowledge_point in concepts:
                        unlinked.append(mistake_file)
            except Exception:
                continue
        
        return unlinked
    
    def _check_outdated_pages(self, days: int = 14) -> List[Path]:
        """检查超过 N 天未更新的页面
        
        Args:
            days: 天数阈值，默认 14 天
        
        Returns:
            List[Path]: 过期页面路径列表
        """
        outdated: List[Path] = []
        
        if not self.wiki_dir.exists():
            return outdated
        
        from datetime import timedelta
        threshold = datetime.now() - timedelta(days=days)
        
        for md_file in self.wiki_dir.rglob("*.md"):
            try:
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                if mtime < threshold:
                    outdated.append(md_file)
            except Exception:
                continue
        
        return outdated
    
    def _check_missing_frontmatter(self) -> List[Path]:
        """检查缺失 frontmatter 的文件
        
        Returns:
            List[Path]: 缺失 frontmatter 的文件列表
        """
        missing: List[Path] = []
        
        if not self.wiki_dir.exists():
            return missing
        
        for md_file in self.wiki_dir.rglob("*.md"):
            if md_file.name == "README.md":
                continue
            
            try:
                content = md_file.read_text(encoding='utf-8')
                if not content.strip().startswith('---'):
                    missing.append(md_file)
                    continue
                
                meta = self._parse_frontmatter(content)
                if 'type' not in meta:
                    missing.append(md_file)
            except Exception:
                continue
        
        return missing
    
    def lint_wiki(self) -> LintReport:
        """检查知识库健康状态
        
        执行全面的知识库健康检查，包括孤儿页面、未关联错题、
        过期内容和缺失 frontmatter 等。
        
        Returns:
            LintReport: 检查报告，包含所有发现的问题和健康评分
        
        Example:
            >>> service = WikiService("张三")
            >>> report = service.lint_wiki()
            >>> print(f"健康评分：{report.health_score}")
            >>> print(f"发现问题数：{len(report.issues)}")
        """
        report = LintReport(
            student=self.student_name,
            check_time=datetime.now(),
        )
        
        # 执行各项检查
        report.orphans = self._check_orphan_pages()
        report.unlinked = self._check_unlinked_mistakes()
        report.outdated = self._check_outdated_pages()
        report.missing_frontmatter = self._check_missing_frontmatter()
        
        # 汇总问题
        all_issues: List[LintIssue] = []
        
        for path in report.orphans:
            all_issues.append(LintIssue(
                issue_type='orphan',
                path=path,
                message=f"孤儿页面：{path.name}",
                severity='warning',
                suggestion="考虑删除或添加链接",
            ))
        
        for path in report.unlinked:
            all_issues.append(LintIssue(
                issue_type='unlinked',
                path=path,
                message=f"未关联知识点：{path.name}",
                severity='info',
                suggestion="添加知识点链接",
            ))
        
        for path in report.outdated:
            all_issues.append(LintIssue(
                issue_type='outdated',
                path=path,
                message=f"过期页面：{path.name}",
                severity='info',
                suggestion="检查并更新内容",
            ))
        
        for path in report.missing_frontmatter:
            all_issues.append(LintIssue(
                issue_type='missing_frontmatter',
                path=path,
                message=f"缺失 frontmatter: {path.name}",
                severity='error',
                suggestion="添加 YAML frontmatter",
            ))
        
        report.issues = all_issues
        
        # 计算健康评分
        total_checks = (
            len(report.orphans) + 
            len(report.unlinked) + 
            len(report.outdated) + 
            len(report.missing_frontmatter)
        )
        
        # 基础分 100，每个问题扣分
        error_penalty = len(report.missing_frontmatter) * 10
        warning_penalty = len(report.orphans) * 5
        info_penalty = (len(report.unlinked) + len(report.outdated)) * 2
        
        total_penalty = error_penalty + warning_penalty + info_penalty
        report.health_score = max(0.0, 100.0 - total_penalty)
        
        # 生成摘要
        report.summary = {
            'total_issues': len(all_issues),
            'errors': len(report.missing_frontmatter),
            'warnings': len(report.orphans),
            'info': len(report.unlinked) + len(report.outdated),
            'health_score': round(report.health_score, 1),
        }
        
        return report
    
    def generate_lint_report_markdown(self, report: LintReport) -> str:
        """生成 Markdown 格式的检查报告
        
        Args:
            report: LintReport 对象
        
        Returns:
            str: Markdown 格式的报告内容
        """
        lines: List[str] = []
        lines.append("# 知识库健康检查报告")
        lines.append(f"\n**学生**: {report.student}")
        lines.append(f"**检查时间**: {report.check_time.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**健康评分**: {report.health_score}/100")
        lines.append("")
        
        # 孤儿页面
        lines.append("## 🚨 孤儿知识点页面")
        if report.orphans:
            lines.append("以下知识点页面没有被任何题目引用：")
            lines.append("")
            for path in report.orphans:
                try:
                    rel_path = path.relative_to(self.student_dir)
                    lines.append(f"- `{rel_path}`")
                except ValueError:
                    lines.append(f"- `{path}`")
        else:
            lines.append("✅ 无孤儿页面")
        lines.append("")
        
        # 未关联错题
        lines.append("## ⚠️ 未关联知识点的错题")
        if report.unlinked:
            lines.append("以下错题未关联到知识点页面：")
            lines.append("")
            for path in report.unlinked:
                try:
                    rel_path = path.relative_to(self.student_dir)
                    lines.append(f"- `{rel_path}`")
                except ValueError:
                    lines.append(f"- `{path}`")
        else:
            lines.append("✅ 所有错题已关联")
        lines.append("")
        
        # 过期页面
        lines.append("## 📅 过期页面（超过 14 天未更新）")
        if report.outdated:
            for path in report.outdated:
                try:
                    rel_path = path.relative_to(self.student_dir)
                    mtime = datetime.fromtimestamp(path.stat().st_mtime)
                    lines.append(f"- `{rel_path}` (最后更新：{mtime.strftime('%Y-%m-%d')})")
                except (ValueError, Exception):
                    lines.append(f"- `{path}`")
        else:
            lines.append("✅ 无过期页面")
        lines.append("")
        
        # 缺失 frontmatter
        lines.append("## 📝 缺失 Frontmatter 的文件")
        if report.missing_frontmatter:
            for path in report.missing_frontmatter:
                try:
                    rel_path = path.relative_to(self.student_dir)
                    lines.append(f"- `{rel_path}`")
                except ValueError:
                    lines.append(f"- `{path}`")
        else:
            lines.append("✅ 所有文件包含 frontmatter")
        lines.append("")
        
        # 总结
        lines.append("## 📊 统计摘要")
        lines.append(f"- 总问题数：{report.summary.get('total_issues', 0)}")
        lines.append(f"- 错误：{report.summary.get('errors', 0)}")
        lines.append(f"- 警告：{report.summary.get('warnings', 0)}")
        lines.append(f"- 提示：{report.summary.get('info', 0)}")
        lines.append("")
        
        return '\n'.join(lines)
