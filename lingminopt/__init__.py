"""
Minimal Optimizer - A universal minimalist self-optimization framework

Inspired by 灵研 (LingResearch) and autoresearch frameworks.
Core philosophy: Simplicity, Automation, Data-Driven Optimization.
"""

__version__ = "0.1.0"

from lingminopt.core.optimizer import MinimalOptimizer
from lingminopt.core.searcher import SearchSpace
from lingminopt.core.evaluator import EvaluatorBase, FunctionEvaluator
from lingminopt.config.config import ExperimentConfig
from lingminopt.core.models import Experiment, OptimizationResult

__all__ = [
    "MinimalOptimizer",
    "SearchSpace",
    "EvaluatorBase",
    "FunctionEvaluator",
    "ExperimentConfig",
    "Experiment",
    "OptimizationResult",
]
