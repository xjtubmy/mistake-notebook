#!/usr/bin/env python3
"""
create-concept.py - 基于现有错题自动生成知识点页面（卡帕西 Wiki 模式）

用法:
    python3 create-concept.py --student "曲凌松" --knowledge "程序运算与不等式组"
    python3 create-concept.py --student "曲凌松" --scan  # 扫描所有未关联的知识点
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# 知识点模板
CONCEPT_TEMPLATE = """---
type: concept
title: {title}
subject: {subject}
stage: middle
grade: {grade}
semester: {semester}
unit: {unit}
confidence: low
created: {created}
updated: {updated}
sources:
{sources}
related_concepts:
  - {related}
tags:
  - {tags}
---

# 概念：{title}

## 📌 TLDR
{tldr}

---

## 📖 核心定义

{definition}

---

## 🔑 解题步骤

{steps}

---

## ❌ 常见错误

| 错误类型 | 表现 | 纠正 |
|---------|------|------|
| {errors} |

---

## 📚 关联题目

**当前题目**：
{questions}

---

## 🎯 变式练习

**生成命令**：
```bash
python3 skills/mistake-notebook/scripts/generate-practice.py \\
  --student {student} \\
  --knowledge "{title}" \\
  --count 3
```

---

## 📅 学习轨迹

| 日期 | 事件 | 掌握程度 |
|------|------|---------|
| {created} | 建立概念页面 | 🟡 初步理解 |

---

## 🔗 相关链接

- 前置概念：[[前置概念]]
- 后置概念：[[后置概念]]
- 相关概念：[[相关概念]]

---

**最后更新**：{updated}
"""

def find_mistakes_by_knowledge(student_dir: Path, knowledge: str) -> list:
    """查找包含指定知识点的所有错题"""
    mistakes = []
    mistakes_dir = student_dir / "mistakes"
    
    if not mistakes_dir.exists():
        return mistakes
    
    for md_file in mistakes_dir.rglob("mistake.md"):
        content = md_file.read_text(encoding='utf-8')
        if knowledge in content:
            mistakes.append(md_file)
    
    return mistakes

def extract_metadata(mistake_path: Path) -> dict:
    """从错题文件中提取元数据"""
    content = mistake_path.read_text(encoding='utf-8')
    meta = {}
    
    # 简单解析 YAML frontmatter
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

def generate_sources(mistakes: list, student_dir: Path) -> str:
    """生成 sources 字段"""
    lines = []
    for m in mistakes:
        rel_path = m.relative_to(student_dir.parent)
        lines.append(f"  - {rel_path}")
    return '\n'.join(lines)

def generate_questions(mistakes: list, student_dir: Path) -> str:
    """生成关联题目列表"""
    lines = []
    for m in mistakes:
        rel_path = m.relative_to(student_dir)
        meta = extract_metadata(m)
        difficulty = meta.get('difficulty', '⭐⭐⭐')
        q_id = meta.get('id', m.stem)
        lines.append(f"- [[{rel_path}|{q_id}]] {difficulty}")
    return '\n'.join(lines)

def create_concept_page(student: str, knowledge: str, base_dir: Path = None):
    """创建知识点页面"""
    if base_dir is None:
        base_dir = Path("/home/ubuntu/clawd/data/mistake-notebook/students")
    
    student_dir = base_dir / student
    if not student_dir.exists():
        print(f"❌ 学生目录不存在：{student_dir}")
        return False
    
    # 查找相关错题
    mistakes = find_mistakes_by_knowledge(student_dir, knowledge)
    if not mistakes:
        print(f"⚠️  未找到包含知识点'{knowledge}'的错题")
        return False
    
    print(f"✅ 找到 {len(mistakes)} 道相关题目")
    
    # 提取元数据（从第一道题）
    meta = extract_metadata(mistakes[0])
    
    # 生成相对路径
    sources = generate_sources(mistakes, student_dir)
    questions = generate_questions(mistakes, student_dir)
    
    # 创建概念页面
    wiki_concepts_dir = student_dir / "wiki" / "concepts"
    wiki_concepts_dir.mkdir(parents=True, exist_ok=True)
    
    # 文件名：知识点的简化版本
    filename = knowledge.replace(" ", "").replace("与", "-").replace("的", "") + ".md"
    output_path = wiki_concepts_dir / filename
    
    # 填充模板
    today = datetime.now().strftime("%Y-%m-%d")
    content = CONCEPT_TEMPLATE.format(
        title=knowledge,
        subject=meta.get('subject', 'unknown'),
        grade=meta.get('grade', 'grade-8'),
        semester=meta.get('semester', 'semester-2'),
        unit=meta.get('unit', 'unit-01'),
        created=today,
        updated=today,
        sources=sources,
        related=knowledge,
        tags=knowledge,
        tldr=f"[待完善] {knowledge}的核心概念总结...",
        definition="[待完善] 详细定义和解释...",
        steps="[待完善] 解题步骤...",
        errors="待完善 | 待完善 | 待完善",
        questions=questions,
        student=student,
    )
    
    # 写入文件
    output_path.write_text(content, encoding='utf-8')
    print(f"✅ 已创建：{output_path}")
    
    return True

def scan_all_knowledge(student: str, base_dir: Path = None):
    """扫描学生所有错题，提取未创建的知识点"""
    if base_dir is None:
        base_dir = Path("/home/ubuntu/clawd/data/mistake-notebook/students")
    
    student_dir = base_dir / student
    if not student_dir.exists():
        print(f"❌ 学生目录不存在：{student_dir}")
        return
    
    # 收集所有知识点
    all_knowledge = set()
    mistakes_dir = student_dir / "mistakes"
    
    for md_file in mistakes_dir.rglob("mistake.md"):
        content = md_file.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if line.startswith('knowledge-point:'):
                kp = line.split(':', 1)[1].strip()
                all_knowledge.add(kp)
    
    # 检查已创建的知识点
    wiki_concepts_dir = student_dir / "wiki" / "concepts"
    existing = set()
    if wiki_concepts_dir.exists():
        for md_file in wiki_concepts_dir.glob("*.md"):
            if md_file.name != "README.md":
                existing.add(md_file.stem)
    
    # 输出结果
    print(f"\n📊 学生 '{student}' 知识点统计")
    print(f"=" * 50)
    print(f"总知识点数：{len(all_knowledge)}")
    print(f"已创建：{len(existing)}")
    print(f"待创建：{len(all_knowledge) - len(existing)}")
    print()
    
    for kp in sorted(all_knowledge):
        status = "✅" if kp in existing or kp.replace(" ", "").replace("与", "-").replace("的", "") in existing else "⏳"
        print(f"{status} {kp}")

def main():
    parser = argparse.ArgumentParser(description="创建知识点页面（卡帕西 Wiki 模式）")
    parser.add_argument("--student", required=True, help="学生姓名")
    parser.add_argument("--knowledge", help="知识点名称（与 --scan 互斥）")
    parser.add_argument("--scan", action="store_true", help="扫描所有未创建的知识点")
    parser.add_argument("--base-dir", default="/home/ubuntu/clawd/data/mistake-notebook/students", help="学生目录基路径")
    
    args = parser.parse_args()
    
    if args.scan:
        scan_all_knowledge(args.student, Path(args.base_dir))
    elif args.knowledge:
        success = create_concept_page(args.student, args.knowledge, Path(args.base_dir))
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
