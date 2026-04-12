"""
文件操作模块 - 错题文件的前后处理、查找和读写操作。

提供统一的 frontmatter 解析、文件查找、路径处理等核心功能。
"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
from threading import Lock


# 全局目录缓存 - 缓存学生目录结构，避免重复扫描
_directory_cache: Dict[str, List[Path]] = {}
_cache_lock = Lock()


def clear_directory_cache(student_dir: Optional[Path] = None) -> None:
    """
    清除目录缓存
    
    Args:
        student_dir: 指定要清除的学生目录，None 则清除所有缓存
    """
    with _cache_lock:
        if student_dir is None:
            _directory_cache.clear()
        else:
            key = str(student_dir.resolve())
            if key in _directory_cache:
                del _directory_cache[key]


def get_directory_cache_key(student_dir: Path) -> str:
    """获取目录缓存键"""
    return str(student_dir.resolve())


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


def _scan_mistake_file(
    mistake_file: Path,
    subject: Optional[str] = None,
    knowledge_point: Optional[str] = None,
    **filters: Any
) -> Optional[Path]:
    """
    扫描单个错题文件（用于并行处理）
    
    Args:
        mistake_file: 错题文件路径
        subject: 按学科筛选
        knowledge_point: 按知识点筛选
        **filters: 其他筛选条件
        
    Returns:
        符合条件的文件路径，不符合返回 None
    """
    try:
        content = mistake_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        
        # 学科筛选
        if subject and fm.get("subject") != subject:
            return None
        
        # 知识点筛选
        if knowledge_point and fm.get("knowledge-point") != knowledge_point:
            return None
        
        # 其他筛选条件（预留扩展）
        # TODO: 实现更多筛选逻辑
        
        return mistake_file
    except (OSError, UnicodeDecodeError):
        return None


def find_mistake_files_parallel(
    student_dir: Path,
    subject: Optional[str] = None,
    knowledge_point: Optional[str] = None,
    max_workers: int = 8,
    use_cache: bool = True,
    **filters: Any
) -> List[Path]:
    """
    并行查找符合条件的错题文件（使用多线程加速）
    
    Args:
        student_dir: 学生目录路径
        subject: 按学科筛选（可选）
        knowledge_point: 按知识点筛选（可选）
        max_workers: 最大工作线程数（默认：8）
        use_cache: 是否使用目录缓存（默认：True）
        **filters: 其他筛选条件
        
    Returns:
        符合条件的文件路径列表
        
    Examples:
        >>> # 并行查找所有错题文件
        >>> files = find_mistake_files_parallel(Path("data/students/张三"))
        >>> # 按学科筛选
        >>> math_files = find_mistake_files_parallel(Path("data/students/张三"), subject="math")
    """
    mistakes_dir = student_dir / "mistakes"
    if not mistakes_dir.exists():
        return []
    
    # 使用缓存或扫描目录
    cache_key = get_directory_cache_key(student_dir)
    
    if use_cache:
        with _cache_lock:
            if cache_key in _directory_cache:
                mistake_files = _directory_cache[cache_key]
            else:
                mistake_files = list(mistakes_dir.rglob("mistake.md"))
                _directory_cache[cache_key] = mistake_files
    else:
        mistake_files = list(mistakes_dir.rglob("mistake.md"))
    
    if not mistake_files:
        return []
    
    # 并行处理文件
    result: List[Path] = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(
                _scan_mistake_file,
                f,
                subject,
                knowledge_point,
                **filters
            ): f for f in mistake_files
        }
        
        # 收集结果
        for future in as_completed(future_to_file):
            file_path = future.result()
            if file_path is not None:
                result.append(file_path)
    
    return result


def find_mistake_files(
    student_dir: Path,
    subject: Optional[str] = None,
    knowledge_point: Optional[str] = None,
    use_cache: bool = True,
    **filters: Any
) -> List[Path]:
    """
    查找符合条件的错题文件。
    
    Args:
        student_dir: 学生目录路径
        subject: 按学科筛选（可选）
        knowledge_point: 按知识点筛选（可选）
        use_cache: 是否使用目录缓存（默认：True）
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
    
    # 使用缓存或扫描目录
    cache_key = get_directory_cache_key(student_dir)
    
    if use_cache:
        with _cache_lock:
            if cache_key in _directory_cache:
                mistake_files = _directory_cache[cache_key]
            else:
                mistake_files = list(mistakes_dir.rglob("mistake.md"))
                _directory_cache[cache_key] = mistake_files
    else:
        mistake_files = list(mistakes_dir.rglob("mistake.md"))
    
    if not mistake_files:
        return []
    
    result: List[Path] = []
    
    for mistake_file in mistake_files:
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
    else:
        # 如果 base 不以 students 结尾，则添加 students 子目录
        if base.name != 'students':
            base = base / 'students'
    
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
