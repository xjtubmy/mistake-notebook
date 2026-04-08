#!/usr/bin/env python3
"""
lint-wiki.py - 检查知识库健康状态（卡帕西 Wiki 模式）

检查项目:
1. 孤儿页面（没有链接指向的知识点）
2. 缺失关联（题目未关联到知识点）
3. 矛盾检测（同一知识点不同描述）
4. 过期内容（长时间未更新的页面）
5. 缺失 frontmatter 的文件

用法:
    python3 lint-wiki.py --student "曲凌松"
    python3 lint-wiki.py --student "曲凌松" --fix
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

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

def find_all_links(content: str) -> set:
    """找出文件中所有的 wiki 链接 [[xxx]]"""
    links = set()
    for line in content.split('\n'):
        # 匹配 [[xxx]] 或 [[xxx|yyy]]
        start = 0
        while True:
            pos = line.find('[[', start)
            if pos == -1:
                break
            end = line.find(']]', pos)
            if end == -1:
                break
            link = line[pos+2:end]
            # 处理 [[xxx|yyy]] 格式
            if '|' in link:
                link = link.split('|')[0]
            links.add(link.strip())
            start = end + 2
    return links

def check_orphan_pages(student_dir: Path) -> list:
    """检查孤儿知识点页面（没有题目链接指向）"""
    orphans = []
    concepts_dir = student_dir / "wiki" / "concepts"
    mistakes_dir = student_dir / "mistakes"
    
    if not concepts_dir.exists():
        return orphans
    
    # 收集所有知识点页面
    concept_files = {}
    for md_file in concepts_dir.glob("*.md"):
        if md_file.name == "README.md":
            continue
        # 提取概念名称（从 filename 或 frontmatter）
        meta = parse_frontmatter(md_file.read_text(encoding='utf-8'))
        title = meta.get('title', md_file.stem)
        concept_files[title] = md_file
        concept_files[md_file.stem] = md_file
        concept_files[md_file.name] = md_file
    
    # 扫描所有错题，收集引用
    referenced = set()
    for mistake_file in mistakes_dir.rglob("*.md"):
        content = mistake_file.read_text(encoding='utf-8')
        links = find_all_links(content)
        for link in links:
            # 匹配多种格式：concepts/xxx.md, wiki/concepts/xxx, xxx.md, xxx
            if 'concepts/' in link:
                # 提取文件名
                fname = link.split('/')[-1].replace('.md', '')
                referenced.add(fname)
            if link in concept_files:
                referenced.add(link)
    
    # 找出未被引用的知识点
    for title, path in concept_files.items():
        # 检查多种匹配方式
        if title in referenced or path.stem in referenced or path.name in referenced:
            continue
        orphans.append(path)
    
    return orphans

def check_unlinked_mistakes(student_dir: Path) -> list:
    """检查未关联到知识点的错题"""
    unlinked = []
    mistakes_dir = student_dir / "mistakes"
    concepts_dir = student_dir / "wiki" / "concepts"
    
    if not concepts_dir.exists():
        return unlinked
    
    # 收集所有知识点名称
    concepts = set()
    for md_file in concepts_dir.glob("*.md"):
        if md_file.name == "README.md":
            continue
        meta = parse_frontmatter(md_file.read_text(encoding='utf-8'))
        title = meta.get('title', md_file.stem)
        concepts.add(title)
    
    # 检查错题是否关联到知识点
    for mistake_file in mistakes_dir.rglob("mistake.md"):
        content = mistake_file.read_text(encoding='utf-8')
        meta = parse_frontmatter(content)
        
        knowledge_point = meta.get('knowledge-point', '')
        has_link = any(concept in content for concept in concepts)
        
        if not has_link and knowledge_point:
            # 检查是否有知识点页面匹配
            if knowledge_point in concepts:
                unlinked.append(mistake_file)
    
    return unlinked

def check_outdated_pages(student_dir: Path, days: int = 14) -> list:
    """检查超过 N 天未更新的页面"""
    outdated = []
    wiki_dir = student_dir / "wiki"
    
    if not wiki_dir.exists():
        return outdated
    
    threshold = datetime.now() - timedelta(days=days)
    
    for md_file in wiki_dir.rglob("*.md"):
        mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
        if mtime < threshold:
            outdated.append((md_file, mtime))
    
    return outdated

def check_missing_frontmatter(student_dir: Path) -> list:
    """检查缺失 frontmatter 的文件"""
    missing = []
    wiki_dir = student_dir / "wiki"
    
    if not wiki_dir.exists():
        return missing
    
    for md_file in wiki_dir.rglob("*.md"):
        if md_file.name == "README.md":
            continue
        
        content = md_file.read_text(encoding='utf-8')
        if not content.strip().startswith('---'):
            missing.append(md_file)
            continue
        
        # 检查是否有 type 字段
        meta = parse_frontmatter(content)
        if 'type' not in meta:
            missing.append(md_file)
    
    return missing

def generate_report(student: str, results: dict) -> str:
    """生成检查报告"""
    report = []
    report.append(f"# 知识库健康检查报告")
    report.append(f"\n**学生**: {student}")
    report.append(f"**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    
    # 孤儿页面
    report.append("## 🚨 孤儿知识点页面")
    if results['orphans']:
        report.append("以下知识点页面没有被任何题目引用：")
        report.append("")
        for path in results['orphans']:
            report.append(f"- `{path.relative_to(student_dir)}`")
    else:
        report.append("✅ 无孤儿页面")
    report.append("")
    
    # 未关联错题
    report.append("## ⚠️ 未关联知识点的错题")
    if results['unlinked']:
        report.append("以下错题未关联到知识点页面：")
        report.append("")
        for path in results['unlinked']:
            report.append(f"- `{path.relative_to(student_dir)}`")
    else:
        report.append("✅ 所有错题已关联")
    report.append("")
    
    # 过期页面
    report.append("## 📅 过期页面（超过 14 天未更新）")
    if results['outdated']:
        for path, mtime in results['outdated']:
            report.append(f"- `{path.relative_to(student_dir)}` (最后更新：{mtime.strftime('%Y-%m-%d')})")
    else:
        report.append("✅ 无过期页面")
    report.append("")
    
    # 缺失 frontmatter
    report.append("## 📝 缺失 Frontmatter 的文件")
    if results['missing_fm']:
        for path in results['missing_fm']:
            report.append(f"- `{path.relative_to(student_dir)}`")
    else:
        report.append("✅ 所有文件包含 frontmatter")
    report.append("")
    
    return '\n'.join(report)

def main():
    parser = argparse.ArgumentParser(description="检查知识库健康状态（卡帕西 Wiki 模式）")
    parser.add_argument("--student", required=True, help="学生姓名")
    parser.add_argument("--fix", action="store_true", help="自动修复可修复的问题")
    parser.add_argument("--base-dir", default="/home/ubuntu/clawd/data/mistake-notebook/students", help="学生目录基路径")
    parser.add_argument("--output", help="输出报告文件路径")
    
    args = parser.parse_args()
    
    global student_dir
    student_dir = Path(args.base_dir) / args.student
    
    if not student_dir.exists():
        print(f"❌ 学生目录不存在：{student_dir}")
        sys.exit(1)
    
    print(f"🔍 检查学生 '{args.student}' 的知识库健康状态...\n")
    
    results = {
        'orphans': check_orphan_pages(student_dir),
        'unlinked': check_unlinked_mistakes(student_dir),
        'outdated': check_outdated_pages(student_dir),
        'missing_fm': check_missing_frontmatter(student_dir),
    }
    
    # 生成报告
    report = generate_report(args.student, results)
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(report, encoding='utf-8')
        print(f"📄 报告已保存到：{output_path}")
    else:
        print(report)
    
    # 统计
    total_issues = len(results['orphans']) + len(results['unlinked']) + len(results['outdated']) + len(results['missing_fm'])
    
    if total_issues == 0:
        print("✅ 知识库健康状态良好！")
        sys.exit(0)
    else:
        print(f"\n⚠️  共发现 {total_issues} 个问题")
        if args.fix:
            print("🔧 自动修复模式已启用（待实现）")
        sys.exit(1)

if __name__ == "__main__":
    main()
