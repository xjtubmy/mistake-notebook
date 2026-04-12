#!/usr/bin/env python3
"""
migrate-to-wiki.py - 批量迁移错题到 Wiki 模式（卡帕西 LLM Wiki）

功能:
1. 扫描 mistakes/ 目录下所有错题
2. 按知识点自动分组
3. 创建知识点页面（如不存在）
4. 建立错题到知识点的双向链接
5. 生成迁移报告

用法:
    python3 migrate-to-wiki.py --student <学生名>
    python3 migrate-to-wiki.py --student <学生名> --dry-run  # 预览不执行
    python3 migrate-to-wiki.py --student <学生名> --subject math  # 按学科迁移
"""

import argparse
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 知识点→学科映射（用于自动分类）
KNOWLEDGE_SUBJECT_MAP = {
    # 物理
    '力的合成': 'physics',
    '牛顿第一定律': 'physics',
    '惯性': 'physics',
    '欧姆定律': 'physics',
    '浮力': 'physics',
    '压强': 'physics',
    '杠杆': 'physics',
    '电功率': 'physics',
    # 数学
    '一元一次方程': 'math',
    '二次函数': 'math',
    '勾股定理': 'math',
    '三角形全等': 'math',
    '全等三角形': 'math',
    '平行四边形': 'math',
    # 英语
    '现在完成时': 'english',
    '一般过去时': 'english',
    '定语从句': 'english',
    '被动语态': 'english',
    # 化学
    '化学方程式': 'chemistry',
}

# 知识点页面模板
CONCEPT_TEMPLATE = """---
type: concept
title: {title}
subject: {subject}
stage: middle
grade: {grade}
confidence: low
created: {created}
updated: {updated}
tags:
  - 知识点
  - {subject}
---

# 概念：{title}

## 📌 TLDR
{tldr}

---

## 📖 核心定义

（待补充：核心概念定义、公式、定理）

---

## 🔑 解题步骤

（待补充：典型解题方法和步骤）

---

## ❌ 常见错误

| 错误类型 | 表现 | 纠正 |
|---------|------|------|
| 概念不清 | 对基本概念理解错误 | 回归课本，重新学习概念定义 |
| 计算错误 | 计算过程出错 | 每天 5 分钟练习，养成验算习惯 |

---

## 📚 关联题目

{questions}

---

## 🎯 变式练习

**生成命令**：
```bash
python3 scripts/generate-practice.py --student {student} --knowledge "{title}" --count 3
```

---

## 📅 学习轨迹

| 日期 | 事件 | 掌握程度 |
|------|------|---------|
| {created} | 建立概念页面 | 🟡 初步理解 |

---

## 🔗 相关链接

- [[../../mistakes/README|返回错题总览]]
- [[../index|回到知识库首页]]

---

*最后更新：{updated}*
*本页面由 migrate-to-wiki.py 自动创建*
"""


def parse_frontmatter(content: str) -> dict:
    """解析 YAML frontmatter"""
    meta = {}
    in_frontmatter = False
    
    for line in content.split('\n'):
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                break
        
        if in_frontmatter and ':' in line:
            key, value = line.split(':', 1)
            meta[key.strip()] = value.strip()
    
    return meta


def find_all_mistakes(student_dir: Path, subject: str = None) -> list:
    """扫描所有错题文件"""
    mistakes = []
    mistakes_dir = student_dir / "mistakes"
    
    if not mistakes_dir.exists():
        return mistakes
    
    for md_file in mistakes_dir.rglob("mistake.md"):
        content = md_file.read_text(encoding='utf-8')
        meta = parse_frontmatter(content)
        
        # 学科筛选
        if subject and meta.get('subject') != subject:
            continue
        
        mistakes.append({
            'path': md_file,
            'meta': meta,
            'content': content
        })
    
    return mistakes


def group_by_knowledge(mistakes: list) -> dict:
    """按知识点分组错题"""
    groups = defaultdict(list)
    
    for m in mistakes:
        kp = m['meta'].get('knowledge-point', '未分类')
        if not kp or kp == '':
            kp = '未分类'
        groups[kp].append(m)
    
    return groups


def get_subject_for_knowledge(knowledge: str, default_meta: dict = None) -> str:
    """获取知识点对应的学科"""
    # 先查映射表
    if knowledge in KNOWLEDGE_SUBJECT_MAP:
        return KNOWLEDGE_SUBJECT_MAP[knowledge]
    
    # 再查错题元数据
    if default_meta:
        return default_meta.get('subject', 'unknown')
    
    return 'unknown'


def generate_tldr(knowledge: str) -> str:
    """生成知识点 TLDR 摘要"""
    tldr_templates = {
        '欧姆定律': '导体中的电流与电压成正比，与电阻成反比。公式：I = U/R',
        '浮力': '浸在液体中的物体受到向上的力，大小等于排开液体的重力。公式：F浮 = ρ液 gV排',
        '勾股定理': '直角三角形两直角边的平方和等于斜边的平方。公式：a² + b² = c²',
        '一元一次方程': '只含有一个未知数，且未知数的最高次数为 1 的方程。标准形式：ax + b = 0',
        '二次函数': '形如 y = ax² + bx + c 的函数，图像是抛物线',
        '现在完成时': '表示过去发生的动作对现在有影响，或从过去持续到现在的动作。结构：have/has + 过去分词',
        '定语从句': '用一个句子修饰名词或代词，被修饰的词叫先行词',
    }
    return tldr_templates.get(knowledge, f'关于"{knowledge}"的核心概念和方法')


def generate_questions_list(mistakes: list, student_dir: Path) -> str:
    """生成关联题目列表（带 wikilink）"""
    lines = []
    for i, m in enumerate(mistakes[:10], 1):  # 最多显示 10 题
        rel_path = m['path'].relative_to(student_dir)
        kp = m['meta'].get('knowledge-point', '')
        subject = m['meta'].get('subject', '')
        unit = m['meta'].get('unit-name', '')
        
        # 生成 wikilink
        link = f"[[{rel_path.parent}|{kp}]]"
        lines.append(f"{i}. {link}（{subject}·{unit}）")
    
    if len(mistakes) > 10:
        lines.append(f"\n*还有 {len(mistakes) - 10} 道题目，详见错题目录*")
    
    return '\n'.join(lines)


def create_concept_page(student_dir: Path, knowledge: str, mistakes: list, dry_run: bool = False) -> Path:
    """创建知识点页面"""
    concepts_dir = student_dir / "wiki" / "concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取学科
    subject = get_subject_for_knowledge(knowledge, mistakes[0]['meta'] if mistakes else None)
    
    # 生成文件名
    filename = f"{knowledge}.md"
    concept_path = concepts_dir / filename
    
    # 检查是否已存在
    if concept_path.exists():
        print(f"⚠️  知识点页面已存在：{concept_path}")
        return concept_path
    
    if dry_run:
        print(f"📄 [预览] 将创建：{concept_path}")
        return concept_path
    
    # 生成页面内容
    now = datetime.now().strftime('%Y-%m-%d')
    student = student_dir.name
    
    content = CONCEPT_TEMPLATE.format(
        title=knowledge,
        subject=subject,
        grade='八年级',  # 默认值
        created=now,
        updated=now,
        tldr=generate_tldr(knowledge),
        questions=generate_questions_list(mistakes, student_dir),
        student=student,
    )
    
    concept_path.write_text(content, encoding='utf-8')
    print(f"✅ 创建知识点页面：{concept_path}")
    
    return concept_path


def add_link_to_mistake(mistake: dict, knowledge: str, dry_run: bool = False) -> bool:
    """在错题文件中添加知识点链接"""
    content = mistake['content']
    
    # 检查是否已有链接
    if f'[[wiki/concepts/{knowledge}' in content or f'[[{knowledge}]]' in content:
        return False
    
    # 在 frontmatter 后添加 wikilink
    fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match:
        return False
    
    insert_pos = fm_match.end()
    link_text = f"\n**关联知识点**：[[wiki/concepts/{knowledge}|{knowledge}]]\n"
    
    if dry_run:
        print(f"🔗 [预览] 将添加链接到：{mistake['path']}")
        return True
    
    new_content = content[:insert_pos] + link_text + content[insert_pos:]
    mistake['path'].write_text(new_content, encoding='utf-8')
    print(f"✅ 添加知识点链接：{mistake['path']}")
    
    return True


def generate_report(stats: dict, output_path: Path) -> None:
    """生成迁移报告"""
    report = f"""# Wiki 迁移报告

**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 统计摘要

| 指标 | 数量 |
|------|------|
| 扫描错题总数 | {stats['total_mistakes']} |
| 涉及知识点数 | {stats['total_concepts']} |
| 创建知识点页面 | {stats['created_pages']} |
| 添加链接数 | {stats['added_links']} |
| 跳过（已关联） | {stats['skipped']} |

## 📚 知识点分布

| 知识点 | 题目数 | 学科 | 页面状态 |
|--------|--------|------|---------|
{stats['concept_table']}

## ✅ 下一步建议

1. 检查新创建的知识点页面，补充核心定义和解题步骤
2. 运行 `lint-wiki.py` 检查知识库健康状态
3. 在 Obsidian 中查看图谱，确认双向链接正常

---

*本报告由 migrate-to-wiki.py 自动生成*
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding='utf-8')
    print(f"📝 迁移报告已保存：{output_path}")


def main():
    parser = argparse.ArgumentParser(description='批量迁移错题到 Wiki 模式')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--subject', help='学科筛选（可选）')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改文件')
    parser.add_argument('--output', help='报告输出路径（可选）')
    
    args = parser.parse_args()
    
    student_dir = Path(f'data/mistake-notebook/students/{args.student}')
    
    if not student_dir.exists():
        print(f"❌ 学生目录不存在：{student_dir}")
        sys.exit(1)
    
    print(f"🔍 开始扫描学生：{args.student}")
    if args.subject:
        print(f"📌 学科筛选：{args.subject}")
    if args.dry_run:
        print("⚠️  预览模式，不会修改任何文件")
    print()
    
    # 扫描错题
    mistakes = find_all_mistakes(student_dir, args.subject)
    print(f"📚 找到 {len(mistakes)} 道错题")
    
    if not mistakes:
        print("✅ 没有错题需要迁移")
        return
    
    # 按知识点分组
    groups = group_by_knowledge(mistakes)
    print(f"📋 涉及 {len(groups)} 个知识点")
    print()
    
    # 统计
    stats = {
        'total_mistakes': len(mistakes),
        'total_concepts': len(groups),
        'created_pages': 0,
        'added_links': 0,
        'skipped': 0,
        'concept_table': ''
    }
    
    concept_rows = []
    
    # 创建知识点页面
    for knowledge, mistakes_list in sorted(groups.items()):
        print(f"📖 处理知识点：{knowledge} ({len(mistakes_list)} 题)")
        
        # 创建页面
        concept_path = create_concept_page(student_dir, knowledge, mistakes_list, args.dry_run)
        if concept_path and not args.dry_run:
            if concept_path.exists():
                stats['created_pages'] += 1
        
        # 添加链接到错题
        for m in mistakes_list:
            if add_link_to_mistake(m, knowledge, args.dry_run):
                stats['added_links'] += 1
            else:
                stats['skipped'] += 1
        
        # 统计表
        subject = get_subject_for_knowledge(knowledge, mistakes_list[0]['meta'] if mistakes_list else None)
        status = '✅ 已创建' if not args.dry_run else '📄 待创建'
        concept_rows.append(f"| {knowledge} | {len(mistakes_list)} | {subject} | {status} |")
    
    stats['concept_table'] = '\n'.join(concept_rows)
    
    # 生成报告
    report_path = args.output or student_dir / "wiki" / "reports" / f"migration-{datetime.now().strftime('%Y%m%d')}.md"
    if not args.dry_run:
        generate_report(stats, report_path)
    
    print()
    print("=" * 50)
    print("📊 迁移完成摘要")
    print("=" * 50)
    print(f"扫描错题总数：{stats['total_mistakes']}")
    print(f"涉及知识点数：{stats['total_concepts']}")
    print(f"创建知识点页面：{stats['created_pages']}")
    print(f"添加链接数：{stats['added_links']}")
    print(f"跳过（已关联）：{stats['skipped']}")
    print()


if __name__ == '__main__':
    main()
