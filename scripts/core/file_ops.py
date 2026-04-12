"""
文件操作模块 - 错题文件的前后处理、查找和读写操作。

提供统一的 frontmatter 解析、文件查找、路径处理等核心功能。
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def parse_frontmatter(content: str) -> Dict[str, Any]:
    """
    解析 Markdown 文件的 frontmatter 部分。
    
    Args:
        content: Markdown 文件内容
        
    Returns:
        解析后的 frontmatter 字典，无 frontmatter 时返回空字典
        
    Examples:
        >>> content = "---\\ncreated: 2026-04-12\\ndue-date: 2026-04-13\\n---\\n# Title"
        >>> fm = parse_frontmatter(content)
        >>> fm['created']
        '2026-04-12'
    """
    fm: Dict[str, Any] = {}
    match = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match:
        for line in match.group(1).strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                fm[key.strip()] = value.strip()
    return fm


def write_frontmatter(content: str, metadata: Dict[str, Any]) -> str:
    """
    将 metadata 写入 content 的 frontmatter 部分。
    
    如果 content 已有 frontmatter，则更新现有字段；
    如果没有 frontmatter，则在开头添加。
    
    Args:
        content: Markdown 文件内容
        metadata: 要写入的元数据字典
        
    Returns:
        更新后的完整内容
        
    Examples:
        >>> content = "---\\ncreated: 2026-04-12\\n---\\n# Title"
        >>> new_content = write_frontmatter(content, {'due-date': '2026-04-13'})
        >>> 'due-date: 2026-04-13' in new_content
        True
    """
    # 构建新的 frontmatter 字符串
    fm_lines = ["---"]
    for key, value in metadata.items():
        fm_lines.append(f"{key}: {value}")
    fm_lines.append("---")
    fm_block = "\n".join(fm_lines) + "\n"
    
    # 检查是否已有 frontmatter
    match = re.search(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
    if match:
        # 替换现有 frontmatter
        return fm_block + content[match.end():]
    else:
        # 在开头添加 frontmatter
        return fm_block + content


def find_mistake_files(
    student_dir: Path,
    subject: Optional[str] = None,
    knowledge_point: Optional[str] = None,
    **filters: Any
) -> List[Path]:
    """
    查找符合条件的错题文件。
    
    Args:
        student_dir: 学生目录路径
        subject: 按学科筛选（可选）
        knowledge_point: 按知识点筛选（可选）
        **filters: 其他筛选条件（暂未实现）
        
    Returns:
        符合条件的文件路径列表
        
    Examples:
        >>> # 查找某学生的所有错题文件
        >>> files = find_mistake_files(Path("data/students/张三"))
        >>> # 按学科筛选
        >>> math_files = find_mistake_files(Path("data/students/张三"), subject="math")
    """
    mistakes_dir = student_dir / "mistakes"
    if not mistakes_dir.exists():
        return []
    
    result: List[Path] = []
    
    for mistake_file in mistakes_dir.rglob("mistake.md"):
        try:
            content = mistake_file.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
        except (OSError, UnicodeDecodeError):
            continue
        
        # 学科筛选
        if subject and fm.get("subject") != subject:
            continue
        
        # 知识点筛选
        if knowledge_point and fm.get("knowledge-point") != knowledge_point:
            continue
        
        # 其他筛选条件（预留扩展）
        # TODO: 实现更多筛选逻辑
        
        result.append(mistake_file)
    
    return result


def get_student_dir(
    student_name: str,
    base: Optional[Path] = None
) -> Path:
    """
    获取或创建学生目录。
    
    Args:
        student_name: 学生姓名
        base: 基础目录（可选，默认为 data/mistake-notebook/students）
        
    Returns:
        学生目录路径（如果不存在则创建）
        
    Examples:
        >>> # 获取学生目录
        >>> student_dir = get_student_dir("张三")
        >>> # 指定基础目录
        >>> student_dir = get_student_dir("张三", base=Path("/tmp"))
    """
    if base is None:
        base = Path("data/mistake-notebook/students")
    
    student_dir = base / student_name
    student_dir.mkdir(parents=True, exist_ok=True)
    
    return student_dir


def read_mistake_file(path: Path) -> Tuple[Dict[str, Any], str]:
    """
    读取错题文件，返回 frontmatter 和正文内容。
    
    Args:
        path: 文件路径
        
    Returns:
        (frontmatter, content) 元组
        
    Raises:
        FileNotFoundError: 文件不存在时抛出
        
    Examples:
        >>> # 读取错题文件
        >>> fm, content = read_mistake_file(Path("data/students/张三/mistakes/math-001/mistake.md"))
    """
    if not path.exists():
        raise FileNotFoundError(f"错题文件不存在：{path}")
    
    content = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)
    
    # 移除 frontmatter 部分，返回纯正文
    match = re.search(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
    if match:
        body = content[match.end():]
    else:
        body = content
    
    return fm, body


def write_mistake_file(
    path: Path,
    metadata: Dict[str, Any],
    content: str
) -> None:
    """
    写入错题文件，包含 frontmatter 和正文。
    
    Args:
        path: 文件路径
        metadata: frontmatter 元数据
        content: 正文内容
        
    Examples:
        >>> # 写入新错题
        >>> metadata = {'id': '001', 'subject': 'math', 'created': '2026-04-12'}
        >>> write_mistake_file(Path("data/students/张三/mistakes/math-001/mistake.md"), metadata, "# 题目内容")
    """
    # 确保父目录存在
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # 构建完整内容
    full_content = write_frontmatter(content, metadata)
    
    # 写入文件
    path.write_text(full_content, encoding="utf-8")
