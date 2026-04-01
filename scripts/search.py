#!/usr/bin/env python3
"""
错题检索脚本 - 支持标签、知识点、错误类型等多维度筛选

用法:
    python3 search.py --student <学生名> [筛选条件]

筛选条件:
    --tag <标签>          按标签筛选
    --knowledge <知识点>   按知识点筛选
    --error-type <类型>    按错误类型筛选
    --subject <学科>       按学科筛选
    --status <状态>        按状态筛选
    --unit <单元>          按单元筛选
    --unread              仅显示仍在 SRS 排程中的（未完成全部轮次）

功能:
    - 多维度筛选错题
    - 输出筛选结果列表
    - 支持导出
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
import re

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import mistake_srs as srs  # noqa: E402


def parse_frontmatter(content: str) -> dict:
    """解析 YAML Frontmatter（支持多行列表）"""
    data = {}
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        lines = match.group(1).strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # 处理列表（多行格式）
                if value == '' and i + 1 < len(lines) and lines[i+1].strip().startswith('-'):
                    value = []
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith('-'):
                        item = lines[i].strip().lstrip('-').strip()
                        value.append(item)
                        i += 1
                    data[key] = value
                    continue
                
                # 处理单行列表 [a, b, c]
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip().lstrip('-').strip() for v in value[1:-1].split(',')]
                # 处理布尔值
                elif value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                data[key] = value
            i += 1
    return data


def search_mistakes(student: str, filters: dict) -> list:
    """搜索错题"""
    results = []
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return results
    
    for mistake_file in base_path.rglob('mistake.md'):
        content = mistake_file.read_text(encoding='utf-8')
        frontmatter = parse_frontmatter(content)
        
        if not frontmatter:
            continue
        
        # 应用筛选条件
        match = True
        
        if 'tag' in filters:
            tags = frontmatter.get('tags', [])
            if filters['tag'] not in tags:
                match = False
        
        if 'knowledge' in filters:
            kp = frontmatter.get('knowledge-point', '')
            if filters['knowledge'].lower() not in kp.lower():
                match = False
        
        if 'error_type' in filters:
            et = frontmatter.get('error-type', '')
            if filters['error_type'].lower() not in et.lower():
                match = False
        
        if 'subject' in filters:
            if frontmatter.get('subject') != filters['subject']:
                match = False
        
        if 'status' in filters:
            if frontmatter.get('status') != filters['status']:
                match = False
        
        if 'unit' in filters:
            if frontmatter.get('unit') != filters['unit']:
                match = False
        
        if filters.get('unread', False):
            due = str(frontmatter.get('due-date', '')).strip().lower()
            if due in ('completed', 'done', 'none', ''):
                match = False
        
        if match:
            results.append({
                'id': frontmatter.get('id', 'unknown'),
                'subject': frontmatter.get('subject', ''),
                'grade': frontmatter.get('grade', ''),
                'semester': frontmatter.get('semester', ''),
                'unit': frontmatter.get('unit', ''),
                'unit_name': frontmatter.get('unit-name', ''),
                'knowledge_point': frontmatter.get('knowledge-point', ''),
                'error_type': frontmatter.get('error-type', ''),
                'tags': frontmatter.get('tags', []),
                'status': frontmatter.get('status', ''),
                'difficulty': frontmatter.get('difficulty', ''),
                'created': frontmatter.get('created', ''),
                'review_round': frontmatter.get('review-round', 0),
                'srs_complete': srs.srs_complete(frontmatter),
                'path': mistake_file
            })
    
    # 按创建日期排序（最新的在前）
    results.sort(key=lambda x: x['created'], reverse=True)
    
    return results


def list_all_tags(student: str) -> dict:
    """列出所有标签及其使用次数"""
    tag_count = {}
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return tag_count
    
    for mistake_file in base_path.rglob('mistake.md'):
        content = mistake_file.read_text(encoding='utf-8')
        frontmatter = parse_frontmatter(content)
        
        tags = frontmatter.get('tags', [])
        for tag in tags:
            tag_count[tag] = tag_count.get(tag, 0) + 1
    
    return tag_count


def list_all_knowledge_points(student: str) -> dict:
    """列出所有知识点及其使用次数"""
    kp_count = {}
    base_path = Path(f'data/mistake-notebook/students/{student}/mistakes')
    
    if not base_path.exists():
        return kp_count
    
    for mistake_file in base_path.rglob('mistake.md'):
        content = mistake_file.read_text(encoding='utf-8')
        frontmatter = parse_frontmatter(content)
        
        kp = frontmatter.get('knowledge-point', '')
        if kp:
            kp_count[kp] = kp_count.get(kp, 0) + 1
    
    return kp_count


def generate_search_results(results: list, student: str, filters: dict) -> str:
    """生成搜索结果"""
    filter_desc = ' + '.join([f"{k}={v}" for k, v in filters.items() if v != False])
    filter_desc = filter_desc or '全部'
    
    content = f"""---
type: search-results
student: {student}
filters: {filter_desc}
generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
---

# 🔍 错题检索结果

**学生**：[[../profile|{student}]]  
**筛选条件**：{filter_desc}  
**找到**：{len(results)} 道错题

---

## 📋 结果列表

"""
    
    if results:
        content += """| 日期 | 错题 ID | 学科 | 知识点 | 错误类型 | 状态 | 链接 |
|------|--------|------|--------|---------|------|------|
"""
        for r in results:
            rel_path = r['path'].relative_to(Path(f'data/mistake-notebook/students/{student}'))
            status_icon = '✅' if r['srs_complete'] else '🟡'
            content += f"| {r['created']} | {r['id']} | {r['subject']} | {r['knowledge_point']} | {r['error_type']} | {status_icon} {r['status']} | [[{rel_path}]] |\n"
    else:
        content += "未找到符合条件的错题。\n"
    
    content += f"""
---

## 🏷️ 热门标签

"""
    
    tags = list_all_tags(student)
    if tags:
        content += "| 标签 | 使用次数 |\n"
        content += "|------|---------|\n"
        for tag, count in sorted(tags.items(), key=lambda x: -x[1])[:20]:
            content += f"| #{tag} | {count} |\n"
    else:
        content += "暂无标签数据\n"
    
    content += f"""
---

## 🎯 知识点分布

"""
    
    kps = list_all_knowledge_points(student)
    if kps:
        content += "| 知识点 | 错题数 |\n"
        content += "|--------|--------|\n"
        for kp, count in sorted(kps.items(), key=lambda x: -x[1])[:20]:
            content += f"| {kp} | {count} |\n"
    else:
        content += "暂无知识点数据\n"
    
    content += f"""
---

## 🔗 相关链接

- [[../profile|返回学生主页]]
- [[./README|返回错题总览]]

---

**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    return content


def main():
    parser = argparse.ArgumentParser(description='错题检索')
    parser.add_argument('--student', required=True, help='学生姓名')
    parser.add_argument('--tag', help='按标签筛选')
    parser.add_argument('--knowledge', help='按知识点筛选')
    parser.add_argument('--error-type', dest='error_type', help='按错误类型筛选')
    parser.add_argument('--subject', help='按学科筛选')
    parser.add_argument('--status', help='按状态筛选')
    parser.add_argument('--unit', help='按单元筛选')
    parser.add_argument('--unread', action='store_true', help='仅显示未掌握的')
    parser.add_argument('--list-tags', action='store_true', help='列出所有标签')
    parser.add_argument('--list-kp', action='store_true', help='列出所有知识点')
    parser.add_argument('--output', help='输出文件路径（可选）')
    
    args = parser.parse_args()
    
    # 构建筛选条件
    filters = {}
    if args.tag:
        filters['tag'] = args.tag
    if args.knowledge:
        filters['knowledge'] = args.knowledge
    if args.error_type:
        filters['error_type'] = args.error_type
    if args.subject:
        filters['subject'] = args.subject
    if args.status:
        filters['status'] = args.status
    if args.unit:
        filters['unit'] = args.unit
    if args.unread:
        filters['unread'] = True
    
    # 特殊模式：列出标签或知识点
    if args.list_tags:
        tags = list_all_tags(args.student)
        print("🏷️  所有标签：")
        for tag, count in sorted(tags.items(), key=lambda x: -x[1]):
            print(f"  #{tag}: {count}")
        return
    
    if args.list_kp:
        kps = list_all_knowledge_points(args.student)
        print("🎯  所有知识点：")
        for kp, count in sorted(kps.items(), key=lambda x: -x[1]):
            print(f"  {kp}: {count}")
        return
    
    # 搜索
    print(f"正在搜索 {args.student} 的错题...")
    print(f"筛选条件：{filters}")
    results = search_mistakes(args.student, filters)
    print(f"找到 {len(results)} 道错题")
    
    # 生成结果
    content = generate_search_results(results, args.student, filters)
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(content, encoding='utf-8')
        print(f"已保存：{args.output}")
    else:
        # 默认保存到 search 目录
        output_dir = Path(f'data/mistake-notebook/students/{args.student}/search')
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M')
        filter_key = '-'.join([f"{k}-{v}" for k, v in filters.items() if v != False]) or 'all'
        output_path = output_dir / f'search-{timestamp}-{filter_key}.md'
        output_path.write_text(content, encoding='utf-8')
        print(f"已保存：{output_path}")


if __name__ == '__main__':
    main()
