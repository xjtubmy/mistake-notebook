#!/usr/bin/env python3
"""
verify-links.py - 验证错题到知识点的链接是否有效

用法:
    python3 verify-links.py --student "曲凌松"
"""

import argparse
import os
from pathlib import Path

def check_links(student_dir: Path) -> list:
    """检查所有错题的 wiki 链接是否指向有效文件"""
    issues = []
    mistakes_dir = student_dir / "mistakes"
    
    for mistake_file in mistakes_dir.rglob("mistake.md"):
        content = mistake_file.read_text(encoding='utf-8')
        
        # 找出所有 wiki 链接
        for line in content.split('\n'):
            if 'wiki/concepts' in line and '[[' in line:
                # 提取链接路径
                start = line.find('[[') + 2
                end = line.find(']]')
                if end == -1:
                    continue
                
                link = line[start:end]
                # 处理 [[path|text]] 格式
                if '|' in link:
                    link = link.split('|')[0]
                
                # 解析相对路径（从 mistake_file.parent 开始）
                link = link.strip()
                if link.startswith('../../'):
                    # 从 mistake 文件所在目录解析相对路径
                    target_path = mistake_file.parent / link
                    # 规范化路径（解析 ../）
                    target = Path(os.path.normpath(str(target_path)))
                    
                    if not target.exists():
                        issues.append({
                            'file': mistake_file,
                            'link': link,
                            'target': target
                        })
    
    return issues

def main():
    parser = argparse.ArgumentParser(description="验证错题到知识点的链接")
    parser.add_argument("--student", required=True, help="学生姓名")
    parser.add_argument("--base-dir", default="/home/ubuntu/clawd/data/mistake-notebook/students", help="学生目录基路径")
    
    args = parser.parse_args()
    
    student_dir = Path(args.base_dir) / args.student
    
    if not student_dir.exists():
        print(f"❌ 学生目录不存在：{student_dir}")
        return 1
    
    print(f"🔗 验证学生 '{args.student}' 的错题链接...\n")
    
    issues = check_links(student_dir)
    
    if not issues:
        print("✅ 所有链接有效！")
        return 0
    else:
        print(f"❌ 发现 {len(issues)} 个无效链接:\n")
        for issue in issues:
            print(f"文件：{issue['file'].relative_to(student_dir)}")
            print(f"链接：{issue['link']}")
            print(f"目标：{issue['target']} (不存在)\n")
        return 1

if __name__ == "__main__":
    exit(main())
