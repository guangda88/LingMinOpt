import logging
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_BRIDGE_OPT_DIR = Path(__file__).parent.parent.parent / "zhineng-bridge" / "optimization"
if not (_BRIDGE_OPT_DIR / "variable.py").exists():
    logger.warning("安全限制: 此示例需要智桥优化模块，但路径不在灵极优管辖范围内。")
    logger.warning("期望路径: %s", _BRIDGE_OPT_DIR)
    logger.warning("请在智桥项目中独立运行此优化。")
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(_BRIDGE_OPT_DIR))

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
from variable import create_websocket_search_space, create_performance_search_space
from evaluator import evaluate_websocket_params, evaluate_performance_params

logging.basicConfig(level=logging.INFO, format="%(message)s")

logger.info("=" * 70)
logger.info("智桥落地案例 - 使用 lingminopt 框架")
logger.info("=" * 70)
logger.info("")

# WebSocket 优化
logger.info("📋 WebSocket 连接参数优化")
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

logger.info("")
logger.info("=" * 70)
logger.info("WebSocket 连接优化结果")
logger.info("=" * 70)
logger.info("最佳分数: %.4f", result.best_score)
logger.info("最佳参数:")
for key, value in result.best_params.items():
    logger.info("  %s: %s", key, value)
logger.info("总实验次数: %s", result.total_experiments)
logger.info("总时间: %.2f 秒", result.total_time)
logger.info("总改进: %.4f", result.improvement)
logger.info("")

# 性能优化
logger.info("📋 性能参数优化")
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

logger.info("")
logger.info("=" * 70)
logger.info("性能参数优化结果")
logger.info("=" * 70)
logger.info("最佳分数: %.4f", result.best_score)
logger.info("最佳参数:")
for key, value in result.best_params.items():
    logger.info("  %s: %s", key, value)
logger.info("总实验次数: %s", result.total_experiments)
logger.info("总时间: %.2f 秒", result.total_time)
logger.info("总改进: %.4f", result.improvement)
logger.info("")

logger.info("=" * 70)
logger.info("智桥优化总结")
logger.info("=" * 70)
logger.info("💡 使用建议:")
logger.info("  1. 将最佳参数应用到 zhineng-bridge 配置中")
logger.info("  2. 重新运行优化实验以获得更稳定的结果")
logger.info("  3. 监控实际系统表现，调整评估函数")
logger.info("  4. 定期运行优化实验，适应系统变化")
logger.info("")
