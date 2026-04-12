#!/usr/bin/env python3
"""
WikiService 单元测试

测试 scripts.services.wiki_service 模块中的 WikiService 类、
MigrationResult 和 LintReport 数据类。
"""

import tempfile
import shutil
from datetime import date, datetime
from pathlib import Path
import pytest

from scripts.core.models import Mistake, Subject, ErrorType, Confidence
from scripts.services.wiki_service import (
    WikiService,
    MigrationResult,
    LintReport,
    LintIssue,
    KNOWLEDGE_SUBJECT_MAP,
)


class TestMigrationResult:
    """MigrationResult 数据类测试"""
    
    def test_default_values(self):
        """测试 MigrationResult 默认值"""
        result = MigrationResult()
        
        assert result.total_mistakes == 0
        assert result.total_concepts == 0
        assert result.created_pages == 0
        assert result.added_links == 0
        assert result.skipped == 0
        assert result.concept_details == {}
        assert result.report_path is None
        assert result.success is True
        assert result.error_message == ""
    
    def test_custom_values(self):
        """测试 MigrationResult 自定义值"""
        result = MigrationResult(
            total_mistakes=100,
            total_concepts=10,
            created_pages=8,
            added_links=50,
            skipped=5,
            success=True,
        )
        
        assert result.total_mistakes == 100
        assert result.total_concepts == 10
        assert result.created_pages == 8
        assert result.added_links == 50
        assert result.skipped == 5
        assert result.success is True
    
    def test_concept_details(self):
        """测试 concept_details 字典"""
        result = MigrationResult()
        result.concept_details['欧姆定律'] = {
            'subject': 'physics',
            'mistake_count': 5,
            'page_created': True,
        }
        
        assert '欧姆定律' in result.concept_details
        assert result.concept_details['欧姆定律']['subject'] == 'physics'
        assert result.concept_details['欧姆定律']['mistake_count'] == 5


class TestLintReport:
    """LintReport 数据类测试"""
    
    def test_default_values(self):
        """测试 LintReport 默认值"""
        report = LintReport()
        
        assert report.student == ""
        assert isinstance(report.check_time, datetime)
        assert report.issues == []
        assert report.orphans == []
        assert report.unlinked == []
        assert report.outdated == []
        assert report.missing_frontmatter == []
        assert report.health_score == 100.0
        assert report.summary == {}
    
    def test_custom_values(self):
        """测试 LintReport 自定义值"""
        report = LintReport(
            student="张三",
            health_score=85.5,
            summary={'total_issues': 5},
        )
        
        assert report.student == "张三"
        assert report.health_score == 85.5
        assert report.summary['total_issues'] == 5
    
    def test_issues_list(self):
        """测试 issues 列表"""
        report = LintReport()
        report.issues.append(LintIssue(
            issue_type='orphan',
            path=Path('/test.md'),
            message='测试问题',
        ))
        
        assert len(report.issues) == 1
        assert report.issues[0].issue_type == 'orphan'


class TestLintIssue:
    """LintIssue 数据类测试"""
    
    def test_default_values(self):
        """测试 LintIssue 默认值"""
        issue = LintIssue(
            issue_type='orphan',
            path=Path('/test.md'),
            message='测试',
        )
        
        assert issue.severity == "warning"
        assert issue.suggestion == ""
    
    def test_custom_severity(self):
        """测试自定义严重程度"""
        issue = LintIssue(
            issue_type='missing_frontmatter',
            path=Path('/test.md'),
            message='缺失 frontmatter',
            severity='error',
            suggestion='添加 YAML frontmatter',
        )
        
        assert issue.severity == 'error'
        assert issue.suggestion == '添加 YAML frontmatter'


class TestWikiServiceInit:
    """WikiService 初始化测试"""
    
    def test_init_with_default_base_dir(self):
        """测试使用默认基目录初始化"""
        service = WikiService("测试学生")
        
        assert service.student_name == "测试学生"
        assert service.base_dir == Path("/home/ubuntu/clawd/data/mistake-notebook/students")
        assert service.student_dir == service.base_dir / "测试学生"
        assert service.wiki_dir == service.student_dir / "wiki"
        assert service.concepts_dir == service.wiki_dir / "concepts"
        assert service.mistakes_dir == service.student_dir / "mistakes"
    
    def test_init_with_custom_base_dir(self):
        """测试使用自定义基目录初始化"""
        custom_base = Path("/tmp/test_mistake_notebook")
        service = WikiService("测试学生", base_dir=custom_base)
        
        assert service.student_name == "测试学生"
        assert service.base_dir == custom_base
        assert service.student_dir == custom_base / "测试学生"
    
    def test_init_creates_path_objects(self):
        """测试初始化创建 Path 对象"""
        service = WikiService("测试学生")
        
        assert isinstance(service.base_dir, Path)
        assert isinstance(service.student_dir, Path)
        assert isinstance(service.wiki_dir, Path)


class TestWikiServiceParseFrontmatter:
    """WikiService._parse_frontmatter 方法测试"""
    
    def test_parse_empty_content(self):
        """测试解析空内容"""
        service = WikiService("测试学生")
        meta = service._parse_frontmatter("")
        
        assert meta == {}
    
    def test_parse_standard_frontmatter(self):
        """测试解析标准 frontmatter"""
        service = WikiService("测试学生")
        content = """---
type: mistake
subject: math
knowledge-point: 一元一次方程
---

# 题目内容
"""
        meta = service._parse_frontmatter(content)
        
        assert meta['type'] == 'mistake'
        assert meta['subject'] == 'math'
        assert meta['knowledge-point'] == '一元一次方程'
    
    def test_parse_no_frontmatter(self):
        """测试解析无 frontmatter 的内容"""
        service = WikiService("测试学生")
        content = "# 没有 frontmatter 的内容"
        
        meta = service._parse_frontmatter(content)
        
        assert meta == {}
    
    def test_parse_with_colon_in_value(self):
        """测试解析包含冒号的值"""
        service = WikiService("测试学生")
        content = """---
title: "标题：副标题"
---
"""
        meta = service._parse_frontmatter(content)
        
        assert meta['title'] == '"标题：副标题"'


class TestWikiServiceFindMistakes:
    """WikiService._find_all_mistakes 方法测试"""
    
    def test_find_no_mistakes_dir(self):
        """测试错题目录不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            mistakes = service._find_all_mistakes()
            
            assert mistakes == []
    
    def test_find_empty_mistakes_dir(self):
        """测试错题目录为空"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生" / "mistakes"
            student_dir.mkdir(parents=True)
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            mistakes = service._find_all_mistakes()
            
            assert mistakes == []
    
    def test_find_mistakes_with_files(self):
        """测试找到错题文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生" / "mistakes" / "unit1"
            student_dir.mkdir(parents=True)
            
            mistake_file = student_dir / "mistake.md"
            mistake_file.write_text("""---
type: mistake
subject: math
knowledge-point: 一元一次方程
---

# 题目
""", encoding='utf-8')
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            mistakes = service._find_all_mistakes()
            
            assert len(mistakes) == 1
            assert mistakes[0]['meta']['subject'] == 'math'
    
    def test_find_mistakes_with_subject_filter(self):
        """测试按学科筛选错题"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生" / "mistakes"
            student_dir.mkdir(parents=True)
            
            # 数学错题（文件名必须是 mistake.md 才能被扫描到）
            math_dir = student_dir / "math_unit"
            math_dir.mkdir()
            math_file = math_dir / "mistake.md"
            math_file.write_text("""---
type: mistake
subject: math
knowledge-point: 一元一次方程
---
""", encoding='utf-8')
            
            # 物理错题
            physics_dir = student_dir / "physics_unit"
            physics_dir.mkdir()
            physics_file = physics_dir / "mistake.md"
            physics_file.write_text("""---
type: mistake
subject: physics
knowledge-point: 欧姆定律
---
""", encoding='utf-8')
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            
            # 筛选数学
            math_mistakes = service._find_all_mistakes(subject='math')
            assert len(math_mistakes) == 1
            assert math_mistakes[0]['meta']['subject'] == 'math'
            
            # 筛选物理
            physics_mistakes = service._find_all_mistakes(subject='physics')
            assert len(physics_mistakes) == 1


class TestWikiServiceGroupByKnowledge:
    """WikiService._group_by_knowledge 方法测试"""
    
    def test_group_empty_list(self):
        """测试分组空列表"""
        service = WikiService("测试学生")
        groups = service._group_by_knowledge([])
        
        assert groups == {}
    
    def test_group_single_knowledge(self):
        """测试单个知识点分组"""
        service = WikiService("测试学生")
        mistakes = [
            {'meta': {'knowledge-point': '欧姆定律'}},
            {'meta': {'knowledge-point': '欧姆定律'}},
        ]
        
        groups = service._group_by_knowledge(mistakes)
        
        assert len(groups) == 1
        assert len(groups['欧姆定律']) == 2
    
    def test_group_multiple_knowledge(self):
        """测试多个知识点分组"""
        service = WikiService("测试学生")
        mistakes = [
            {'meta': {'knowledge-point': '欧姆定律'}},
            {'meta': {'knowledge-point': '勾股定理'}},
            {'meta': {'knowledge-point': '欧姆定律'}},
        ]
        
        groups = service._group_by_knowledge(mistakes)
        
        assert len(groups) == 2
        assert len(groups['欧姆定律']) == 2
        assert len(groups['勾股定理']) == 1
    
    def test_group_empty_knowledge_point(self):
        """测试空知识点归类为'未分类'"""
        service = WikiService("测试学生")
        mistakes = [
            {'meta': {'knowledge-point': ''}},
            {'meta': {}},
        ]
        
        groups = service._group_by_knowledge(mistakes)
        
        assert '未分类' in groups
        assert len(groups['未分类']) == 2


class TestWikiServiceGetSubjectForKnowledge:
    """WikiService._get_subject_for_knowledge 方法测试"""
    
    def test_get_from_map(self):
        """测试从映射表获取学科"""
        service = WikiService("测试学生")
        
        assert service._get_subject_for_knowledge('欧姆定律') == 'physics'
        assert service._get_subject_for_knowledge('勾股定理') == 'math'
        assert service._get_subject_for_knowledge('一元一次方程') == 'math'
    
    def test_get_from_default_meta(self):
        """测试从默认元数据获取学科"""
        service = WikiService("测试学生")
        
        subject = service._get_subject_for_knowledge(
            '未知知识点',
            {'subject': 'chemistry'}
        )
        
        assert subject == 'chemistry'
    
    def test_get_unknown_subject(self):
        """测试未知知识点返回 unknown"""
        service = WikiService("测试学生")
        
        subject = service._get_subject_for_knowledge('未知知识点')
        
        assert subject == 'unknown'


class TestWikiServiceGenerateTldr:
    """WikiService._generate_tldr 方法测试"""
    
    def test_generate_known_knowledge(self):
        """测试生成已知知识点的 TLDR"""
        service = WikiService("测试学生")
        
        tldr = service._generate_tldr('欧姆定律')
        assert '电流' in tldr
        assert 'I = U/R' in tldr
    
    def test_generate_unknown_knowledge(self):
        """测试生成未知知识点的 TLDR"""
        service = WikiService("测试学生")
        
        tldr = service._generate_tldr('未知知识点')
        
        assert '未知知识点' in tldr
        assert '核心概念' in tldr


class TestWikiServiceCreateConceptPage:
    """WikiService.create_concept_page 方法测试"""
    
    def test_create_new_page(self):
        """测试创建新知识点页面"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            student_dir.mkdir()
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            
            mistakes = [
                Mistake(
                    id='001',
                    student='测试学生',
                    subject=Subject.MATH,
                    knowledge_point='一元一次方程',
                    unit=None,
                    error_type=ErrorType.CALC,
                    created=date.today(),
                    due_date=date.today(),
                )
            ]
            
            concept_path = service.create_concept_page('一元一次方程', mistakes)
            
            assert concept_path.exists()
            assert concept_path.name == '一元一次方程.md'
            
            content = concept_path.read_text(encoding='utf-8')
            assert '一元一次方程' in content
            assert 'type: concept' in content
    
    def test_create_page_already_exists(self):
        """测试知识点页面已存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            concepts_dir = student_dir / "wiki" / "concepts"
            concepts_dir.mkdir(parents=True)
            
            # 预先创建页面
            existing_file = concepts_dir / "测试知识点.md"
            existing_file.write_text("# 已有页面", encoding='utf-8')
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            
            mistakes = [
                Mistake(
                    id='001',
                    student='测试学生',
                    subject=Subject.MATH,
                    knowledge_point='测试知识点',
                    unit=None,
                    error_type=ErrorType.CALC,
                    created=date.today(),
                    due_date=date.today(),
                )
            ]
            
            concept_path = service.create_concept_page('测试知识点', mistakes)
            
            assert concept_path.exists()
            assert concept_path.read_text(encoding='utf-8') == "# 已有页面"
    
    def test_create_page_student_dir_not_exists(self):
        """测试学生目录不存在时抛出异常"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            
            mistakes = [
                Mistake(
                    id='001',
                    student='测试学生',
                    subject=Subject.MATH,
                    knowledge_point='测试',
                    unit=None,
                    error_type=ErrorType.CALC,
                    created=date.today(),
                    due_date=date.today(),
                )
            ]
            
            with pytest.raises(ValueError, match="学生目录不存在"):
                service.create_concept_page('测试', mistakes)
    
    def test_create_page_with_multiple_mistakes(self):
        """测试创建包含多个错题的知识点页面"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            student_dir.mkdir()
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            
            mistakes = [
                Mistake(
                    id=f'00{i}',
                    student='测试学生',
                    subject=Subject.MATH,
                    knowledge_point='一元一次方程',
                    unit=None,
                    error_type=ErrorType.CALC,
                    created=date.today(),
                    due_date=date.today(),
                )
                for i in range(15)  # 15 个错题
            ]
            
            concept_path = service.create_concept_page('一元一次方程', mistakes)
            
            content = concept_path.read_text(encoding='utf-8')
            assert '还有 5 道题目' in content  # 只显示前 10 个


class TestWikiServiceMigrateToWiki:
    """WikiService.migrate_to_wiki 方法测试"""
    
    def test_migrate_empty_dir(self):
        """测试迁移空目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            student_dir.mkdir()
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            result = service.migrate_to_wiki()
            
            assert result.success is True
            assert result.total_mistakes == 0
            assert result.created_pages == 0
    
    def test_migrate_student_dir_not_exists(self):
        """测试学生目录不存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            result = service.migrate_to_wiki()
            
            assert result.success is False
            assert '学生目录不存在' in result.error_message
    
    def test_migrate_with_mistakes(self):
        """测试迁移包含错题的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建错题文件（需要嵌套在子目录中，文件名为 mistake.md）
            mistakes_dir = Path(tmpdir) / "测试学生" / "mistakes"
            unit_dir = mistakes_dir / "unit1"
            unit_dir.mkdir(parents=True)
            
            mistake_file = unit_dir / "mistake.md"
            mistake_file.write_text("""---
type: mistake
subject: math
knowledge-point: 一元一次方程
---

# 题目内容
""", encoding='utf-8')
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            result = service.migrate_to_wiki()
            
            assert result.success is True
            assert result.total_mistakes == 1
            assert result.total_concepts == 1
            assert result.created_pages == 1
            assert result.report_path is not None
            assert result.report_path.exists()
    
    def test_migrate_creates_report(self):
        """测试迁移生成报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建错题文件（需要嵌套在子目录中）
            mistakes_dir = Path(tmpdir) / "测试学生" / "mistakes"
            unit_dir = mistakes_dir / "unit1"
            unit_dir.mkdir(parents=True)
            
            mistake_file = unit_dir / "mistake.md"
            mistake_file.write_text("""---
type: mistake
subject: math
knowledge-point: 测试知识点
---
""", encoding='utf-8')
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            result = service.migrate_to_wiki()
            
            assert result.report_path is not None
            assert result.report_path.exists()
            
            report_content = result.report_path.read_text(encoding='utf-8')
            assert 'Wiki 迁移报告' in report_content
            assert '测试学生' in report_content


class TestWikiServiceLintWiki:
    """WikiService.lint_wiki 方法测试"""
    
    def test_lint_empty_wiki(self):
        """测试检查空知识库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            student_dir.mkdir()
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            report = service.lint_wiki()
            
            assert report.student == "测试学生"
            assert report.health_score == 100.0
            assert len(report.issues) == 0
    
    def test_lint_orphan_pages(self):
        """测试检查孤儿页面"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            concepts_dir = student_dir / "wiki" / "concepts"
            concepts_dir.mkdir(parents=True)
            
            # 创建孤儿页面
            orphan_file = concepts_dir / "孤儿知识点.md"
            orphan_file.write_text("""---
type: concept
title: 孤儿知识点
---
# 内容
""", encoding='utf-8')
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            report = service.lint_wiki()
            
            assert len(report.orphans) == 1
            assert report.health_score < 100.0
    
    def test_lint_missing_frontmatter(self):
        """测试检查缺失 frontmatter"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            wiki_dir = student_dir / "wiki"
            wiki_dir.mkdir(parents=True)
            
            # 创建缺失 frontmatter 的文件
            no_fm_file = wiki_dir / "no_frontmatter.md"
            no_fm_file.write_text("# 没有 frontmatter", encoding='utf-8')
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            report = service.lint_wiki()
            
            assert len(report.missing_frontmatter) == 1
            assert any(issue.issue_type == 'missing_frontmatter' for issue in report.issues)
    
    def test_lint_health_score_calculation(self):
        """测试健康评分计算"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            wiki_dir = student_dir / "wiki"
            wiki_dir.mkdir(parents=True)
            
            # 创建多个问题文件
            for i in range(3):
                no_fm_file = wiki_dir / f"no_fm_{i}.md"
                no_fm_file.write_text(f"# 内容{i}", encoding='utf-8')
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            report = service.lint_wiki()
            
            # 每个 missing_frontmatter 扣 10 分
            assert report.health_score <= 70.0
            assert report.summary['errors'] == 3
    
    def test_lint_generates_summary(self):
        """测试生成摘要统计"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            student_dir.mkdir()
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            report = service.lint_wiki()
            
            assert 'total_issues' in report.summary
            assert 'errors' in report.summary
            assert 'warnings' in report.summary
            assert 'info' in report.summary
            assert 'health_score' in report.summary


class TestWikiServiceGenerateLintReportMarkdown:
    """WikiService.generate_lint_report_markdown 方法测试"""
    
    def test_generate_report_structure(self):
        """测试生成报告结构"""
        report = LintReport(
            student="测试学生",
            health_score=85.0,
            summary={'total_issues': 2, 'errors': 1, 'warnings': 1, 'info': 0},
        )
        
        service = WikiService("测试学生")
        markdown = service.generate_lint_report_markdown(report)
        
        assert '# 知识库健康检查报告' in markdown
        assert '**学生**: 测试学生' in markdown
        assert '**健康评分**: 85.0/100' in markdown
        assert '## 🚨 孤儿知识点页面' in markdown
        assert '## ⚠️ 未关联知识点的错题' in markdown
        assert '## 📊 统计摘要' in markdown
    
    def test_generate_report_with_issues(self):
        """测试生成包含问题的报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "测试学生"
            concepts_dir = student_dir / "wiki" / "concepts"
            concepts_dir.mkdir(parents=True)
            
            orphan_file = concepts_dir / "孤儿.md"
            orphan_file.write_text("# 孤儿页面", encoding='utf-8')
            
            service = WikiService("测试学生", base_dir=Path(tmpdir))
            report = service.lint_wiki()
            markdown = service.generate_lint_report_markdown(report)
            
            assert '孤儿.md' in markdown or '孤儿' in markdown


class TestWikiServiceKnowledgeSubjectMap:
    """知识点 - 学科映射测试"""
    
    def test_map_contains_physics(self):
        """测试映射表包含物理知识点"""
        assert '欧姆定律' in KNOWLEDGE_SUBJECT_MAP
        assert KNOWLEDGE_SUBJECT_MAP['欧姆定律'] == 'physics'
    
    def test_map_contains_math(self):
        """测试映射表包含数学知识点"""
        assert '勾股定理' in KNOWLEDGE_SUBJECT_MAP
        assert KNOWLEDGE_SUBJECT_MAP['勾股定理'] == 'math'
    
    def test_map_contains_english(self):
        """测试映射表包含英语知识点"""
        assert '现在完成时' in KNOWLEDGE_SUBJECT_MAP
        assert KNOWLEDGE_SUBJECT_MAP['现在完成时'] == 'english'


class TestWikiServiceIntegration:
    """WikiService 集成测试"""
    
    def test_full_migration_workflow(self):
        """测试完整迁移工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建学生目录和错题
            student_dir = Path(tmpdir) / "集成测试学生" / "mistakes"
            student_dir.mkdir(parents=True)
            
            # 创建多个错题（每个错题在独立子目录中，文件名为 mistake.md）
            for i in range(3):
                unit_dir = student_dir / f"unit{i}"
                unit_dir.mkdir()
                mistake_file = unit_dir / "mistake.md"
                mistake_file.write_text(f"""---
type: mistake
subject: math
knowledge-point: 一元一次方程
unit-name: Unit 1
---

# 题目{i}
""", encoding='utf-8')
            
            # 执行迁移
            service = WikiService("集成测试学生", base_dir=Path(tmpdir))
            result = service.migrate_to_wiki()
            
            # 验证迁移结果
            assert result.success is True
            assert result.total_mistakes == 3
            assert result.created_pages == 1
            
            # 验证知识点页面创建
            concept_file = service.concepts_dir / "一元一次方程.md"
            assert concept_file.exists()
            
            content = concept_file.read_text(encoding='utf-8')
            assert '一元一次方程' in content
            assert 'type: concept' in content
            
            # 执行检查
            lint_report = service.lint_wiki()
            assert lint_report.student == "集成测试学生"
            assert lint_report.health_score > 0
    
    def test_migration_with_multiple_knowledge_points(self):
        """测试多个知识点的迁移"""
        with tempfile.TemporaryDirectory() as tmpdir:
            student_dir = Path(tmpdir) / "多知识点学生" / "mistakes"
            student_dir.mkdir(parents=True)
            
            # 创建不同知识点的错题（每个错题在独立子目录中）
            knowledge_points = ['欧姆定律', '勾股定理', '一元一次方程']
            for i, kp in enumerate(knowledge_points):
                unit_dir = student_dir / f"unit{i}"
                unit_dir.mkdir()
                mistake_file = unit_dir / "mistake.md"
                mistake_file.write_text(f"""---
type: mistake
subject: {"physics" if "欧姆" in kp else "math"}
knowledge-point: {kp}
---
""", encoding='utf-8')
            
            service = WikiService("多知识点学生", base_dir=Path(tmpdir))
            result = service.migrate_to_wiki()
            
            assert result.total_concepts == 3
            assert result.created_pages == 3
            
            # 验证每个知识点页面都创建了
            for kp in knowledge_points:
                concept_file = service.concepts_dir / f"{kp}.md"
                assert concept_file.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
