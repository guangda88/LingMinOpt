"""
Optimization engine
"""

import time
import logging
from typing import Callable, Dict, Any
from lingminopt.core.searcher import SearchSpace
from lingminopt.core.models import Experiment, OptimizationResult
from lingminopt.config.config import ExperimentConfig
from lingminopt.core.strategy import create_strategy

logger = logging.getLogger(__name__)


class MinimalOptimizer:
    """Minimalist optimizer for parameter optimization"""

    def __init__(
        self,
        evaluate: Callable[[Dict[str, Any]], float],
        search_space: SearchSpace,
        config: ExperimentConfig = None,
        search_strategy: str = "random",
        seed: int = None
    ):
        """
        Initialize the optimizer.

        Args:
            evaluate: Function that takes params dict and returns score
            search_space: SearchSpace defining parameter space
            config: ExperimentConfig for optimization settings
            search_strategy: Strategy name ('random', 'grid', 'bayesian', 'annealing')
            seed: Random seed for reproducibility
        """
        self.evaluate = evaluate
        self.search_space = search_space
        self.config = config or ExperimentConfig()
        self.search_strategy = search_strategy
        self.seed = seed or self.config.random_seed

        # Initialize result
        if self.config.direction == "minimize":
            initial_best = float('inf')
        else:
            initial_best = float('-inf')

        self.result = OptimizationResult(
            best_score=initial_best,
            best_params={},
            history=[],
            total_experiments=0,
            total_time=0.0,
            improvement=0.0
        )

    def run(self) -> OptimizationResult:
        """
        Run optimization.

        Returns:
            OptimizationResult with best parameters and history
        """
        import random

        # Set random seed
        if self.seed is not None:
            random.seed(self.seed)

        # Create search strategy
        strategy = create_strategy(
            self.search_strategy,
            self.search_space,
            seed=self.seed
        )

        start_time = time.time()
        patience_counter = 0
        last_best = self.result.best_score
        consecutive_failures = 0
        max_consecutive_failures = max(3, self.config.max_experiments // 5)

        logger.info(f"Starting optimization with {self.config.max_experiments} experiments")

        for i in range(self.config.max_experiments):
            # Check time budget
            elapsed = time.time() - start_time
            if elapsed > self.config.time_budget:
                logger.info(f"Time budget exceeded: {elapsed:.2f}s > {self.config.time_budget}s")
                break

            # Get next parameters from strategy
            params = strategy.suggest_next(self.result.history)

            # Evaluate
            try:
                score = self.evaluate(params)
                consecutive_failures = 0
            except Exception as e:
                consecutive_failures += 1
                logger.error(f"Experiment {i} failed ({consecutive_failures} consecutive): {e}")
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(
                        f"Aborting: {consecutive_failures} consecutive evaluation failures"
                    )
                    break
                continue

            # Update best
            improved = self.config.is_better(score, self.result.best_score)

            if improved:
                logger.info(f"Improvement: {self.result.best_score:.6f} -> {score:.6f}")
                self.result.best_score = score
                self.result.best_params = params
                self.result.improvement = abs(score - last_best)
                last_best = score
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping after {patience_counter} experiments without improvement")
                    break

            # Record history
            from datetime import datetime
            exp = Experiment(
                experiment_id=i,
                params=params,
                score=score,
                timestamp=datetime.now()
            )
            self.result.history.append(exp)
            self.result.total_experiments += 1

            # Log progress
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{self.config.max_experiments} experiments")

        self.result.total_time = time.time() - start_time

        logger.info(
            f"Optimization complete: {self.result.total_experiments} experiments in "
            f"{self.result.total_time:.2f}s, best score: {self.result.best_score:.6f}"
        )

        return self.result

    def get_status(self) -> Dict[str, Any]:
        """
        Get current optimization status.

        Returns:
            Dictionary with status information
        """
        return {
            "experiments_completed": self.result.total_experiments,
            "best_score": self.result.best_score,
            "best_params": self.result.best_params,
            "total_time": self.result.total_time,
            "improvement": self.result.improvement
        }
