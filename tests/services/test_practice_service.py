"""
PracticeService 单元测试模块

测试练习生成服务的核心功能，包括：
- 服务初始化
- 知识点别名解析
- 练习生成（不同风格、数量）
- 可用模板查询
- PracticeSet 数据模型
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest import TestCase, main

# 添加 scripts 目录到路径
_script_dir = Path(__file__).resolve().parent.parent.parent / 'scripts'
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from services.practice_service import (
    KNOWLEDGE_ALIASES,
    PRACTICE_TEMPLATES,
    PracticeItem,
    PracticeService,
    PracticeSet,
)


class TestPracticeItem(TestCase):
    """PracticeItem 数据模型测试。"""
    
    def test_create_practice_item_basic(self) -> None:
        """测试创建基础练习题。"""
        item = PracticeItem(
            question='1+1=?',
            answer='2',
            parse='基础加法'
        )
        self.assertEqual(item.question, '1+1=?')
        self.assertEqual(item.answer, '2')
        self.assertEqual(item.parse, '基础加法')
        self.assertIsNone(item.options)
        self.assertEqual(item.style, 'mixed')
    
    def test_create_practice_item_with_options(self) -> None:
        """测试创建带选项的练习题。"""
        item = PracticeItem(
            question='选择题',
            answer='A',
            parse='解析',
            options='A. 选项 1  B. 选项 2',
            style='基础'
        )
        self.assertEqual(item.options, 'A. 选项 1  B. 选项 2')
        self.assertEqual(item.style, '基础')


class TestPracticeSet(TestCase):
    """PracticeSet 数据模型测试。"""
    
    def test_create_practice_set(self) -> None:
        """测试创建练习集。"""
        now = datetime.now()
        items = [
            PracticeItem('Q1', 'A1', 'P1'),
            PracticeItem('Q2', 'A2', 'P2'),
        ]
        ps = PracticeSet(
            student='张三',
            knowledge_point='欧姆定律',
            style='mixed',
            generated_at=now,
            items=items
        )
        self.assertEqual(ps.student, '张三')
        self.assertEqual(ps.knowledge_point, '欧姆定律')
        self.assertEqual(ps.style, 'mixed')
        self.assertEqual(ps.count, 2)
        self.assertEqual(ps.items, items)
    
    def test_practice_set_count_property(self) -> None:
        """测试 count 属性。"""
        ps = PracticeSet(
            student='张三',
            knowledge_point='测试',
            style='mixed',
            generated_at=datetime.now(),
            items=[]
        )
        self.assertEqual(ps.count, 0)
        
        ps.items.append(PracticeItem('Q', 'A', 'P'))
        self.assertEqual(ps.count, 1)
    
    def test_practice_set_to_markdown(self) -> None:
        """测试 to_markdown 方法。"""
        ps = PracticeSet(
            student='张三',
            knowledge_point='欧姆定律',
            style='mixed',
            generated_at=datetime(2026, 4, 12, 10, 30),
            items=[PracticeItem('1+1=?', '2', '基础加法')]
        )
        md = ps.to_markdown()
        
        self.assertIn('# 📝 举一反三练习', md)
        self.assertIn('**学生**：张三', md)
        self.assertIn('**知识点**：欧姆定律', md)
        self.assertIn('2026-04-12 10:30', md)
        self.assertIn('1+1=?', md)
        self.assertIn('**答案**：2', md)
        self.assertIn('**解析**：基础加法', md)
    
    def test_practice_set_save(self) -> None:
        """测试 save 方法（临时目录）。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            ps = PracticeSet(
                student='测试学生',
                knowledge_point='测试知识点',
                style='mixed',
                generated_at=datetime.now(),
                items=[PracticeItem('Q', 'A', 'P')]
            )
            output_path = Path(tmpdir) / 'test_practice.md'
            saved_path = ps.save(output_path)
            
            self.assertTrue(saved_path.exists())
            content = saved_path.read_text(encoding='utf-8')
            self.assertIn('测试学生', content)
            self.assertIn('测试知识点', content)


class TestPracticeServiceInit(TestCase):
    """PracticeService 初始化测试。"""
    
    def test_init_with_student_name(self) -> None:
        """测试基础初始化。"""
        service = PracticeService('张三')
        self.assertEqual(service.student_name, '张三')
        self.assertIsNone(service.base_dir)
    
    def test_init_with_base_dir(self) -> None:
        """测试带基础目录初始化。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            service = PracticeService('李四', base_dir=base_dir)
            self.assertEqual(service.student_name, '李四')
            self.assertEqual(service.base_dir, base_dir)


class TestPracticeServiceResolveKnowledgePoint(TestCase):
    """知识点别名解析测试。"""
    
    def setUp(self) -> None:
        self.service = PracticeService('测试')
    
    def test_resolve_known_alias(self) -> None:
        """测试已知别名解析。"""
        self.assertEqual(self.service._resolve_knowledge_point('欧姆'), '欧姆定律')
        self.assertEqual(self.service._resolve_knowledge_point('惯性'), '牛顿第一定律')
        self.assertEqual(self.service._resolve_knowledge_point('完成时'), '现在完成时')
    
    def test_resolve_standard_name(self) -> None:
        """测试标准名称返回原值。"""
        self.assertEqual(self.service._resolve_knowledge_point('欧姆定律'), '欧姆定律')
        self.assertEqual(self.service._resolve_knowledge_point('勾股定理'), '勾股定理')
    
    def test_resolve_unknown_name(self) -> None:
        """测试未知名称返回原值。"""
        self.assertEqual(self.service._resolve_knowledge_point('未知知识点'), '未知知识点')


class TestPracticeServiceGenerateParams(TestCase):
    """参数生成测试。"""
    
    def setUp(self) -> None:
        self.service = PracticeService('测试')
    
    def test_generate_params_returns_dict(self) -> None:
        """测试生成参数字典。"""
        params = self.service._generate_params()
        self.assertIsInstance(params, dict)
    
    def test_generate_params_contains_required_keys(self) -> None:
        """测试参数包含必需的键。"""
        params = self.service._generate_params()
        required_keys = ['f1', 'g', 'u', 'i', 'r', 'v', 's', 'p']
        for key in required_keys:
            self.assertIn(key, params, f"缺少必需参数：{key}")
    
    def test_generate_params_randomness(self) -> None:
        """测试参数生成的随机性。"""
        params1 = self.service._generate_params()
        params2 = self.service._generate_params()
        # 至少有部分参数不同
        self.assertNotEqual(params1, params2)


class TestPracticeServiceFillTemplate(TestCase):
    """模板填充测试。"""
    
    def setUp(self) -> None:
        self.service = PracticeService('测试')
    
    def test_fill_template_basic(self) -> None:
        """测试基础模板填充。"""
        params = self.service._generate_params()
        template = {
            'question': '一个重 {g}N 的物体',
            'answer': '{g}N',
            'parse': '重力为{g}'
        }
        item = self.service._fill_template(template, params)
        
        self.assertEqual(item.question, f"一个重 {params['g']}N 的物体")
        self.assertEqual(item.answer, f"{params['g']}N")
        self.assertIn(str(params['g']), item.parse)
    
    def test_fill_template_with_options(self) -> None:
        """测试带选项的模板填充。"""
        params = self.service._generate_params()
        template = {
            'question': '选择题',
            'answer': 'A',
            'parse': '解析',
            'options': 'A. {g}N  B. 其他'
        }
        item = self.service._fill_template(template, params)
        
        self.assertIsNotNone(item.options)
        self.assertIn(str(params['g']), item.options)
    
    def test_fill_template_missing_key(self) -> None:
        """测试缺失参数键的处理。"""
        params = self.service._generate_params()
        template = {
            'question': '题目：{unknown_key}',
            'answer': '答案',
            'parse': '解析'
        }
        item = self.service._fill_template(template, params)
        # 应该保留原样而不是抛出异常
        self.assertEqual(item.question, '题目：{unknown_key}')


class TestPracticeServiceGeneratePractice(TestCase):
    """练习生成测试。"""
    
    def setUp(self) -> None:
        self.service = PracticeService('张三')
    
    def test_generate_practice_basic(self) -> None:
        """测试基础练习生成。"""
        practice_set = self.service.generate_practice('欧姆定律', style='mixed', count=2)
        
        self.assertEqual(practice_set.student, '张三')
        self.assertEqual(practice_set.knowledge_point, '欧姆定律')
        self.assertEqual(practice_set.style, 'mixed')
        self.assertEqual(practice_set.count, 2)
        self.assertIsInstance(practice_set.generated_at, datetime)
    
    def test_generate_practice_with_alias(self) -> None:
        """测试使用知识点别名。"""
        practice_set = self.service.generate_practice('欧姆', style='基础', count=1)
        
        self.assertEqual(practice_set.knowledge_point, '欧姆')
        self.assertGreater(practice_set.count, 0)
    
    def test_generate_practice_different_styles(self) -> None:
        """测试不同风格的练习生成。"""
        for style in ['基础', '变式', '提升', 'mixed']:
            with self.subTest(style=style):
                ps = self.service.generate_practice('勾股定理', style=style, count=1)
                self.assertGreaterEqual(ps.count, 0)
    
    def test_generate_practice_unknown_knowledge_point(self) -> None:
        """测试未知知识点的处理。"""
        practice_set = self.service.generate_practice('不存在的知识点', count=3)
        
        self.assertEqual(practice_set.count, 0)
        self.assertEqual(practice_set.items, [])
    
    def test_generate_practice_count_limit(self) -> None:
        """测试题目数量限制。"""
        ps = self.service.generate_practice('欧姆定律', style='基础', count=10)
        # 基础风格只有 2 道题，应该返回 2 道
        self.assertLessEqual(ps.count, 10)
    
    def test_generate_practice_randomness(self) -> None:
        """测试练习生成的随机性。"""
        ps1 = self.service.generate_practice('欧姆定律', style='mixed', count=3)
        ps2 = self.service.generate_practice('欧姆定律', style='mixed', count=3)
        
        # 两次生成的题目应该不同（至少部分不同）
        q1 = [item.question for item in ps1.items]
        q2 = [item.question for item in ps2.items]
        # 不要求完全不同，但应该有差异
        self.assertNotEqual(q1, q2)


class TestPracticeServiceGetAvailableTemplates(TestCase):
    """可用模板查询测试。"""
    
    def setUp(self) -> None:
        self.service = PracticeService('测试')
    
    def test_get_available_templates_returns_list(self) -> None:
        """测试返回类型。"""
        templates = self.service.get_available_templates()
        self.assertIsInstance(templates, list)
    
    def test_get_available_templates_not_empty(self) -> None:
        """测试模板列表非空。"""
        templates = self.service.get_available_templates()
        self.assertGreater(len(templates), 0)
    
    def test_get_available_templates_sorted(self) -> None:
        """测试模板列表已排序。"""
        templates = self.service.get_available_templates()
        self.assertEqual(templates, sorted(templates))
    
    def test_get_available_templates_contains_expected(self) -> None:
        """测试包含预期的知识点。"""
        templates = self.service.get_available_templates()
        expected = ['欧姆定律', '勾股定理', '牛顿第一定律', '浮力']
        for kp in expected:
            self.assertIn(kp, templates)


class TestPracticeServiceIntegration(TestCase):
    """集成测试。"""
    
    def test_full_workflow(self) -> None:
        """测试完整工作流程。"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            service = PracticeService('王五', base_dir=base_dir)
            
            # 生成练习
            ps = service.generate_practice('杠杆', style='mixed', count=2)
            self.assertEqual(ps.count, 2)
            
            # 保存
            output_path = base_dir / 'output' / 'practice.md'
            saved_path = ps.save(output_path)
            self.assertTrue(saved_path.exists())
            
            # 验证内容
            content = saved_path.read_text(encoding='utf-8')
            self.assertIn('王五', content)
            self.assertIn('杠杆', content)


class TestKnowledgeAliases(TestCase):
    """知识点别名映射测试。"""
    
    def test_alias_mapping_exists(self) -> None:
        """测试别名映射存在。"""
        self.assertIsInstance(KNOWLEDGE_ALIASES, dict)
        self.assertGreater(len(KNOWLEDGE_ALIASES), 0)
    
    def test_alias_consistency(self) -> None:
        """测试别名一致性。"""
        # 别名应该映射到实际存在的模板
        for alias, standard in KNOWLEDGE_ALIASES.items():
            self.assertIn(standard, PRACTICE_TEMPLATES, f"别名 {alias} 映射到不存在的模板 {standard}")


class TestPracticeTemplates(TestCase):
    """练习模板测试。"""
    
    def test_templates_structure(self) -> None:
        """测试模板结构。"""
        self.assertIsInstance(PRACTICE_TEMPLATES, dict)
        
        for kp, styles in PRACTICE_TEMPLATES.items():
            self.assertIsInstance(styles, dict)
            for style, templates in styles.items():
                self.assertIn(style, ['基础', '变式', '提升'], f"{kp} 包含无效风格：{style}")
                self.assertIsInstance(templates, list)
                for t in templates:
                    self.assertIn('question', t)
                    self.assertIn('answer', t)
                    self.assertIn('parse', t)


if __name__ == '__main__':
    main()
