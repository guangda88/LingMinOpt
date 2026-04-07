"""
Example 1: Simple Quadratic Optimization

This example demonstrates basic MinOpt usage by optimizing a simple
quadratic function: f(x, y) = (x - 2)² + (y + 3)²

The global minimum is at x = 2, y = -3 with value 0.
"""

import logging

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig

logger = logging.getLogger("lingminopt.examples.quadratic")


def objective(params):
    """Objective function to minimize."""
    x = params["x"]
    y = params["y"]
    return (x - 2)**2 + (y + 3)**2


search_space = SearchSpace()
search_space.add_continuous("x", -10, 10)
search_space.add_continuous("y", -10, 10)

config = ExperimentConfig(
    max_experiments=50,
    improvement_threshold=0.01,
    time_budget=1.0,
    direction="minimize"
)

optimizer = MinimalOptimizer(
    evaluate=objective,
    search_space=search_space,
    config=config,
    search_strategy="random",
    seed=42
)

logger.info("Starting optimization...")
logger.info("Search strategy: random")
logger.info("Max experiments: %d", config.max_experiments)

result = optimizer.run()

logger.info("=" * 60)
logger.info("Optimization Results")
logger.info("=" * 60)
logger.info("Best Score: %.6f", result.best_score)
logger.info("Best Parameters: %s", result.best_params)
logger.info("Expected: x ≈ 2.0, y ≈ -3.0")
logger.info("Total Experiments: %d", result.total_experiments)
logger.info("Total Time: %.2fs", result.total_time)
logger.info("Improvement: %.6f", result.improvement)

result.save("example1_results.json")
logger.info("Results saved to: example1_results.json")

logger.info("=" * 60)
logger.info("Verification")
logger.info("=" * 60)
expected_x = 2.0
expected_y = -3.0
actual_x = result.best_params.get("x", 0)
actual_y = result.best_params.get("y", 0)

error_x = abs(actual_x - expected_x)
error_y = abs(actual_y - expected_y)

logger.info("x: Expected %.2f, Got %.2f, Error %.2f", expected_x, actual_x, error_x)
logger.info("y: Expected %.2f, Got %.2f, Error %.2f", expected_y, actual_y, error_y)

if error_x < 1.0 and error_y < 1.0:
    logger.info("Optimization successful! Found near-optimal solution.")
else:
    logger.warning("Could not find optimal solution. Try increasing max_experiments.")
