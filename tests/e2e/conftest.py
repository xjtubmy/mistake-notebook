"""
E2E 测试 pytest fixtures。

提供临时目录、测试数据生成等共享 fixture。
"""

import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

import pytest


@pytest.fixture
def temp_dir():
    """
    创建临时测试目录，测试完成后自动清理。
    
    Yields:
        Path: 临时目录路径
    """
    tmpdir = tempfile.mkdtemp(prefix='mistake-notebook-e2e-')
    yield Path(tmpdir)
    # 清理临时目录
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def student_data_dir(temp_dir: Path) -> Path:
    """
    创建学生数据目录结构。
    
    Args:
        temp_dir: 临时根目录
    
    Yields:
        Path: 学生数据根目录
    """
    student_dir = temp_dir / 'data' / 'mistake-notebook' / 'students' / '测试学生'
    student_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建子目录
    (student_dir / 'mistakes').mkdir(exist_ok=True)
    (student_dir / 'wiki' / 'concepts').mkdir(parents=True, exist_ok=True)
    (student_dir / 'wiki' / 'reviews').mkdir(parents=True, exist_ok=True)
    (student_dir / 'practice').mkdir(exist_ok=True)
    (student_dir / 'reports').mkdir(exist_ok=True)
    
    return student_dir


@pytest.fixture
def sample_mistake_data() -> List[Dict]:
    """
    提供示例错题数据。
    
    Returns:
        List[Dict]: 错题数据列表
    """
    today = datetime.now()
    return [
        {
            'id': '20260412-001',
            'subject': 'math',
            'knowledge_point': '一元一次方程',
            'error_type': '计算错误',
            'difficulty': '⭐⭐',
            'created': (today - timedelta(days=5)).strftime('%Y-%m-%d'),
            'question': '解方程：3x + 5 = 17',
            'answer': 'x = 4',
            'analysis': '移项时符号错误',
        },
        {
            'id': '20260412-002',
            'subject': 'physics',
            'knowledge_point': '欧姆定律',
            'error_type': '概念理解错误',
            'difficulty': '⭐⭐⭐',
            'created': (today - timedelta(days=3)).strftime('%Y-%m-%d'),
            'question': '一段导体两端电压为 6V 时，通过它的电流为 0.3A，求电阻。',
            'answer': '20Ω',
            'analysis': '欧姆定律公式应用错误',
        },
        {
            'id': '20260412-003',
            'subject': 'math',
            'knowledge_point': '二次函数',
            'error_type': '审题错误',
            'difficulty': '⭐⭐⭐⭐',
            'created': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'question': '求抛物线 y = x² - 4x + 3 的顶点坐标。',
            'answer': '(2, -1)',
            'analysis': '顶点公式记忆错误',
        },
    ]


@pytest.fixture
def created_mistake_files(student_data_dir: Path, sample_mistake_data: List[Dict]) -> List[Path]:
    """
    在临时目录中创建示例错题文件。
    
    Args:
        student_data_dir: 学生数据目录
        sample_mistake_data: 错题数据
    
    Returns:
        List[Path]: 创建的错题文件路径列表
    """
    created_files = []
    
    for mistake in sample_mistake_data:
        # 创建错题目录
        mistake_dir = student_data_dir / 'mistakes' / mistake['id']
        mistake_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建错题文件
        mistake_file = mistake_dir / 'mistake.md'
        content = f"""---
id: {mistake['id']}
type: mistake
subject: {mistake['subject']}
knowledge-point: {mistake['knowledge_point']}
error-type: {mistake['error_type']}
difficulty: {mistake['difficulty']}
created: {mistake['created']}
review-round: 0
due-date: {(datetime.strptime(mistake['created'], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')}
tags:
  - 错题
  - {mistake['subject']}
---

# 错题：{mistake['id']}

## 题目

{mistake['question']}

## 正确答案

{mistake['answer']}

## 错误分析

{mistake['analysis']}

## 举一反三

（待补充）
"""
        mistake_file.write_text(content, encoding='utf-8')
        created_files.append(mistake_file)
    
    return created_files
