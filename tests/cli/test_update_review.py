"""
CLI 复习更新脚本单元测试

测试覆盖：
- --confidence 参数解析
- 掌握度对复习间隔的影响
"""

import shutil
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from scripts.core.file_ops import get_student_dir, write_mistake_file
from scripts.core.srs import calculate_next_due, ReviewSchedule


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


class TestConfidenceIntervalCalculation:
    """掌握度间隔计算测试"""
    
    def test_confidence_low_interval(self):
        """测试低掌握度间隔（乘数 1.0）"""
        today = date(2026, 4, 12)
        
        # 第二轮（索引 1），基础间隔 3 天
        # 低掌握度：3 * 1.0 = 3 天
        next_due = calculate_next_due(1, today, confidence='low')
        assert next_due == today + timedelta(days=3)
    
    def test_confidence_medium_interval(self):
        """测试中等掌握度间隔（乘数 1.2）"""
        today = date(2026, 4, 12)
        
        # 第二轮（索引 1），基础间隔 3 天
        # 中等掌握度：3 * 1.2 = 3.6 -> 3 天（向下取整）
        next_due = calculate_next_due(1, today, confidence='medium')
        assert next_due == today + timedelta(days=3)
    
    def test_confidence_high_interval(self):
        """测试高掌握度间隔（乘数 1.5）"""
        today = date(2026, 4, 12)
        
        # 第二轮（索引 1），基础间隔 3 天
        # 高掌握度：3 * 1.5 = 4.5 -> 4 天（向下取整）
        next_due = calculate_next_due(1, today, confidence='high')
        assert next_due == today + timedelta(days=4)
    
    def test_confidence_high_interval_round2(self):
        """测试高掌握度在第三轮的影响"""
        today = date(2026, 4, 12)
        
        # 第三轮（索引 2），基础间隔 7 天
        # 高掌握度：7 * 1.5 = 10.5 -> 10 天（向下取整）
        next_due = calculate_next_due(2, today, confidence='high')
        assert next_due == today + timedelta(days=10)
    
    def test_confidence_high_interval_round3(self):
        """测试高掌握度在第四轮的影响"""
        today = date(2026, 4, 12)
        
        # 第四轮（索引 3），基础间隔 15 天
        # 高掌握度：15 * 1.5 = 22.5 -> 22 天（向下取整）
        next_due = calculate_next_due(3, today, confidence='high')
        assert next_due == today + timedelta(days=22)
    
    def test_confidence_medium_interval_round3(self):
        """测试中等掌握度在第四轮的影响"""
        today = date(2026, 4, 12)
        
        # 第四轮（索引 3），基础间隔 15 天
        # 中等掌握度：15 * 1.2 = 18 天
        next_due = calculate_next_due(3, today, confidence='medium')
        assert next_due == today + timedelta(days=18)
    
    def test_default_confidence_multipliers(self):
        """测试默认掌握度乘数配置"""
        schedule = ReviewSchedule()
        
        assert schedule.confidence_multipliers['low'] == 1.0
        assert schedule.confidence_multipliers['medium'] == 1.2
        assert schedule.confidence_multipliers['high'] == 1.5


class TestCLIConfidenceParameter:
    """CLI --confidence 参数测试"""
    
    def test_confidence_help_message(self):
        """测试 CLI 帮助信息包含 --confidence 参数"""
        import subprocess
        import sys
        
        script_path = Path(__file__).parent.parent.parent / 'scripts' / 'cli' / 'update-review.py'
        
        result = subprocess.run(
            [sys.executable, str(script_path), '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # 验证帮助信息包含 confidence 参数
        assert '--confidence' in result.stdout
        assert 'low' in result.stdout.lower()
        assert 'medium' in result.stdout.lower()
        assert 'high' in result.stdout.lower()
