#!/usr/bin/env python3
"""
init-student.py - 学生档案初始化向导

功能:
1. 交互式问答收集学生信息
2. 自动选择教材版本映射
3. 创建学生档案和目录结构
4. 生成使用指南

用法:
    python3 init-student.py
    python3 init-student.py --name "张三" --grade "八年级"  # 非交互模式
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# 教材版本选项
TEXTBOOK_VERSIONS = {
    'math': ['人教版', '北师大版', '苏教版', '沪教版', '浙教版', '其他'],
    'chinese': ['部编版', '人教版', '苏教版', '语文版', '其他'],
    'english': ['外研版', '人教版', '译林版', '牛津版', '北师大版', '其他'],
    'physics': ['人教版', '北师大版', '苏科版', '沪科版', '其他'],
    'chemistry': ['人教版', '北师大版', '沪教版', '其他'],
    'biology': ['人教版', '北师大版', '苏教版', '其他'],
}

# 年级选项
GRADES = ['六年级', '七年级', '八年级', '九年级', '高一', '高二', '高三']

# 学期单元映射参考
UNIT_MAPPINGS = {
    'math': {
        '七年级': {
            '七上': 'unit-01:有理数，unit-02:整式的加减，unit-03:一元一次方程，unit-04:几何图形初步',
            '七下': 'unit-01:相交线与平行线，unit-02:实数，unit-03:平面直角坐标系，unit-04:二元一次方程组',
        },
        '八年级': {
            '八上': 'unit-01:三角形，unit-02:全等三角形，unit-03:轴对称，unit-04:整式乘法，unit-05:分式',
            '八下': 'unit-01:二次根式，unit-02:勾股定理，unit-03:平行四边形，unit-04:一次函数',
        },
        '九年级': {
            '九上': 'unit-01:一元二次方程，unit-02:二次函数，unit-03:圆，unit-04:相似',
            '九下': 'unit-01:反比例函数，unit-02:投影与视图',
        },
    },
    'english': {
        '七年级': {
            '七上': 'unit-01:Starter-Unit3，unit-02:Unit4-Unit6，unit-03:Unit7-Unit9',
            '七下': 'unit-01:Unit1-Unit4，unit-02:Unit5-Unit8，unit-03:Unit9-Unit12',
        },
        '八年级': {
            '八上': 'unit-01:Module1-2，unit-02:Module3-4，unit-03:Module5-6，unit-04:Module7-8',
            '八下': 'unit-01:Module1-2，unit-02:Module3-4，unit-03:Module5-6',
        },
    },
    'physics': {
        '八年级': {
            '八上': 'unit-01:机械运动，unit-02:声现象，unit-03:物态变化，unit-04:光现象，unit-05:透镜',
            '八下': 'unit-01:力，unit-02:运动和力，unit-03:压强，unit-04:浮力，unit-05:功和机械能',
        },
        '九年级': {
            '九上': 'unit-01:内能，unit-02:电流和电路，unit-03:电压电阻，unit-04:欧姆定律',
            '九下': 'unit-01:电功率，unit-02:生活用电，unit-03:电与磁',
        },
    },
}

# 学生档案模板
STUDENT_PROFILE_TEMPLATE = """---
type: student-profile
name: {name}
grade: {grade}
school: {school}
created: {created}
updated: {updated}
tags:
  - 学生档案
  - {grade}
---

# 学生档案：{name}

> 学段：[[../mistakes/README|错题总览]]
> 知识库：[[../wiki/index|知识库首页]]

## 📋 基本信息

| 项目 | 内容 |
|------|------|
| 姓名 | {name} |
| 年级 | {grade} |
| 学校 | {school} |
| 班级 | {class_name} |
| 创建时间 | {created} |
| 最后更新 | {updated} |

## 📚 教材版本

| 学科 | 版本 | 备注 |
|------|------|------|
{textbook_table}

## 🗂️ 学期单元映射

{unit_mapping}

## 🎯 学习特点

- **优势学科**：{strength_subjects}
- **薄弱学科**：{weak_subjects}
- **薄弱知识点**：{weak_points}
- **常见错误类型**：{error_types}

## 🎯 学习目标

- **短期目标（1 个月）**：{goal_short}
- **中期目标（1 学期）**：{goal_mid}
- **长期目标（1 学年）**：{goal_long}

---

## 📊 统计概览

| 指标 | 数值 |
|------|------|
| 错题总数 | 0 |
| 本周新增 | 0 |
| 本月新增 | 0 |
| 已掌握（复习 5 轮） | 0 |
| 待复习 | 0 |

> 💡 统计数据将在录入错题后自动更新

---

## 📅 复习记录

| 日期 | 复习内容 | 完成度 | 签名 |
|------|---------|--------|------|
| | | | |

---

## 📝 备注

（其他需要记录的信息，如特殊学习需求、过敏史等）

---

## 🔗 快速链接

- [[../mistakes/README|错题总览]]
- [[../wiki/index|知识库首页]]
- [[../practice/README|变式练习]]
- [[../reports/README|分析报告]]

---

*最后更新：{updated}*
*本档案由 init-student.py 自动创建*
"""




def ask_question(question: str, options: list = None, default: str = None) -> str:
    """交互式提问"""
    if options:
        print(f"\n{question}")
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")
        while True:
            answer = input(f"请选择 (1-{len(options)}) [默认:{default or options[0]}]: ").strip()
            if not answer and default:
                return default
            if not answer:
                return options[0]
            try:
                idx = int(answer) - 1
                if 0 <= idx < len(options):
                    return options[idx]
            except ValueError:
                pass
            print("❌ 无效输入，请重试")
    else:
        answer = input(f"{question} [默认:{default}]: ").strip()
        return answer if answer else (default or '')


def select_subjects() -> list:
    """选择需要记录的学科"""
    print("\n📚 请选择需要记录的学科（多选，用逗号分隔）：")
    all_subjects = ['数学', '语文', '英语', '物理', '化学', '生物', '历史', '地理', '政治']
    for i, subj in enumerate(all_subjects, 1):
        print(f"  {i}. {subj}")
    
    answer = input("选择 (如 1,2,3 或全选) [默认:1,2,3]: ").strip()
    if not answer:
        return ['数学', '语文', '英语']
    
    if answer == 'all':
        return all_subjects
    
    try:
        indices = [int(x.strip()) - 1 for x in answer.split(',')]
        return [all_subjects[i] for i in indices if 0 <= i < len(all_subjects)]
    except:
        return ['数学', '语文', '英语']


def generate_textbook_table(selected_subjects: list) -> str:
    """生成教材版本表格"""
    lines = []
    default_versions = {
        '数学': '人教版',
        '语文': '部编版',
        '英语': '外研版',
        '物理': '人教版',
        '化学': '人教版',
        '生物': '人教版',
    }
    
    for subj in selected_subjects:
        version = ask_question(
            f"{subj} 教材版本",
            TEXTBOOK_VERSIONS.get(subj.lower(), ['其他']),
            default_versions.get(subj, '其他')
        )
        lines.append(f"| {subj} | {version} | |")
    
    return '\n'.join(lines)


def generate_unit_mapping(grade: str, selected_subjects: list) -> str:
    """生成学期单元映射"""
    lines = []
    lines.append("| 学科 | 学期 | 单元范围 |")
    lines.append("|------|------|---------|")
    
    for subj in selected_subjects:
        subj_key = subj.lower()
        if subj_key in UNIT_MAPPINGS and grade in UNIT_MAPPINGS[subj_key]:
            semesters = UNIT_MAPPINGS[subj_key][grade]
            for sem, units in semesters.items():
                lines.append(f"| {subj} | {sem} | {units} |")
    
    if len(lines) == 2:
        # 没有预置映射
        lines.append(f"| {selected_subjects[0]} | 当前学期 | （待补充） |")
    
    return '\n'.join(lines)


def create_student_profile(data: dict) -> str:
    """生成学生档案内容"""
    now = datetime.now().strftime('%Y-%m-%d')
    
    # 生成教材版本表格
    textbook_lines = []
    for subj, version in data.get('textbooks', {}).items():
        textbook_lines.append(f"| {subj} | {version} | |")
    textbook_table = '\n'.join(textbook_lines) if textbook_lines else '| 数学 | 人教版 | |\n| 语文 | 部编版 | |\n| 英语 | 外研版 | |'
    
    # 生成单元映射
    unit_mapping = data.get('unit_mapping', '| 学科 | 学期 | 单元范围 |\n|------|------|---------|\n| （待补充） |')
    
    return STUDENT_PROFILE_TEMPLATE.format(
        name=data['name'],
        grade=data['grade'],
        school=data.get('school', '待补充'),
        class_name=data.get('class_name', '待补充'),
        created=now,
        updated=now,
        textbook_table=textbook_table,
        unit_mapping=unit_mapping,
        strength_subjects=data.get('strength_subjects', '待补充'),
        weak_subjects=data.get('weak_subjects', '待补充'),
        weak_points=data.get('weak_points', '待补充'),
        error_types=data.get('error_types', '待补充'),
        goal_short=data.get('goal_short', '待补充'),
        goal_mid=data.get('goal_mid', '待补充'),
        goal_long=data.get('goal_long', '待补充'),
    )


def create_directory_structure(base_path: Path, name: str) -> None:
    """创建目录结构"""
    dirs = [
        base_path / 'mistakes',
        base_path / 'wiki' / 'concepts',
        base_path / 'wiki' / 'reviews',
        base_path / 'practice',
        base_path / 'reports',
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录：{d}")


def interactive_mode() -> dict:
    """交互式收集信息"""
    print("=" * 60)
    print("🎓 错题本 - 学生档案初始化向导")
    print("=" * 60)
    
    data = {}
    
    # 基本信息
    print("\n📋 第一步：基本信息")
    data['name'] = ask_question("学生姓名：")
    data['grade'] = ask_question("年级：", GRADES, default='八年级')
    data['school'] = ask_question("学校名称：", default='待补充')
    data['class_name'] = ask_question("班级：", default='待补充')
    
    # 选择学科
    print("\n📚 第二步：选择学科")
    selected_subjects = select_subjects()
    print(f"✅ 已选择：{', '.join(selected_subjects)}")
    
    # 教材版本
    print("\n📖 第三步：教材版本")
    data['textbooks'] = {}
    for subj in selected_subjects:
        version = ask_question(
            f"{subj} 教材版本",
            TEXTBOOK_VERSIONS.get(subj.lower(), ['其他']),
            default='人教版'
        )
        data['textbooks'][subj] = version
    
    # 单元映射
    print("\n🗂️ 第四步：学期单元映射")
    data['unit_mapping'] = generate_unit_mapping(data['grade'], selected_subjects)
    
    # 学习特点
    print("\n🎯 第五步：学习特点（可留空稍后补充）")
    data['strength_subjects'] = ask_question("优势学科：", default='待补充')
    data['weak_subjects'] = ask_question("薄弱学科：", default='待补充')
    data['weak_points'] = ask_question("薄弱知识点：", default='待补充')
    data['error_types'] = ask_question("常见错误类型：", default='待补充')
    
    # 学习目标
    print("\n🎯 第六步：学习目标（可留空稍后补充）")
    data['goal_short'] = ask_question("短期目标（1 个月）：", default='待补充')
    data['goal_mid'] = ask_question("中期目标（1 学期）：", default='待补充')
    data['goal_long'] = ask_question("长期目标（1 学年）：", default='待补充')
    
    return data


def main():
    parser = argparse.ArgumentParser(description='学生档案初始化向导')
    parser.add_argument('--name', help='学生姓名（非交互模式）')
    parser.add_argument('--grade', default='八年级', help='年级（非交互模式）')
    parser.add_argument('--school', default='待补充', help='学校名称')
    parser.add_argument('--output', help='输出目录（默认：data/mistake-notebook/students/）')
    parser.add_argument('--non-interactive', action='store_true', help='非交互模式')
    
    args = parser.parse_args()
    
    # 确定输出目录
    base_output = Path(args.output) if args.output else Path('data/mistake-notebook/students')
    
    if args.non_interactive and args.name:
        # 非交互模式
        data = {
            'name': args.name,
            'grade': args.grade,
            'school': args.school,
            'class_name': '待补充',
            'textbooks': {'数学': '人教版', '语文': '部编版', '英语': '外研版'},
            'unit_mapping': '| 学科 | 学期 | 单元范围 |\n|------|------|---------|\n| （待补充） |',
            'strength_subjects': '待补充',
            'weak_subjects': '待补充',
            'weak_points': '待补充',
            'error_types': '待补充',
            'goal_short': '待补充',
            'goal_mid': '待补充',
            'goal_long': '待补充',
        }
    else:
        # 交互模式
        data = interactive_mode()
    
    print("\n" + "=" * 60)
    print("📁 正在创建学生档案...")
    print("=" * 60)
    
    # 创建目录
    student_dir = base_output / data['name']
    create_directory_structure(student_dir, data['name'])
    
    # 创建学生档案
    profile_content = create_student_profile(data)
    profile_path = student_dir / 'profile.md'
    profile_path.write_text(profile_content, encoding='utf-8')
    print(f"✅ 创建学生档案：{profile_path}")
    
    # 完成提示
    print("\n" + "=" * 60)
    print("✅ 学生档案创建完成！")
    print("=" * 60)
    print(f"\n📁 档案位置：{student_dir}")
    print(f"\n📋 下一步：")
    print(f"  1. 编辑 profile.md 补充详细信息（学校、班级、学习目标等）")
    print(f"  2. 开始录入错题：对 AI 说\"这道题拍下来了，帮我归档\"")
    print(f"\n📚 常用命令：")
    print(f"  - 今天复习什么：python3 scripts/update-review.py --student \"{data['name']}\" --today")
    print(f"  - 生成练习：python3 scripts/generate-practice.py --student \"{data['name']}\" --knowledge \"知识点\"")
    print(f"  - 迁移到 Wiki: python3 scripts/migrate-to-wiki.py --student \"{data['name']}\"")
    print()


if __name__ == '__main__':
    main()
