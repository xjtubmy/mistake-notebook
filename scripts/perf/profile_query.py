#!/usr/bin/env python3
"""
性能分析脚本 - 分析 get_due_reviews() 性能瓶颈

使用方法：
    python -m scripts.perf.profile_query
"""

import cProfile
import pstats
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from io import StringIO
from typing import List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.services.review_service import ReviewService
from scripts.perf.generate_test_data import generate_test_dataset


def profile_get_due_reviews(num_mistakes: int = 1000, student_name: str = "性能测试学生") -> tuple[float, List]:
    """
    分析 get_due_reviews() 函数的性能
    
    Args:
        num_mistakes: 测试数据集中的错题数量
        student_name: 测试学生姓名
    
    Returns:
        (elapsed_time, due_reviews) 查询时间和到期错题列表
    """
    print(f"=" * 60)
    print(f"性能分析：get_due_reviews()")
    print(f"=" * 60)
    print(f"测试数据集：{num_mistakes} 道错题")
    print(f"测试学生：{student_name}")
    print()
    
    # 生成测试数据
    print("正在生成测试数据集...")
    start_gen = time.time()
    generate_test_dataset(num_mistakes, student_name)
    gen_time = time.time() - start_gen
    print(f"数据集生成完成：{gen_time:.2f} 秒")
    print()
    
    # 创建 ReviewService 实例
    service = ReviewService(student_name)
    
    # 性能分析
    print("开始性能分析...")
    print()
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    due_reviews = service.get_due_reviews()
    elapsed_time = time.time() - start_time
    
    profiler.disable()
    
    print(f"=" * 60)
    print(f"查询结果:")
    print(f"  - 到期复习错题数：{len(due_reviews)}")
    print(f"  - 查询耗时：{elapsed_time:.4f} 秒")
    print(f"=" * 60)
    print()
    
    # 输出性能统计
    print("性能热点分析 (Top 20):")
    print("-" * 60)
    
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    print(stream.getvalue())
    
    return elapsed_time, due_reviews


def benchmark_with_different_sizes() -> List[tuple[int, float, int]]:
    """
    测试不同数据规模下的性能表现
    
    Returns:
        测试结果列表 [(size, elapsed_time, due_count), ...]
    """
    print("=" * 70)
    print("性能基准测试：不同数据规模")
    print("=" * 70)
    print()
    
    test_sizes = [100, 500, 1000, 2000, 5000]
    results = []
    
    for size in test_sizes:
        student_name = f"性能测试_{size}"
        print(f"测试规模：{size} 道错题")
        
        # 生成数据
        generate_test_dataset(size, student_name)
        
        # 测试查询
        service = ReviewService(student_name)
        
        start_time = time.time()
        due_reviews = service.get_due_reviews()
        elapsed_time = time.time() - start_time
        
        results.append((size, elapsed_time, len(due_reviews)))
        
        print(f"  - 查询时间：{elapsed_time:.4f} 秒")
        print(f"  - 到期数量：{len(due_reviews)}")
        print(f"  - 平均每错题：{elapsed_time / size * 1000:.4f} 毫秒")
        print()
    
    # 汇总结果
    print("=" * 70)
    print("汇总结果:")
    print("-" * 70)
    print(f"{'错题数量':<12} {'查询时间 (秒)':<16} {'到期数量':<12} {'平均每错题 (ms)':<16}")
    print("-" * 70)
    for size, elapsed, due_count in results:
        print(f"{size:<12} {elapsed:<16.4f} {due_count:<12} {elapsed / size * 1000:<16.4f}")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="分析 get_due_reviews() 性能")
    parser.add_argument(
        "--size",
        type=int,
        default=1000,
        help="测试数据集大小（默认：1000）"
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="运行多规模基准测试"
    )
    parser.add_argument(
        "--student",
        type=str,
        default="性能测试学生",
        help="测试学生姓名（默认：性能测试学生）"
    )
    
    args = parser.parse_args()
    
    if args.benchmark:
        benchmark_with_different_sizes()
    else:
        profile_get_due_reviews(args.size, args.student)
