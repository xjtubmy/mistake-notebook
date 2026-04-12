#!/usr/bin/env python3
"""
测试数据生成器 - 生成大量错题用于性能测试

使用方法：
    python -m scripts.perf.generate_test_data [数量] [学生姓名]
"""

import random
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.file_ops import get_student_dir, write_mistake_file
from scripts.core.models import Subject, ErrorType, Confidence


# 知识点示例数据
SUBJECT_KNOWLEDGE_POINTS = {
    Subject.MATH: [
        "一元二次方程", "二次函数", "三角函数", "数列", "概率统计",
        "立体几何", "解析几何", "导数与应用", "向量", "复数",
        "不等式", "函数性质", "极限", "微积分基础", "线性代数"
    ],
    Subject.PHYSICS: [
        "力学基础", "牛顿运动定律", "能量守恒", "动量定理", "圆周运动",
        "万有引力", "电场", "电路分析", "磁场", "电磁感应",
        "光学", "波动", "热力学", "原子物理", "相对论基础"
    ],
    Subject.CHEMISTRY: [
        "化学键", "化学反应速率", "化学平衡", "氧化还原", "电化学",
        "有机化学基础", "烃类", "官能团", "溶液", "酸碱中和",
        "沉淀溶解", "配位化合物", "元素周期律", "物质结构", "实验操作"
    ],
    Subject.BIOLOGY: [
        "细胞结构", "细胞代谢", "遗传规律", "基因表达", "进化论",
        "生态系统", "光合作用", "呼吸作用", "神经系统", "内分泌系统",
        "免疫系统", "生殖发育", "DNA 结构", "蛋白质合成", "生物多样性"
    ],
    Subject.ENGLISH: [
        "时态语态", "从句", "非谓语动词", "虚拟语气", "倒装句",
        "词汇辨析", "阅读理解", "完形填空", "写作技巧", "听力理解",
        "固定搭配", "介词用法", "连词用法", "冠词用法", "代词用法"
    ],
    Subject.CHINESE: [
        "文言文阅读", "古诗词鉴赏", "现代文阅读", "作文技巧", "修辞手法",
        "病句修改", "成语运用", "文学常识", "字词辨析", "标点符号",
        "段落结构", "文章主旨", "表达方式", "描写手法", "论证方法"
    ],
}


def generate_mistake_content(subject: Subject, knowledge_point: str, mistake_id: str) -> str:
    """
    生成模拟的错题内容
    
    Args:
        subject: 学科
        knowledge_point: 知识点
        mistake_id: 错题 ID
    
    Returns:
        错题正文字符串
    """
    templates = [
        f"""## 题目

已知关于 {knowledge_point} 的问题，求解下列问题。

## 错误答案

学生在解题过程中出现了错误。

## 正确答案

正确的解题步骤和答案。

## 错因分析

学生对{knowledge_point}的理解不够深入，需要加强练习。
""",
        f"""## 题目

这是一道关于{subject.value}中{knowledge_point}的典型题目。

## 学生解答

学生采用了错误的方法进行解答。

## 正确解答

应该使用正确的方法来解决这个问题。

## 反思

需要加强对{knowledge_point}知识点的理解和应用。
""",
        f"""## 原题

考察{knowledge_point}的综合应用。

## 错误分析

错误原因：概念理解不清，解题方法不当。

## 正确思路

1. 首先分析题目条件
2. 运用{knowledge_point}相关知识
3. 逐步推导得出结论

## 总结

本题主要考察{knowledge_point}的掌握程度。
""",
    ]
    
    return random.choice(templates)


def generate_test_dataset(
    num_mistakes: int = 1000,
    student_name: str = "测试学生",
    base_dir: Optional[Path] = None,
    due_date_range: tuple = (-30, 30)
) -> List[Path]:
    """
    生成测试用的错题数据集
    
    Args:
        num_mistakes: 生成的错题数量
        student_name: 学生姓名
        base_dir: 基础目录，默认为 data/mistake-notebook/students
        due_date_range: 到期日范围（相对今天的天数），默认前后 30 天
    
    Returns:
        生成的错题文件路径列表
    """
    student_dir = get_student_dir(student_name, base_dir)
    mistakes_dir = student_dir / "mistakes"
    
    # 确保目录存在
    mistakes_dir.mkdir(parents=True, exist_ok=True)
    
    subjects = list(Subject)
    error_types = list(ErrorType)
    confidences = list(Confidence)
    
    today = date.today()
    created_files = []
    
    print(f"正在生成 {num_mistakes} 道错题...")
    
    for i in range(num_mistakes):
        # 随机选择学科
        subject = random.choice(subjects)
        
        # 获取该学科的知识点
        knowledge_points = SUBJECT_KNOWLEDGE_POINTS.get(subject, ["通用知识点"])
        knowledge_point = random.choice(knowledge_points)
        
        # 生成错题 ID
        mistake_id = f"perf-test-{i:05d}"
        
        # 随机生成日期
        days_ago = random.randint(0, 365)
        created = today - timedelta(days=days_ago)
        
        # 随机生成到期日（部分到期，部分未到期，部分已完成）
        if random.random() < 0.1:  # 10% 已完成
            due_date = date.max
            review_round = random.randint(5, 10)
        else:
            # 随机到期日
            due_days = random.randint(due_date_range[0], due_date_range[1])
            due_date = today + timedelta(days=due_days)
            review_round = random.randint(0, 4)
        
        # 随机错误类型和掌握度
        error_type = random.choice(error_types)
        confidence = random.choice(confidences)
        
        # 生成错题内容
        content = generate_mistake_content(subject, knowledge_point, mistake_id)
        
        # 构建文件路径
        subject_dir = mistakes_dir / subject.value
        mistake_dir = subject_dir / mistake_id
        mistake_file = mistake_dir / "mistake.md"
        
        # 写入文件
        metadata = {
            'id': mistake_id,
            'student': student_name,
            'subject': subject.value,
            'knowledge-point': knowledge_point,
            'error-type': error_type.value,
            'created': created.strftime('%Y-%m-%d'),
            'due-date': 'completed' if due_date == date.max else due_date.strftime('%Y-%m-%d'),
            'review-round': str(review_round),
            'confidence': confidence.value,
        }
        
        write_mistake_file(mistake_file, metadata, content)
        created_files.append(mistake_file)
        
        # 进度显示
        if (i + 1) % 100 == 0:
            print(f"  已生成 {i + 1}/{num_mistakes} 道错题")
    
    print(f"测试数据集生成完成：{len(created_files)} 道错题")
    print(f"存储位置：{mistakes_dir}")
    
    return created_files


def clear_test_data(student_name: str, base_dir: Optional[Path] = None) -> None:
    """
    清除测试数据
    
    Args:
        student_name: 学生姓名
        base_dir: 基础目录
    """
    import shutil
    
    student_dir = get_student_dir(student_name, base_dir)
    if student_dir.exists():
        shutil.rmtree(student_dir)
        print(f"已清除测试数据：{student_name}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="生成测试错题数据集")
    parser.add_argument(
        "num_mistakes",
        type=int,
        nargs="?",
        default=1000,
        help="生成的错题数量（默认：1000）"
    )
    parser.add_argument(
        "student_name",
        type=str,
        nargs="?",
        default="性能测试学生",
        help="学生姓名（默认：性能测试学生）"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="清除指定学生的测试数据"
    )
    
    args = parser.parse_args()
    
    if args.clear:
        clear_test_data(args.student_name)
    else:
        generate_test_dataset(args.num_mistakes, args.student_name)
