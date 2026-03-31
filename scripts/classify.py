#!/usr/bin/env python3
"""
错题自动分类脚本

用法:
    python3 classify.py --text <题目文本> --student <学生名> [其他参数]

功能:
    - 基于关键词匹配自动识别学科、知识点
    - 从学生档案读取年级、教材版本
    - 输出分类建议供用户确认

注意：题目文本由 LLM 从图片识别得到，无需单独 OCR
"""

import argparse
import json
import re
from pathlib import Path


# 学科关键词
SUBJECT_KEYWORDS = {
    'math': ['数学', '方程', '函数', '三角形', '圆', '概率', '统计', '代数', '几何', '计算', '求值', '证明'],
    'chinese': ['语文', '阅读', '作文', '古诗', '文言', '拼音', '汉字', '词语', '句子', '修辞'],
    'english': ['英语', 'English', 'grammar', 'vocabulary', 'reading', 'writing', 'listening', '单词', '语法', '从句'],
    'physics': ['物理', '力', '电', '磁', '光', '热', '能量', '速度', '加速度', '电阻', '电压'],
    'chemistry': ['化学', '反应', '元素', '分子', '原子', '溶液', '酸碱', '氧化', '还原', '方程式'],
    'biology': ['生物', '细胞', '基因', '遗传', '进化', '生态', '器官', '植物', '动物'],
    'history': ['历史', '朝代', '战争', '革命', '事件', '人物', '年代', '公元'],
    'geography': ['地理', '地图', '气候', '地形', '河流', '城市', '国家', '经纬度'],
    'politics': ['政治', '法律', '道德', '经济', '哲学', '社会', '制度', '政策'],
}

# 错误类型关键词
ERROR_TYPE_KEYWORDS = {
    '概念不清': ['概念', '定义', '理解', '含义', '意义', '性质'],
    '计算错误': ['计算', '算错', '结果', '答案', '得数'],
    '审题错误': ['题意', '条件', '要求', '问题', '已知'],
    '公式错误': ['公式', '定理', '法则', '规律'],
    '逻辑错误': ['推理', '证明', '逻辑', '因为', '所以'],
    '书写错误': ['格式', '步骤', '单位', '符号', '书写'],
}


def detect_subject(text: str) -> str:
    """检测学科"""
    scores = {}
    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[subject] = score

    if max(scores.values()) == 0:
        return 'unknown'

    return max(scores, key=scores.get)


def detect_error_type(text: str, user_answer: str = None) -> str:
    """检测错误类型"""
    scores = {}
    for error_type, keywords in ERROR_TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        scores[error_type] = score

    if max(scores.values()) == 0:
        return '其他'

    return max(scores, key=scores.get)


def suggest_knowledge_point(text: str, subject: str) -> str:
    """建议知识点（基于简单关键词匹配）"""
    # 这里可以加载更详细的知识点库进行匹配
    # 目前返回一个占位符，实际使用时需要更复杂的 NLP 模型

    # 数学知识点关键词
    if subject == 'math':
        if any(kw in text for kw in ['方程', '等式', '解']):
            return '方程'
        if any(kw in text for kw in ['函数', '图像', 'y=']):
            return '函数'
        if any(kw in text for kw in ['三角形', '角', '边']):
            return '三角形'
        if any(kw in text for kw in ['圆', '圆周', '半径']):
            return '圆'

    # 英语知识点关键词
    if subject == 'english':
        if any(kw in text for kw in ['时态', 'tense', 'have done', 'did']):
            return '时态'
        if any(kw in text for kw in ['从句', 'clause', 'which', 'who', 'that']):
            return '从句'

    return '待分类'


def classify(text: str, student: str, semester: str = None, unit: str = None, custom: str = None) -> dict:
    """
    自动分类错题

    Returns:
        分类结果字典
    """
    subject = detect_subject(text)
    error_type = detect_error_type(text)
    knowledge_point = suggest_knowledge_point(text, subject)

    # 读取学生档案获取年级和教材版本
    profile_path = Path(f'mistake-notebook/students/{student}/profile.md')
    grade = 'unknown'
    version = 'unknown'
    semester_info = 'unknown'

    if profile_path.exists():
        content = profile_path.read_text(encoding='utf-8')
        # 简单解析年级
        grade_match = re.search(r'年级 [：:]\s*(.+)', content)
        if grade_match:
            grade = grade_match.group(1).strip()

        # 简单解析教材版本（仅用于参考，不体现在目录中）
        if subject == 'math':
            version_match = re.search(r'数学.*?([人北苏].*?版)', content)
            if version_match:
                version = version_match.group(1).strip()

        # 解析学期单元映射
        if semester and unit:
            semester_info = f'semester-{semester}'

    return {
        'subject': subject,
        'grade': grade,
        'semester': semester_info,
        'unit': unit if unit else 'unknown',
        'custom': custom,  # 自定义分类
        'knowledge_point': knowledge_point,
        'error_type': error_type,
        'version': version,  # 仅参考，不用于目录
    }


def main():
    parser = argparse.ArgumentParser(description='错题自动分类')
    parser.add_argument('--text', required=True, help='题目文本')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--semester', help='学期：1（上）/2（下）')
    parser.add_argument('--unit', help='单元：unit-01 ~ unit-12 或 custom')
    parser.add_argument('--custom', help='自定义分类名')
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出')

    args = parser.parse_args()

    result = classify(args.text, args.student, args.semester, args.unit, args.custom)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=== 分类建议 ===")
        print(f"学科：{result['subject']}")
        print(f"年级：{result['grade']}")
        print(f"学期：{result['semester']}")
        print(f"单元：{result['unit']}")
        if result['custom']:
            print(f"自定义分类：{result['custom']}")
        print(f"知识点：{result['knowledge_point']}")
        print(f"错误类型：{result['error_type']}")
        print(f"教材版本（参考）：{result['version']}")
        print("\n请确认以上分类是否正确")


if __name__ == '__main__':
    main()
