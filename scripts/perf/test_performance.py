#!/usr/bin/env python3
"""
性能测试 - 验证优化后的查询性能

使用方法：
    python -m scripts.perf.test_performance
"""

import sys
import time
from datetime import date
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.services.review_service import ReviewService
from scripts.perf.generate_test_data import generate_test_dataset, clear_test_data


def test_query_performance(
    num_mistakes: int = 1000,
    student_name: str = "性能测试学生",
    target_time: float = 2.0,
    use_parallel: bool = True,
) -> tuple[bool, float, int]:
    """
    测试查询性能
    
    Args:
        num_mistakes: 测试错题数量
        student_name: 学生姓名
        target_time: 目标查询时间（秒）
        use_parallel: 是否使用并行处理
    
    Returns:
        (passed, elapsed_time, due_count) 测试结果
    """
    print("=" * 70)
    print(f"性能测试：{num_mistakes} 道错题查询")
    print(f"目标时间：< {target_time} 秒")
    print(f"并行处理：{'启用' if use_parallel else '禁用'}")
    print("=" * 70)
    
    # 清理旧数据并生成新数据
    print("\n准备测试数据...")
    clear_test_data(student_name)
    generate_test_dataset(num_mistakes, student_name)
    
    # 创建 ReviewService（启用并行）
    service = ReviewService(
        student_name,
        use_parallel=use_parallel,
        max_workers=8,
    )
    
    # 预热缓存（第一次查询会建立缓存）
    print("\n预热缓存...")
    _ = service.get_due_reviews()
    
    # 正式测试（3 次取平均）
    print("\n执行性能测试（3 次平均）...")
    elapsed_times = []
    due_counts = []
    
    for i in range(3):
        start_time = time.time()
        due_reviews = service.get_due_reviews()
        elapsed_time = time.time() - start_time
        
        elapsed_times.append(elapsed_time)
        due_counts.append(len(due_reviews))
        
        print(f"  第 {i + 1} 次：{elapsed_time:.4f} 秒，到期 {len(due_reviews)} 道")
    
    avg_time = sum(elapsed_times) / len(elapsed_times)
    avg_due = sum(due_counts) / len(due_counts)
    
    print("\n" + "=" * 70)
    print(f"测试结果:")
    print(f"  - 平均查询时间：{avg_time:.4f} 秒")
    print(f"  - 平均到期数量：{avg_due:.0f} 道")
    print(f"  - 目标时间：{target_time} 秒")
    print(f"  - 性能达标：{'✓ PASS' if avg_time < target_time else '✗ FAIL'}")
    print("=" * 70)
    
    # 清理测试数据
    clear_test_data(student_name)
    
    return avg_time < target_time, avg_time, int(avg_due)


def compare_parallel_vs_serial() -> tuple[float, float, float]:
    """
    对比并行和串行处理的性能差异
    """
    print("\n" + "=" * 70)
    print("对比测试：并行 vs 串行")
    print("=" * 70)
    
    num_mistakes = 2000
    student_name_parallel = "性能测试_并行"
    student_name_serial = "性能测试_串行"
    
    # 生成测试数据
    print("\n生成测试数据...")
    generate_test_dataset(num_mistakes, student_name_parallel)
    generate_test_dataset(num_mistakes, student_name_serial)
    
    # 测试并行处理
    print("\n测试并行处理...")
    service_parallel = ReviewService(
        student_name_parallel,
        use_parallel=True,
        max_workers=8,
    )
    
    start_time = time.time()
    due_parallel = service_parallel.get_due_reviews()
    time_parallel = time.time() - start_time
    
    print(f"  并行查询时间：{time_parallel:.4f} 秒")
    
    # 测试串行处理
    print("\n测试串行处理...")
    service_serial = ReviewService(
        student_name_serial,
        use_parallel=False,
    )
    
    start_time = time.time()
    due_serial = service_serial.get_due_reviews()
    time_serial = time.time() - start_time
    
    print(f"  串行查询时间：{time_serial:.4f} 秒")
    
    # 计算加速比
    speedup = time_serial / time_parallel if time_parallel > 0 else 0
    
    print("\n" + "=" * 70)
    print(f"对比结果:")
    print(f"  - 并行时间：{time_parallel:.4f} 秒")
    print(f"  - 串行时间：{time_serial:.4f} 秒")
    print(f"  - 加速比：{speedup:.2f}x")
    print("=" * 70)
    
    # 清理
    clear_test_data(student_name_parallel)
    clear_test_data(student_name_serial)
    
    return time_parallel, time_serial, speedup


def test_cache_effectiveness() -> tuple[float, float]:
    """
    测试缓存效果
    """
    print("\n" + "=" * 70)
    print("缓存效果测试")
    print("=" * 70)
    
    num_mistakes = 1000
    student_name = "性能测试_缓存"
    
    # 生成测试数据
    print("\n生成测试数据...")
    generate_test_dataset(num_mistakes, student_name)
    
    service = ReviewService(student_name, use_parallel=True)
    
    # 第一次查询（无缓存）
    print("\n第一次查询（无缓存）...")
    start_time = time.time()
    due_1 = service.get_due_reviews()
    time_1 = time.time() - start_time
    print(f"  查询时间：{time_1:.4f} 秒")
    
    # 第二次查询（有缓存）
    print("\n第二次查询（有缓存）...")
    start_time = time.time()
    due_2 = service.get_due_reviews()
    time_2 = time.time() - start_time
    print(f"  查询时间：{time_2:.4f} 秒")
    
    # 第三次查询（有缓存）
    print("\n第三次查询（有缓存）...")
    start_time = time.time()
    due_3 = service.get_due_reviews()
    time_3 = time.time() - start_time
    print(f"  查询时间：{time_3:.4f} 秒")
    
    # 清除缓存后查询
    print("\n清除缓存后查询...")
    from scripts.core.file_ops import clear_directory_cache
    clear_directory_cache(service.student_dir)
    
    start_time = time.time()
    due_4 = service.get_due_reviews()
    time_4 = time.time() - start_time
    print(f"  查询时间：{time_4:.4f} 秒")
    
    print("\n" + "=" * 70)
    print(f"缓存效果:")
    print(f"  - 无缓存：{time_1:.4f} 秒")
    print(f"  - 有缓存（平均）：{(time_2 + time_3) / 2:.4f} 秒")
    print(f"  - 缓存加速：{time_1 / ((time_2 + time_3) / 2):.2f}x")
    print("=" * 70)
    
    # 清理
    clear_test_data(student_name)
    
    return time_1, (time_2 + time_3) / 2


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="性能测试")
    parser.add_argument(
        "--size",
        type=int,
        default=1000,
        help="测试数据规模（默认：1000）"
    )
    parser.add_argument(
        "--target",
        type=float,
        default=2.0,
        help="目标查询时间（秒，默认：2.0）"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="运行并行 vs 串行对比测试"
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="运行缓存效果测试"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有测试"
    )
    
    args = parser.parse_args()
    
    all_passed = True
    
    # 基本性能测试
    if args.all or not (args.compare or args.cache):
        passed, elapsed, due_count = test_query_performance(
            args.size,
            "性能测试学生",
            args.target,
            use_parallel=True,
        )
        all_passed = all_passed and passed
    
    # 对比测试
    if args.all or args.compare:
        compare_parallel_vs_serial()
    
    # 缓存测试
    if args.all or args.cache:
        test_cache_effectiveness()
    
    # 最终结果
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ 所有性能测试通过")
    else:
        print("✗ 部分性能测试未通过")
    print("=" * 70)
    
    sys.exit(0 if all_passed else 1)
