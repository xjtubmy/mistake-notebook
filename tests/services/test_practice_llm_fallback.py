"""
PracticeService LLM Fallback 单元测试模块

测试 LLM 动态生成变式题功能，包括：
- LLM prompt 构建
- LLM 响应解析
- 无模板时调用 LLM
- Mock LLM 调用测试
"""

import json
import sys
import os
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch, MagicMock

# 添加 scripts 目录到路径
_script_dir = Path(__file__).resolve().parent.parent.parent / 'scripts'
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from services.practice_service import (
    PracticeItem,
    PracticeService,
    PracticeSet,
)


class TestLLMPromptBuilding(TestCase):
    """LLM Prompt 构建测试。"""
    
    def setUp(self) -> None:
        """设置测试夹具。"""
        self.service = PracticeService("测试学生")
    
    def test_build_llm_prompt_basic(self) -> None:
        """测试基础 prompt 构建。"""
        prompt = self.service._build_llm_prompt("量子力学", "基础", 3)
        
        self.assertIn("量子力学", prompt)
        self.assertIn("3道", prompt)
        self.assertIn("基础概念题", prompt)
        self.assertIn("JSON", prompt)
        self.assertIn("questions", prompt)
    
    def test_build_llm_prompt_style_variations(self) -> None:
        """测试不同风格的 prompt。"""
        style_descriptions = {
            '基础': '基础概念题',
            '变式': '变式应用题',
            '提升': '提升拓展题',
            'mixed': '混合难度',
        }
        
        for style, expected_desc in style_descriptions.items():
            prompt = self.service._build_llm_prompt("测试知识点", style, 2)
            self.assertIn(expected_desc, prompt, f"风格 {style} 的 prompt 应包含 {expected_desc}")
    
    def test_build_llm_prompt_includes_example(self) -> None:
        """测试 prompt 包含示例输出。"""
        prompt = self.service._build_llm_prompt("牛顿定律", "变式", 2)
        
        self.assertIn("示例输出", prompt)
        self.assertIn("question", prompt)
        self.assertIn("answer", prompt)
        self.assertIn("parse", prompt)


class TestLLMResponseParsing(TestCase):
    """LLM 响应解析测试。"""
    
    def setUp(self) -> None:
        """设置测试夹具。"""
        self.service = PracticeService("测试学生")
    
    def test_parse_llm_response_valid_json(self) -> None:
        """测试解析有效的 JSON 响应。"""
        response = json.dumps({
            "questions": [
                {
                    "question": "什么是牛顿第一定律？",
                    "answer": "一切物体在没有受到外力作用时，总保持静止状态或匀速直线运动状态",
                    "parse": "牛顿第一定律描述了物体在不受外力时的运动状态"
                },
                {
                    "question": "关于惯性，下列说法正确的是（ ）",
                    "options": "A. 静止的物体没有惯性  B. 速度越大惯性越大  C. 质量越大惯性越大  D. 月球上没有惯性",
                    "answer": "C",
                    "parse": "惯性是物体的固有属性，只与质量有关"
                }
            ]
        })
        
        items = self.service._parse_llm_response(response)
        
        self.assertEqual(len(items), 2)
        self.assertIsInstance(items[0], PracticeItem)
        self.assertEqual(items[0].question, "什么是牛顿第一定律？")
        self.assertEqual(items[0].answer, "一切物体在没有受到外力作用时，总保持静止状态或匀速直线运动状态")
        self.assertIsNone(items[0].options)
        self.assertEqual(items[1].options, "A. 静止的物体没有惯性  B. 速度越大惯性越大  C. 质量越大惯性越大  D. 月球上没有惯性")
    
    def test_parse_llm_response_with_markdown_block(self) -> None:
        """测试解析包含 markdown 代码块的响应。"""
        response = """```json
{
    "questions": [
        {
            "question": "1+1=?",
            "answer": "2",
            "parse": "基础加法"
        }
    ]
}
```"""
        
        items = self.service._parse_llm_response(response)
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].question, "1+1=?")
    
    def test_parse_llm_response_missing_fields(self) -> None:
        """测试解析缺少必需字段的响应。"""
        response = json.dumps({
            "questions": [
                {
                    "question": "完整题目",
                    "answer": "答案",
                    "parse": "解析"
                },
                {
                    "question": "缺少答案的题目"
                    # 缺少 answer 和 parse
                }
            ]
        })
        
        items = self.service._parse_llm_response(response)
        
        # 只应返回格式完整的题目
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].question, "完整题目")
    
    def test_parse_llm_response_invalid_json(self) -> None:
        """测试解析无效 JSON 响应。"""
        response = "这不是 JSON 格式"
        
        with self.assertRaises(ValueError):
            self.service._parse_llm_response(response)
    
    def test_parse_llm_response_missing_questions_field(self) -> None:
        """测试解析缺少 questions 字段的响应。"""
        response = json.dumps({
            "data": [
                {"question": "题目", "answer": "答案", "parse": "解析"}
            ]
        })
        
        with self.assertRaises(ValueError):
            self.service._parse_llm_response(response)


class TestLLMCall(TestCase):
    """LLM 调用测试。"""
    
    def setUp(self) -> None:
        """设置测试夹具。"""
        self.service = PracticeService("测试学生")
        self.mock_response = json.dumps({
            "response": json.dumps({
                "questions": [
                    {
                        "question": "测试题目",
                        "answer": "测试答案",
                        "parse": "测试解析"
                    }
                ]
            })
        })
    
    @patch('urllib.request.urlopen')
    def test_call_llm_success(self, mock_urlopen: MagicMock) -> None:
        """测试 LLM 调用成功。"""
        mock_response = MagicMock()
        mock_response.read.return_value = self.mock_response.encode('utf-8')
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = lambda self, *args: None
        mock_urlopen.return_value = mock_response
        
        result = self.service._call_llm("测试 prompt")
        
        # result 是 LLM 返回的 response 字段内容（JSON 字符串）
        self.assertIn("questions", result)
        mock_urlopen.assert_called_once()
    
    @patch('urllib.request.urlopen')
    def test_call_llm_url_error(self, mock_urlopen: MagicMock) -> None:
        """测试 LLM 调用网络错误。"""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        with self.assertRaises(RuntimeError):
            self.service._call_llm("测试 prompt")
    
    @patch('urllib.request.urlopen')
    def test_call_llm_json_decode_error(self, mock_urlopen: MagicMock) -> None:
        """测试 LLM 返回无效 JSON。"""
        mock_response = MagicMock()
        mock_response.read.return_value = b"invalid json"
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = lambda self, *args: None
        mock_urlopen.return_value = mock_response
        
        with self.assertRaises(RuntimeError):
            self.service._call_llm("测试 prompt")
    
    @patch.dict(os.environ, {'LLM_API_URL': 'http://custom-api:11434/api/generate'})
    @patch('urllib.request.urlopen')
    def test_call_llm_uses_env_config(self, mock_urlopen: MagicMock) -> None:
        """测试 LLM 使用环境变量配置。"""
        mock_response = MagicMock()
        mock_response.read.return_value = self.mock_response.encode('utf-8')
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = lambda self, *args: None
        mock_urlopen.return_value = mock_response
        
        self.service._call_llm("测试 prompt")
        
        # 验证使用了自定义 URL（Request 对象的 full_url 属性）
        call_args = mock_urlopen.call_args[0][0]
        self.assertEqual(call_args.full_url, 'http://custom-api:11434/api/generate')


class TestGenerateWithLLM(TestCase):
    """generate_with_llm 方法测试。"""
    
    def setUp(self) -> None:
        """设置测试夹具。"""
        self.service = PracticeService("测试学生")
    
    @patch.object(PracticeService, '_call_llm')
    @patch.object(PracticeService, '_parse_llm_response')
    def test_generate_with_llm_calls_methods(
        self,
        mock_parse: MagicMock,
        mock_call: MagicMock
    ) -> None:
        """测试 generate_with_llm 调用内部方法。"""
        mock_call.return_value = '{"questions": []}'
        mock_parse.return_value = [
            PracticeItem("题目", "答案", "解析")
        ]
        
        items = self.service.generate_with_llm("新知识点", "基础", 2)
        
        mock_call.assert_called_once()
        mock_parse.assert_called_once()
        self.assertEqual(len(items), 1)
    
    @patch.object(PracticeService, '_call_llm')
    def test_generate_with_llm_propagates_error(self, mock_call: MagicMock) -> None:
        """测试 generate_with_llm 传播错误。"""
        mock_call.side_effect = RuntimeError("LLM 调用失败")
        
        with self.assertRaises(RuntimeError):
            self.service.generate_with_llm("测试", "基础", 1)


class TestGeneratePracticeWithLLMFallback(TestCase):
    """generate_practice LLM Fallback 测试。"""
    
    def setUp(self) -> None:
        """设置测试夹具。"""
        self.service = PracticeService("测试学生")
    
    def test_generate_practice_with_template_returns_items(self) -> None:
        """测试有模板时返回题目。"""
        # 欧姆定律有模板
        practice_set = self.service.generate_practice("欧姆定律", "基础", 2)
        
        # 应有题目
        self.assertGreater(practice_set.count, 0)
    
    def test_generate_practice_no_template_returns_empty(self) -> None:
        """测试无模板时返回空练习集。"""
        # 不存在的知识点
        practice_set = self.service.generate_practice("不存在的知识点", "基础", 2)
        
        # 应返回空练习集
        self.assertEqual(practice_set.count, 0)
    
    def test_generate_practice_llm_fallback_manual_call(self) -> None:
        """测试手动调用 LLM fallback。"""
        with patch.object(PracticeService, 'generate_with_llm') as mock_llm:
            mock_llm.return_value = [
                PracticeItem("LLM 生成题目", "LLM 答案", "LLM 解析")
            ]
            
            # 先调用 generate_practice（返回空）
            practice_set = self.service.generate_practice("不存在的知识点", "基础", 2)
            self.assertEqual(practice_set.count, 0)
            
            # 再手动调用 generate_with_llm
            items = self.service.generate_with_llm("不存在的知识点", "基础", 2)
            
            # 应调用 LLM
            mock_llm.assert_called_once()
            # 应有 LLM 生成的题目
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].question, "LLM 生成题目")


class TestPracticeItemDataTypeValidation(TestCase):
    """PracticeItem 数据类型验证测试。"""
    
    def test_practice_item_from_llm_has_correct_style(self) -> None:
        """测试 LLM 生成的 PracticeItem style 字段。"""
        item = PracticeItem(
            question="LLM 题目",
            answer="LLM 答案",
            parse="LLM 解析",
            style="llm"
        )
        
        self.assertEqual(item.style, "llm")
    
    def test_practice_item_all_fields_required(self) -> None:
        """测试 PracticeItem 必需字段。"""
        # question, answer, parse 是必需的
        item = PracticeItem(
            question="题目",
            answer="答案",
            parse="解析"
        )
        
        self.assertEqual(item.question, "题目")
        self.assertEqual(item.answer, "答案")
        self.assertEqual(item.parse, "解析")
        # options 是可选的
        self.assertIsNone(item.options)


if __name__ == '__main__':
    main()
