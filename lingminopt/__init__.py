"""
LingMinOpt (灵极优) - 灵研极简自优化框架
"""

from lingminopt.core.optimizer import MinimalOptimizer, ExperimentConfig
from lingminopt.core.searcher import SearchSpace

__version__ = "0.1.0"
__all__ = [
    "MinimalOptimizer",
    "SearchSpace",
    "ExperimentConfig"
]
