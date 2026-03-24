import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "zhineng-bridge" / "optimization"))

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
from variable import create_websocket_search_space, create_performance_search_space
from evaluator import evaluate_websocket_params, evaluate_performance_params

print("=" * 70)
print("智桥落地案例 - 使用 LingMinOpt 框架")
print("=" * 70)
print()

# WebSocket 优化
print("📋 WebSocket 连接参数优化")
search_space = create_websocket_search_space()
config = ExperimentConfig(
    max_experiments=50,
    improvement_threshold=0.01,
    time_budget=10,
    direction="maximize",
    random_seed=42
)
optimizer = MinimalOptimizer(evaluate_websocket_params, search_space, config)
result = optimizer.run()

print()
print("=" * 70)
print("WebSocket 连接优化结果")
print("=" * 70)
print(f"最佳分数: {result.best_score:.4f}")
print(f"最佳参数:")
for key, value in result.best_params.items():
    print(f"  {key}: {value}")
print(f"总实验次数: {result.total_experiments}")
print(f"总时间: {result.total_time:.2f} 秒")
print(f"总改进: {result.improvement:.4f}")
print()

# 性能优化
print("📋 性能参数优化")
search_space = create_performance_search_space()
config = ExperimentConfig(
    max_experiments=50,
    improvement_threshold=0.01,
    time_budget=10,
    direction="maximize",
    random_seed=42
)
optimizer = MinimalOptimizer(evaluate_performance_params, search_space, config)
result = optimizer.run()

print()
print("=" * 70)
print("性能参数优化结果")
print("=" * 70)
print(f"最佳分数: {result.best_score:.4f}")
print(f"最佳参数:")
for key, value in result.best_params.items():
    print(f"  {key}: {value}")
print(f"总实验次数: {result.total_experiments}")
print(f"总时间: {result.total_time:.2f} 秒")
print(f"总改进: {result.improvement:.4f}")
print()

print("=" * 70)
print("智桥优化总结")
print("=" * 70)
print("💡 使用建议:")
print("  1. 将最佳参数应用到 zhineng-bridge 配置中")
print("  2. 重新运行优化实验以获得更稳定的结果")
print("  3. 监控实际系统表现，调整评估函数")
print("  4. 定期运行优化实验，适应系统变化")
print()
