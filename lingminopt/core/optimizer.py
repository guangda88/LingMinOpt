"""
Core optimization engine
"""

import time
import logging
from typing import Callable, Dict, Any, Optional, List, Union
from datetime import datetime

from .models import Experiment, OptimizationResult
from .searcher import SearchSpace
from .evaluator import EvaluatorBase, FunctionEvaluator, TimedEvaluator
from .strategy import SearchStrategy, create_strategy
from ..config.config import ExperimentConfig

logger = logging.getLogger(__name__)


class MinimalOptimizer:
    """
    Minimalist optimization engine for automated parameter tuning.

    This optimizer provides a simple interface for optimizing parameters
    in any system with a quantifiable evaluation function.

    Philosophy:
        - Simplicity: Easy to use (5 lines of code)
        - Universality: Works across domains
        - Automation: Automated iteration
        - Data-Driven: Decisions based on results

    Example:
        >>> from lingminopt import MinimalOptimizer
        >>>
        >>> def evaluate(params):
        ...     return params["x"] ** 2 + params["y"] ** 2
        >>>
        >>> search_space = SearchSpace()
        >>> search_space.add_continuous("x", -10, 10)
        >>> search_space.add_continuous("y", -10, 10)
        >>>
        >>> optimizer = MinimalOptimizer(evaluate, search_space)
        >>> result = optimizer.run()
        >>> print(result.best_score)  # Should be close to 0
    """

    def __init__(
        self,
        evaluate: Union[Callable[[Dict[str, Any]], float], EvaluatorBase],
        search_space: Optional[SearchSpace] = None,
        config: Optional[ExperimentConfig] = None,
        search_strategy: str = "random",
        seed: Optional[int] = None,
    ):
        """
        Initialize the optimizer.

        Args:
            evaluate: Either a function or EvaluatorBase instance
            search_space: Search space for parameters (creates default if None)
            config: Experiment configuration (creates default if None)
            search_strategy: Strategy name ("random", "grid", "bayesian", "annealing")
            seed: Random seed for reproducibility
        """
        # Setup evaluator
        if isinstance(evaluate, EvaluatorBase):
            self.evaluator = evaluate
        else:
            self.evaluator = FunctionEvaluator(evaluate)

        # Wrap with timing
        time_budget = config.time_budget if config else 300.0
        self.timed_evaluator = TimedEvaluator(self.evaluator, time_budget)

        # Setup search space
        self.search_space = search_space or SearchSpace()

        # Setup config
        self.config = config or ExperimentConfig()
        if self.config.random_seed is None:
            self.config.random_seed = seed

        # Setup search strategy
        self.strategy = create_strategy(search_strategy, self.search_space, seed)

        # State
        self.history: List[Experiment] = []
        self.best_score = float("inf") if self.config.direction == "minimize" else float("-inf")
        self.best_params: Dict[str, Any] = {}
        self.no_improve_count = 0
        self.start_time: Optional[float] = None

    def run(self, max_experiments: Optional[int] = None) -> OptimizationResult:
        """
        Run the optimization.

        Args:
            max_experiments: Override config.max_experiments if provided

        Returns:
            OptimizationResult with best parameters and history
        """
        # Use override or config value
        max_exp = max_experiments or self.config.max_experiments

        logger.info(f"Starting optimization with {max_exp} experiments")
        logger.info(f"Search strategy: {type(self.strategy).__name__}")
        logger.info(f"Direction: {self.config.direction}")

        # Initialize timing
        self.start_time = time.time()

        # Step 1: Run baseline
        logger.info("Running baseline experiment...")
        baseline_score = self._run_experiment(self.search_space.sample(seed=0))
        logger.info(f"Baseline score: {baseline_score:.6f}")

        self.best_score = baseline_score

        # Step 2: Iterative optimization
        for i in range(1, max_exp):
            # 2.1: Generate new parameters
            params = self.strategy.suggest_next(self.history)

            # 2.2: Run experiment
            try:
                score = self._run_experiment(params)
            except TimeoutError as e:
                logger.warning(f"Experiment {i} timed out: {e}")
                continue
            except Exception as e:
                logger.error(f"Experiment {i} failed: {e}")
                continue

            # 2.3: Evaluate improvement
            improved = self.config.is_better(score, self.best_score)

            if improved:
                improvement = abs(self.best_score - score)
                logger.info(
                    f"Experiment {i}: Improved! "
                    f"Score: {score:.6f} (was {self.best_score:.6f}, +{improvement:.6f})"
                )
                self.best_score = score
                self.best_params = params.copy()
                self.no_improve_count = 0
            else:
                self.no_improve_count += 1
                logger.debug(
                    f"Experiment {i}: No improvement. "
                    f"Score: {score:.6f} (best: {self.best_score:.6f})"
                )

            # 2.4: Check early stopping
            if self.no_improve_count >= self.config.early_stopping_patience:
                logger.info(
                    f"No improvement for {self.no_improve_count} experiments, stopping early"
                )
                break

            # 2.5: Progress report
            if (i + 1) % 10 == 0:
                total_time = time.time() - self.start_time
                avg_time = total_time / (i + 1)
                logger.info(
                    f"Progress: {i + 1}/{max_exp} experiments, "
                    f"Best: {self.best_score:.6f}, "
                    f"Avg time: {avg_time:.2f}s"
                )

        # Step 3: Finalize results
        total_time = time.time() - self.start_time

        # Calculate total improvement
        if self.history:
            first_score = self.history[0].score
            if self.config.direction == "minimize":
                improvement = first_score - self.best_score
            else:
                improvement = self.best_score - first_score
        else:
            improvement = 0.0

        result = OptimizationResult(
            best_score=self.best_score,
            best_params=self.best_params.copy(),
            history=self.history.copy(),
            total_experiments=len(self.history),
            total_time=total_time,
            improvement=improvement,
        )

        logger.info(f"Optimization complete!")
        logger.info(f"Best score: {self.best_score:.6f}")
        logger.info(f"Total experiments: {len(self.history)}")
        logger.info(f"Total time: {total_time:.2f}s")
        logger.info(f"Improvement: {improvement:.6f}")

        return result

    def _run_experiment(self, params: Dict[str, Any]) -> float:
        """
        Run a single experiment.

        Args:
            params: Parameters to evaluate

        Returns:
            Evaluation score
        """
        experiment_id = len(self.history)

        logger.debug(f"Running experiment {experiment_id} with params: {params}")

        # Evaluate
        score = self.timed_evaluator.evaluate(params)

        # Record experiment
        experiment = Experiment(
            experiment_id=experiment_id,
            params=params,
            score=score,
            timestamp=datetime.now()
        )
        self.history.append(experiment)

        return score

    def get_status(self) -> Dict[str, Any]:
        """
        Get current optimization status.

        Returns:
            Dictionary with status information
        """
        total_time = time.time() - self.start_time if self.start_time else 0.0

        return {
            "experiments_completed": len(self.history),
            "best_score": self.best_score,
            "best_params": self.best_params,
            "total_time": total_time,
            "no_improve_count": self.no_improve_count,
        }
