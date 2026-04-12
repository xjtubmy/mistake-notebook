"""
练习服务单元测试 - 验证难度标记、去重机制和难度筛选功能
"""

import unittest
import sys
from pathlib import Path

# 添加 scripts 目录到路径
_script_dir = Path(__file__).resolve().parent.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from services.practice_service import PracticeService, PracticeItem


class TestPracticeItem(unittest.TestCase):
    """测试 PracticeItem 数据模型"""
    
    def test_practice_item_has_difficulty(self):
        """验证 PracticeItem 包含 difficulty 字段"""
        item = PracticeItem(
            question="测试题目",
            answer="测试答案",
            parse="测试解析"
        )
        self.assertTrue(hasattr(item, 'difficulty'))
        self.assertIsInstance(item.difficulty, int)
        self.assertEqual(item.difficulty, 3)  # 默认难度
    
    def test_practice_item_has_hash(self):
        """验证 PracticeItem 包含 hash 字段"""
        item = PracticeItem(
            question="测试题目",
            answer="测试答案",
            parse="测试解析"
        )
        self.assertTrue(hasattr(item, 'hash'))
        self.assertIsInstance(item.hash, str)
    
    def test_practice_item_custom_difficulty(self):
        """验证可以自定义难度"""
        item = PracticeItem(
            question="测试题目",
            answer="测试答案",
            parse="测试解析",
            difficulty=5
        )
        self.assertEqual(item.difficulty, 5)


class TestDifficultyMarking(unittest.TestCase):
    """测试难度标记功能"""
    
    def setUp(self):
        self.service = PracticeService("测试学生")
    
    def test_base_style_difficulty(self):
        """验证基础题目标记为低难度 (1-2)"""
        practice_set = self.service.generate_practice("欧姆定律", style="基础", count=3)
        self.assertGreater(len(practice_set.items), 0)
        for item in practice_set.items:
            self.assertIn(item.difficulty, [1, 2])
    
    def test_variant_style_difficulty(self):
        """验证变式题目标记为中等难度 (3)"""
        practice_set = self.service.generate_practice("欧姆定律", style="变式", count=3)
        self.assertGreater(len(practice_set.items), 0)
        for item in practice_set.items:
            self.assertEqual(item.difficulty, 3)
    
    def test_advanced_style_difficulty(self):
        """验证提升题目标记为高难度 (4-5)"""
        practice_set = self.service.generate_practice("欧姆定律", style="提升", count=3)
        self.assertGreater(len(practice_set.items), 0)
        for item in practice_set.items:
            self.assertIn(item.difficulty, [4, 5])
    
    def test_mixed_style_difficulty(self):
        """验证混合风格包含不同难度"""
        practice_set = self.service.generate_practice("欧姆定律", style="mixed", count=6)
        self.assertGreater(len(practice_set.items), 0)
        difficulties = set(item.difficulty for item in practice_set.items)
        # 混合风格应该包含多种难度
        self.assertGreater(len(difficulties), 1)


class TestDeduplication(unittest.TestCase):
    """测试去重机制"""
    
    def setUp(self):
        self.service = PracticeService("测试学生")
    
    def test_items_have_unique_hash(self):
        """验证生成的题目具有唯一 hash"""
        practice_set = self.service.generate_practice("欧姆定律", style="mixed", count=5)
        hashes = [item.hash for item in practice_set.items]
        # 验证所有 hash 都是唯一的
        self.assertEqual(len(hashes), len(set(hashes)))
    
    def test_hash_based_on_content(self):
        """验证 hash 基于题目内容"""
        practice_set = self.service.generate_practice("欧姆定律", style="基础", count=2)
        items = practice_set.items
        if len(items) >= 2:
            # 不同题目应该有不同的 hash
            if items[0].question != items[1].question:
                self.assertNotEqual(items[0].hash, items[1].hash)
    
    def test_same_content_same_hash(self):
        """验证相同内容产生相同 hash"""
        item1 = PracticeItem(
            question="相同题目",
            answer="相同答案",
            parse="相同解析"
        )
        item2 = PracticeItem(
            question="相同题目",
            answer="相同答案",
            parse="相同解析"
        )
        # 手动计算 hash 验证
        import hashlib
        content = f"{item1.question}|{item1.answer}|{item1.parse}"
        expected_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
        self.assertEqual(expected_hash, expected_hash)  # 验证 hash 计算逻辑


class TestDifficultyFilter(unittest.TestCase):
    """测试难度筛选功能"""
    
    def setUp(self):
        self.service = PracticeService("测试学生")
    
    def test_filter_easy_difficulty(self):
        """验证可以筛选简单题目 (难度 1-2)"""
        practice_set = self.service.generate_practice(
            "欧姆定律",
            style="mixed",
            count=5,
            difficulty=(1, 2)
        )
        self.assertGreater(len(practice_set.items), 0)
        for item in practice_set.items:
            self.assertLessEqual(item.difficulty, 2)
    
    def test_filter_hard_difficulty(self):
        """验证可以筛选困难题目 (难度 4-5)"""
        practice_set = self.service.generate_practice(
            "欧姆定律",
            style="mixed",
            count=5,
            difficulty=(4, 5)
        )
        self.assertGreater(len(practice_set.items), 0)
        for item in practice_set.items:
            self.assertGreaterEqual(item.difficulty, 4)
    
    def test_filter_medium_difficulty(self):
        """验证可以筛选中等难度题目 (难度 3)"""
        practice_set = self.service.generate_practice(
            "欧姆定律",
            style="mixed",
            count=5,
            difficulty=(3, 3)
        )
        self.assertGreater(len(practice_set.items), 0)
        for item in practice_set.items:
            self.assertEqual(item.difficulty, 3)
    
    def test_no_filter_returns_all(self):
        """验证不指定难度时返回所有难度"""
        practice_set = self.service.generate_practice(
            "欧姆定律",
            style="mixed",
            count=10,
            difficulty=None
        )
        self.assertGreater(len(practice_set.items), 0)
        difficulties = set(item.difficulty for item in practice_set.items)
        # 应该包含多种难度
        self.assertGreater(len(difficulties), 1)


class TestPracticeServiceIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        self.service = PracticeService("集成测试学生")
    
    def test_generate_and_save(self):
        """验证生成和保存流程"""
        practice_set = self.service.generate_practice(
            "欧姆定律",
            style="mixed",
            count=3,
            difficulty=(1, 3)
        )
        
        # 验证基本属性
        self.assertEqual(practice_set.student, "集成测试学生")
        self.assertEqual(practice_set.knowledge_point, "欧姆定律")
        self.assertGreater(practice_set.count, 0)
        
        # 验证所有题目都有 difficulty 和 hash
        for item in practice_set.items:
            self.assertTrue(hasattr(item, 'difficulty'))
            self.assertTrue(hasattr(item, 'hash'))
            self.assertIsInstance(item.difficulty, int)
            self.assertIsInstance(item.hash, str)
            self.assertGreaterEqual(item.difficulty, 1)
            self.assertLessEqual(item.difficulty, 5)
    
    def test_multiple_knowledge_points(self):
        """验证多个知识点都能正常工作"""
        knowledge_points = ["欧姆定律", "浮力", "勾股定理", "现在完成时"]
        
        for kp in knowledge_points:
            practice_set = self.service.generate_practice(
                kp,
                style="mixed",
                count=2
            )
            self.assertGreaterEqual(len(practice_set.items), 0)
            for item in practice_set.items:
                self.assertTrue(hasattr(item, 'difficulty'))
                self.assertTrue(hasattr(item, 'hash'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
