"""
LingMinOpt (灵极优) - 灵研极简自优化框架
"""

from lingminopt.core.optimizer import MinimalOptimizer
from lingminopt.core.searcher import SearchSpace
from lingminopt.core.models import Experiment, OptimizationResult
from lingminopt.core.evaluator import EvaluatorBase, FunctionEvaluator, TimedEvaluator
from lingminopt.core.strategy import (
    SearchStrategy,
    RandomSearch,
    GridSearch,
    BayesianSearch,
    SimulatedAnnealing,
    TPESearch,
    create_strategy,
)
from lingminopt.config.config import ExperimentConfig
from lingminopt.utils.logger import setup_logger

__version__ = "0.4.0"
__all__ = [
    "MinimalOptimizer",
    "SearchSpace",
    "Experiment",
    "OptimizationResult",
    "EvaluatorBase",
    "FunctionEvaluator",
    "TimedEvaluator",
    "SearchStrategy",
    "RandomSearch",
    "GridSearch",
    "BayesianSearch",
    "SimulatedAnnealing",
    "TPESearch",
    "create_strategy",
    "ExperimentConfig",
    "setup_logger",
    "__version__",
]
