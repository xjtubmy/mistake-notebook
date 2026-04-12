"""
文件操作模块单元测试。

测试覆盖：
- parse_frontmatter: frontmatter 解析
- write_frontmatter: frontmatter 写入
- find_mistake_files: 文件查找
- get_student_dir: 学生目录获取
- read_mistake_file: 文件读取
- write_mistake_file: 文件写入
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.core.file_ops import (
    find_mistake_files,
    get_student_dir,
    parse_frontmatter,
    read_mistake_file,
    write_frontmatter,
    write_mistake_file,
)


class TestParseFrontmatter:
    """parse_frontmatter 函数测试。"""
    
    def test_parse_empty_content(self):
        """空内容返回空字典。"""
        content = ""
        fm = parse_frontmatter(content)
        assert fm == {}
    
    def test_parse_standard_frontmatter(self):
        """标准 frontmatter 解析。"""
        content = """---
id: 20260412-001
subject: math
knowledge-point: 一元二次方程
created: 2026-04-12
due-date: 2026-04-13
---
# 题目内容

这是一道关于一元二次方程的题目。
"""
        fm = parse_frontmatter(content)
        assert fm['id'] == '20260412-001'
        assert fm['subject'] == 'math'
        assert fm['knowledge-point'] == '一元二次方程'
        assert fm['created'] == '2026-04-12'
        assert fm['due-date'] == '2026-04-13'
    
    def test_parse_no_frontmatter(self):
        """无 frontmatter 返回空字典。"""
        content = """# 题目内容

这是一道没有 frontmatter 的题目。
"""
        fm = parse_frontmatter(content)
        assert fm == {}
    
    def test_parse_empty_frontmatter(self):
        """空 frontmatter 返回空字典。"""
        content = """---
---
# 题目内容
"""
        fm = parse_frontmatter(content)
        assert fm == {}
    
    def test_parse_frontmatter_with_colon_in_value(self):
        """值中包含冒号的情况。"""
        content = """---
title: "题目：一元二次方程"
---
# Content
"""
        fm = parse_frontmatter(content)
        assert fm['title'] == '"题目：一元二次方程"'


class TestWriteFrontmatter:
    """write_frontmatter 函数测试。"""
    
    def test_write_new_frontmatter(self):
        """为无 frontmatter 的内容添加 frontmatter。"""
        content = "# 题目内容\n\n这是正文。"
        metadata = {
            'id': '001',
            'subject': 'math',
            'created': '2026-04-12',
        }
        result = write_frontmatter(content, metadata)
        
        assert result.startswith("---\n")
        assert "id: 001" in result
        assert "subject: math" in result
        assert "created: 2026-04-12" in result
        assert "# 题目内容" in result
    
    def test_write_update_existing_frontmatter(self):
        """更新现有 frontmatter。"""
        content = """---
id: 001
subject: math
created: 2026-04-12
---
# 题目内容
"""
        metadata = {
            'due-date': '2026-04-13',
            'review-round': '1',
        }
        result = write_frontmatter(content, metadata)
        
        # 注意：当前实现是替换整个 frontmatter
        assert "due-date: 2026-04-13" in result
        assert "review-round: 1" in result
        assert "# 题目内容" in result
    
    def test_write_frontmatter_preserves_body(self):
        """写入 frontmatter 时保留正文内容。"""
        content = """---
id: 001
---
# 题目内容

详细的题目描述。
"""
        metadata = {'subject': 'math'}
        result = write_frontmatter(content, metadata)
        
        assert "# 题目内容" in result
        assert "详细的题目描述。" in result


class TestFindMistakeFiles:
    """find_mistake_files 函数测试。"""
    
    @pytest.fixture
    def temp_student_dir(self):
        """创建临时学生目录用于测试。"""
        temp_dir = tempfile.mkdtemp()
        student_dir = Path(temp_dir) / "test_student"
        student_dir.mkdir()
        
        # 创建测试文件结构
        mistakes_dir = student_dir / "mistakes"
        mistakes_dir.mkdir()
        
        # 创建数学错题
        math_dir = mistakes_dir / "math-001"
        math_dir.mkdir()
        (math_dir / "mistake.md").write_text(
            """---
id: math-001
subject: math
knowledge-point: 方程
---
# 数学题
""",
            encoding="utf-8"
        )
        
        # 创建物理错题
        physics_dir = mistakes_dir / "physics-001"
        physics_dir.mkdir()
        (physics_dir / "mistake.md").write_text(
            """---
id: physics-001
subject: physics
knowledge-point: 力学
---
# 物理题
""",
            encoding="utf-8"
        )
        
        # 创建另一道数学题
        math2_dir = mistakes_dir / "math-002"
        math2_dir.mkdir()
        (math2_dir / "mistake.md").write_text(
            """---
id: math-002
subject: math
knowledge-point: 函数
---
# 数学题 2
""",
            encoding="utf-8"
        )
        
        yield student_dir
        
        # 清理临时目录
        shutil.rmtree(temp_dir)
    
    def test_find_all_files(self, temp_student_dir):
        """无筛选条件时返回所有文件。"""
        files = find_mistake_files(temp_student_dir)
        assert len(files) == 3
    
    def test_find_by_subject(self, temp_student_dir):
        """按学科筛选。"""
        math_files = find_mistake_files(temp_student_dir, subject="math")
        assert len(math_files) == 2
        
        physics_files = find_mistake_files(temp_student_dir, subject="physics")
        assert len(physics_files) == 1
    
    def test_find_by_knowledge_point(self, temp_student_dir):
        """按知识点筛选。"""
        equation_files = find_mistake_files(
            temp_student_dir,
            knowledge_point="方程"
        )
        assert len(equation_files) == 1
    
    def test_find_nonexistent_dir(self):
        """目录不存在时返回空列表。"""
        files = find_mistake_files(Path("/nonexistent/path"))
        assert files == []
    
    def test_find_empty_mistakes_dir(self, temp_student_dir):
        """mistakes 目录为空时返回空列表。"""
        empty_dir = tempfile.mkdtemp()
        student_dir = Path(empty_dir) / "empty_student"
        student_dir.mkdir()
        (student_dir / "mistakes").mkdir()
        
        files = find_mistake_files(student_dir)
        assert files == []
        
        shutil.rmtree(empty_dir)


class TestGetStudentDir:
    """get_student_dir 函数测试。"""
    
    @pytest.fixture
    def temp_base_dir(self):
        """创建临时基础目录。"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_get_existing_dir(self, temp_base_dir):
        """目录已存在时直接返回。"""
        student_dir = temp_base_dir / "existing_student"
        student_dir.mkdir()
        
        result = get_student_dir("existing_student", base=temp_base_dir)
        assert result == student_dir
        assert result.exists()
    
    def test_get_create_new_dir(self, temp_base_dir):
        """目录不存在时自动创建。"""
        result = get_student_dir("new_student", base=temp_base_dir)
        
        assert result == temp_base_dir / "new_student"
        assert result.exists()
    
    def test_get_create_nested_dirs(self, temp_base_dir):
        """自动创建嵌套目录。"""
        result = get_student_dir("nested/student", base=temp_base_dir)
        
        assert result.exists()
        assert result.parent.exists()
    
    def test_get_default_base(self):
        """使用默认基础目录。"""
        # 这个测试会创建 data/mistake-notebook/students/测试学生
        # 测试后需要清理
        student_name = "测试学生_get_student_dir"
        try:
            result = get_student_dir(student_name)
            assert result.exists()
            assert "data/mistake-notebook/students" in str(result)
        finally:
            # 清理测试创建的目录
            if result.exists():
                shutil.rmtree(result.parent)


class TestReadMistakeFile:
    """read_mistake_file 函数测试。"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时测试文件。"""
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "mistake.md"
        file_path.write_text(
            """---
id: test-001
subject: math
created: 2026-04-12
---
# 题目内容

这是测试题目正文。
""",
            encoding="utf-8"
        )
        yield file_path
        shutil.rmtree(temp_dir)
    
    def test_read_standard_file(self, temp_file):
        """读取标准文件。"""
        fm, body = read_mistake_file(temp_file)
        
        assert fm['id'] == 'test-001'
        assert fm['subject'] == 'math'
        assert fm['created'] == '2026-04-12'
        assert "# 题目内容" in body
        assert "这是测试题目正文。" in body
    
    def test_read_missing_file(self):
        """读取缺失文件抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            read_mistake_file(Path("/nonexistent/path/mistake.md"))


class TestWriteMistakeFile:
    """write_mistake_file 函数测试。"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录。"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_write_new_file(self, temp_dir):
        """写入新文件。"""
        file_path = temp_dir / "new" / "mistake.md"
        metadata = {
            'id': 'new-001',
            'subject': 'math',
            'created': '2026-04-12',
        }
        content = "# 新题目\n\n这是新题目的内容。"
        
        write_mistake_file(file_path, metadata, content)
        
        assert file_path.exists()
        
        # 验证写入内容
        fm, body = read_mistake_file(file_path)
        assert fm['id'] == 'new-001'
        assert fm['subject'] == 'math'
        assert "# 新题目" in body
    
    def test_write_overwrite_existing(self, temp_dir):
        """覆盖现有文件。"""
        file_path = temp_dir / "existing" / "mistake.md"
        file_path.parent.mkdir(parents=True)
        
        # 先写入初始内容
        initial_metadata = {'id': 'old-001', 'subject': 'physics'}
        initial_content = "# 旧题目"
        write_mistake_file(file_path, initial_metadata, initial_content)
        
        # 覆盖写入新内容
        new_metadata = {'id': 'new-001', 'subject': 'math'}
        new_content = "# 新题目"
        write_mistake_file(file_path, new_metadata, new_content)
        
        # 验证覆盖结果
        fm, body = read_mistake_file(file_path)
        assert fm['id'] == 'new-001'
        assert fm['subject'] == 'math'
        assert "# 新题目" in body
        assert "# 旧题目" not in body
        assert "physics" not in str(fm)
