"""
示例：算法优化

使用 LingMinOpt 优化算法的参数和实现细节。

目标：最小化算法的执行时间
"""

import sys
sys.path.insert(0, '/home/ai/LingMinOpt')

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
import time
import random


# ============================================================================
# 算法实现（可修改）
# ============================================================================
def bubble_sort(arr, params):
    """
    冒泡排序（带优化）

    Args:
        arr: 待排序数组
        params: 排序参数

    Returns:
        排序后的数组
    """
    n = len(arr)

    # 参数控制优化
    early_termination = params.get("early_termination", True)
    adaptive_swap = params.get("adaptive_swap", False)

    for i in range(n):
        swapped = False

        for j in range(0, n - i - 1):
            # 比较逻辑
            should_swap = arr[j] > arr[j + 1]

            # 自适应交换（根据相邻元素差异）
            if adaptive_swap and j > 0:
                diff1 = abs(arr[j] - arr[j-1])
                diff2 = abs(arr[j+1] - arr[j])
                # 如果差异大，优先交换
                if diff1 > diff2 * 2:
                    should_swap = True

            if should_swap:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True

        # 提前终止优化
        if early_termination and not swapped:
            break

    return arr


def quick_sort(arr, params, low=0, high=None):
    """
    快速排序（带优化）

    Args:
        arr: 待排序数组
        params: 排序参数
        low: 起始索引
        high: 结束索引

    Returns:
        排序后的数组
    """
    if high is None:
        high = len(arr) - 1

    if low < high:
        # 参数控制分区策略
        pivot_strategy = params.get("pivot_strategy", "last")
        threshold = params.get("threshold", 10)

        # 小数组使用插入排序
        if high - low + 1 <= threshold:
            arr = insertion_sort_partial(arr, low, high)
            return arr

        # 选择基准
        if pivot_strategy == "last":
            pivot = arr[high]
            i = low - 1

            for j in range(low, high):
                if arr[j] <= pivot:
                    i += 1
                    arr[i], arr[j] = arr[j], arr[i]

            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            pi = i + 1

        elif pivot_strategy == "random":
            # 随机基准
            rand_idx = random.randint(low, high)
            arr[rand_idx], arr[high] = arr[high], arr[rand_idx]

            pivot = arr[high]
            i = low - 1

            for j in range(low, high):
                if arr[j] <= pivot:
                    i += 1
                    arr[i], arr[j] = arr[j], arr[i]

            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            pi = i + 1

        elif pivot_strategy == "median_of_three":
            # 三数取中
            mid = (low + high) // 2
            candidates = [(arr[low], low), (arr[mid], mid), (arr[high], high)]
            candidates.sort(key=lambda x: x[0])
            median_idx = candidates[1][1]

            arr[median_idx], arr[high] = arr[high], arr[median_idx]

            pivot = arr[high]
            i = low - 1

            for j in range(low, high):
                if arr[j] <= pivot:
                    i += 1
                    arr[i], arr[j] = arr[j], arr[i]

            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            pi = i + 1

        # 递归排序
        arr = quick_sort(arr, params, low, pi - 1)
        arr = quick_sort(arr, params, pi + 1, high)

    return arr


def insertion_sort_partial(arr, low, high):
    """
    插入排序（部分数组）

    Args:
        arr: 数组
        low: 起始索引
        high: 结束索引

    Returns:
        排序后的数组
    """
    for i in range(low + 1, high + 1):
        key = arr[i]
        j = i - 1

        while j >= low and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1

        arr[j + 1] = key

    return arr


def hybrid_sort(arr, params):
    """
    混合排序（结合多种策略）

    Args:
        arr: 待排序数组
        params: 排序参数

    Returns:
        排序后的数组
    """
    algorithm = params["algorithm"]
    threshold = params["hybrid_threshold"]

    if len(arr) <= threshold:
        # 小数组用插入排序
        return insertion_sort_partial(arr, 0, len(arr) - 1)
    else:
        # 大数组用快速排序
        if algorithm == "quick":
            return quick_sort(arr, params)
        elif algorithm == "bubble":
            return bubble_sort(arr, params)
        else:
            # 默认
            return quick_sort(arr, params)


# ============================================================================
# 评估函数（不可修改）
# ============================================================================
def evaluate_sort(sort_func, arr, params):
    """
    评估排序函数的性能

    Args:
        sort_func: 排序函数
        arr: 待排序数组
        params: 参数

    Returns:
        tuple: (执行时间, 是否正确)
    """
    # 复制数组以避免修改原数组
    arr_copy = arr.copy()
    arr_sorted = sorted(arr)

    # 测量时间
    start_time = time.time()
    result = sort_func(arr_copy, params)
    elapsed_time = time.time() - start_time

    # 检查正确性
    is_correct = result == arr_sorted

    return elapsed_time, is_correct


# ============================================================================
# 优化实验
# ============================================================================
# 定义搜索空间
search_space = SearchSpace()

# 算法选择
search_space.add_discrete("algorithm", ["quick", "bubble", "hybrid"])

# 快速排序参数
search_space.add_discrete("pivot_strategy", ["last", "random", "median_of_three"])
search_space.add_continuous("threshold", 5, 50)

# 冒泡排序参数
search_space.add_discrete("early_termination", [True, False])
search_space.add_discrete("adaptive_swap", [True, False])

# 混合排序参数
search_space.add_continuous("hybrid_threshold", 10, 100)


def run_experiment(params):
    """
    运行实验：评估排序算法

    Args:
        params: 算法参数

    Returns:
        float: 平均执行时间（越低越好）
    """
    algorithm = params["algorithm"]

    # 生成测试数据
    # 使用不同大小的数组测试
    test_sizes = [100, 500, 1000, 2000]
    total_time = 0.0
    total_correct = 0
    total_tests = 0

    for size in test_sizes:
        # 生成随机数组
        random.seed(42)  # 固定种子以获得可重复的结果
        arr = [random.randint(0, 10000) for _ in range(size)]

        # 根据算法选择排序函数
        if algorithm == "quick":
            sort_func = quick_sort
        elif algorithm == "bubble":
            sort_func = bubble_sort
        else:  # hybrid
            sort_func = hybrid_sort

        # 多次测试取平均
        num_runs = 5
        for _ in range(num_runs):
            elapsed_time, is_correct = evaluate_sort(sort_func, arr, params)
            total_time += elapsed_time
            total_correct += 1 if is_correct else 0
            total_tests += 1

    # 计算平均时间
    avg_time = total_time / total_tests

    # 惩罚不正确的结果
    accuracy = total_correct / total_tests if total_tests > 0 else 0
    if accuracy < 1.0:
        avg_time *= (2.0 - accuracy)  # 惩罚系数

    return avg_time


# ============================================================================
# 主程序
# ============================================================================
def main():
    """主函数"""
    print()
    print("=" * 70)
    print("算法优化示例")
    print("=" * 70)
    print()

    # 配置优化器
    config = ExperimentConfig(
        max_experiments=50,
        improvement_threshold=0.001,
        time_budget=30.0,  # 每个实验最多 30 秒
        direction="minimize",  # 最小化时间
        random_seed=42
    )

    # 创建优化器
    optimizer = MinimalOptimizer(
        evaluate=run_experiment,
        search_space=search_space,
        config=config,
        search_strategy="random",
        seed=42
    )

    # 运行优化
    print("开始优化...")
    print(f"搜索空间: {len(search_space)} 个参数")
    print(f"最大实验次数: {config.max_experiments}")
    print()

    result = optimizer.run()

    # 打印结果
    print()
    print("=" * 70)
    print("优化结果")
    print("=" * 70)
    print()
    print(f"最佳平均执行时间: {result.best_score:.6f} 秒")
    print(f"最佳算法参数:")
    for key, value in result.best_params.items():
        print(f"  {key}: {value}")
    print()
    print(f"总实验次数: {result.total_experiments}")
    print(f"总时间: {result.total_time:.2f} 秒")
    print(f"改进: {result.improvement:.6f} 秒")
    print()

    # 使用最佳参数进行对比测试
    print("=" * 70)
    print("对比测试")
    print("=" * 70)
    print()

    # 生成更大的测试数据
    test_size = 5000
    random.seed(42)
    test_arr = [random.randint(0, 10000) for _ in range(test_size)]

    # 使用最佳参数
    algorithm = result.best_params["algorithm"]
    if algorithm == "quick":
        sort_func = quick_sort
    elif algorithm == "bubble":
        sort_func = bubble_sort
    else:
        sort_func = hybrid_sort

    arr_copy = test_arr.copy()
    start_time = time.time()
    result_arr = sort_func(arr_copy, result.best_params)
    best_time = time.time() - start_time

    # 对比 Python 内置排序
    arr_copy2 = test_arr.copy()
    start_time = time.time()
    sorted_arr = sorted(arr_copy2)
    builtin_time = time.time() - start_time

    print(f"测试数组大小: {test_size}")
    print()
    print(f"优化后的算法:")
    print(f"  执行时间: {best_time:.6f} 秒")
    print(f"  正确性: {'✓ 正确' if result_arr == sorted_arr else '✗ 错误'}")
    print()
    print(f"Python 内置排序:")
    print(f"  执行时间: {builtin_time:.6f} 秒")
    print()
    print(f"性能比: {best_time / builtin_time:.2f}x")
    if best_time / builtin_time < 5:
        print("  ✓ 性能尚可")
    else:
        print("  ✗ 仍需优化")
    print()

    # 保存结果
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"algorithm_optimization_results_{timestamp}.json"

    with open(result_file, 'w') as f:
        json.dump({
            "best_params": result.best_params,
            "best_time": result.best_score,
            "improvement": result.improvement,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time,
            "benchmark": {
                "test_size": test_size,
                "optimized_time": best_time,
                "builtin_time": builtin_time,
                "ratio": best_time / builtin_time
            }
        }, f, indent=2)

    print(f"结果已保存到: {result_file}")


if __name__ == "__main__":
    main()
