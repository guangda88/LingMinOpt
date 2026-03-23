"""
示例：硬件/编译器优化

使用 LingMinOpt 优化编译器标志和配置参数。

目标：最小化程序执行时间
"""

import sys
sys.path.insert(0, '/home/ai/LingMinOpt')

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
import time
import subprocess
import tempfile
import os


# ============================================================================
# 编译和测试环境（不可修改）
# ============================================================================
def compile_program(source_code, flags):
    """
    编译程序

    Args:
        source_code: C 源代码
        flags: 编译标志

    Returns:
        str: 编译后的可执行文件路径
    """
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
        f.write(source_code)
        source_file = f.name

    try:
        # 编译
        exe_file = source_file.replace('.c', '')

        # 构建编译命令
        cmd = ['gcc'] + flags + ['-o', exe_file, source_file]

        # 执行编译
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise RuntimeError(f"编译失败: {result.stderr}")

        return exe_file

    finally:
        # 清理源文件
        if os.path.exists(source_file):
            os.remove(source_file)


def benchmark_program(exe_file, num_runs=10):
    """
    运行程序基准测试

    Args:
        exe_file: 可执行文件路径
        num_runs: 运行次数

    Returns:
        float: 平均执行时间（秒）
    """
    times = []

    for _ in range(num_runs):
        start_time = time.time()

        # 运行程序
        result = subprocess.run(
            [exe_file],
            capture_output=True,
            timeout=30
        )

        elapsed = time.time() - start_time
        times.append(elapsed)

    # 计算平均时间（去掉最大和最小值）
    times_sorted = sorted(times)
    avg_time = sum(times_sorted[1:-1]) / (len(times_sorted) - 2)

    return avg_time


# ============================================================================
# 测试程序（不可修改）
# ============================================================================
# 一个简单的计算密集型程序
TEST_PROGRAM = """
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define SIZE 1000

int main() {
    double matrix[SIZE][SIZE];
    double vector[SIZE];
    double result[SIZE];
    int i, j, k;

    // 初始化矩阵和向量
    for (i = 0; i < SIZE; i++) {
        vector[i] = (double)i / SIZE;
        for (j = 0; j < SIZE; j++) {
            matrix[i][j] = (double)(i + j) / SIZE;
        }
    }

    // 矩阵向量乘法
    for (i = 0; i < SIZE; i++) {
        result[i] = 0.0;
        for (j = 0; j < SIZE; j++) {
            result[i] += matrix[i][j] * vector[j];
        }
    }

    // 一些额外的计算
    for (i = 0; i < SIZE; i++) {
        result[i] = sqrt(result[i] * result[i] + 1.0);
    }

    printf("Computation complete.\\n");
    return 0;
}
"""


# ============================================================================
# 优化实验
# ============================================================================
# 定义搜索空间
search_space = SearchSpace()

# 优化级别
search_space.add_discrete("opt_level", ["-O0", "-O1", "-O2", "-O3", "-Os"])

# 体系结构优化
search_space.add_discrete("march", [None, "-march=native", "-march=x86-64"])
search_space.add_discrete("mtune", [None, "-mtune=native", "-mtune=generic"])

# 循环优化
search_space.add_discrete("unroll_loops", [None, "-funroll-loops"])
search_space.add_discrete("loop_vectorize", [None, "-ftree-vectorize"])
search_space.add_discrete("loop_interchange", [None, "-floop-interchange"])

# 其他优化
search_space.add_discrete("fast_math", [None, "-ffast-math"])
search_space.add_discrete("omit_frame_pointer", [None, "-fomit-frame-pointer"])
search_space.add_discrete("inline_functions", [None, "-finline-functions"])
search_space.add_discrete("strip_symbols", [None, "-s"])

# 链接时优化
search_space.add_discrete("lto", [None, "-flto"])


def build_flags(params):
    """
    根据参数构建编译标志列表

    Args:
        params: 参数字典

    Returns:
        list: 编译标志列表
    """
    flags = []

    # 优化级别
    flags.append(params["opt_level"])

    # 体系结构优化
    if params["march"]:
        flags.append(params["march"])
    if params["mtune"]:
        flags.append(params["mtune"])

    # 循环优化
    if params["unroll_loops"]:
        flags.append(params["unroll_loops"])
    if params["loop_vectorize"]:
        flags.append(params["loop_vectorize"])
    if params["loop_interchange"]:
        flags.append(params["loop_interchange"])

    # 其他优化
    if params["fast_math"]:
        flags.append(params["fast_math"])
    if params["omit_frame_pointer"]:
        flags.append(params["omit_frame_pointer"])
    if params["inline_functions"]:
        flags.append(params["inline_functions"])

    # 链接时优化
    if params["lto"]:
        flags.append(params["lto"])

    # 剥离符号（链接时）
    if params["strip_symbols"]:
        flags.append(params["strip_symbols"])

    return flags


def run_experiment(params):
    """
    运行实验：评估编译器配置

    Args:
        params: 编译器参数

    Returns:
        float: 平均执行时间（越低越好）
    """
    try:
        # 构建编译标志
        flags = build_flags(params)

        # 编译程序
        exe_file = compile_program(TEST_PROGRAM, flags)

        try:
            # 运行基准测试
            avg_time = benchmark_program(exe_file, num_runs=5)

            return avg_time

        finally:
            # 清理可执行文件
            if os.path.exists(exe_file):
                os.remove(exe_file)

    except Exception as e:
        # 如果编译失败，返回一个很大的值
        print(f"  ⚠ 编译失败: {e}")
        return float('inf')


# ============================================================================
# 主程序
# ============================================================================
def main():
    """主函数"""
    print()
    print("=" * 70)
    print("硬件/编译器优化示例")
    print("=" * 70)
    print()

    # 检查 gcc 是否可用
    try:
        result = subprocess.run(['gcc', '--version'], capture_output=True, timeout=5)
        print("✓ GCC 编译器可用")
        print(f"  版本: {result.stdout.decode().split()[2]}")
        print()
    except Exception as e:
        print("✗ GCC 编译器不可用")
        print(f"  错误: {e}")
        print()
        print("请安装 GCC 以运行此示例：")
        print("  Ubuntu/Debian: sudo apt-get install gcc")
        print("  CentOS/RHEL: sudo yum install gcc")
        return

    # 配置优化器
    config = ExperimentConfig(
        max_experiments=30,
        improvement_threshold=0.01,
        time_budget=60.0,  # 每个实验最多 60 秒（编译可能需要时间）
        direction="minimize",  # 最小化执行时间
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
    print(f"最佳执行时间: {result.best_score:.4f} 秒")
    print(f"最佳编译标志:")
    for key, value in result.best_params.items():
        if value is not None and value != "":
            print(f"  {key}: {value}")
    print()
    print(f"总实验次数: {result.total_experiments}")
    print(f"总时间: {result.total_time:.2f} 秒")
    print(f"改进: {result.improvement:.4f} 秒")
    print()

    # 使用最佳标志编译并运行
    print("=" * 70)
    print("验证最佳配置")
    print("=" * 70)
    print()

    best_flags = build_flags(result.best_params)
    print(f"编译命令:")
    print(f"  gcc {' '.join(best_flags)} -o optimized_program")
    print()

    # 编译
    try:
        exe_file = compile_program(TEST_PROGRAM, best_flags)

        # 运行基准测试
        print("运行基准测试...")
        final_time = benchmark_program(exe_file, num_runs=10)

        print()
        print(f"最终执行时间: {final_time:.4f} 秒")
        print(f"平均执行时间: {final_time:.4f} 秒")
        print()

        # 清理
        os.remove(exe_file)

    except Exception as e:
        print(f"✗ 编译失败: {e}")

    # 保存结果
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"hardware_optimization_results_{timestamp}.json"

    with open(result_file, 'w') as f:
        json.dump({
            "best_params": result.best_params,
            "best_flags": best_flags,
            "best_time": result.best_score,
            "improvement": result.improvement,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time
        }, f, indent=2)

    print(f"结果已保存到: {result_file}")


if __name__ == "__main__":
    main()
