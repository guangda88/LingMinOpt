"""
Configuration classes for the optimizer
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExperimentConfig:
    """Configuration for optimization experiments"""

    max_experiments: int = 100
    improvement_threshold: float = 0.001
    time_budget: float = 300.0  # seconds per experiment
    early_stopping_patience: int = 10
    direction: str = "minimize"  # or "maximize"
    random_seed: Optional[int] = None
    parallel_jobs: int = 1

    def __post_init__(self) -> None:
        """Validate configuration"""
        if self.direction not in ["minimize", "maximize"]:
            raise ValueError(f"direction must be 'minimize' or 'maximize', got {self.direction}")

        if self.max_experiments <= 0:
            raise ValueError(f"max_experiments must be positive, got {self.max_experiments}")

        if self.time_budget <= 0:
            raise ValueError(f"time_budget must be positive, got {self.time_budget}")

    def is_better(self, new_score: float, old_score: float) -> bool:
        """Check if new score is better than old score"""
        if self.direction == "minimize":
            return (old_score - new_score) >= self.improvement_threshold
        else:
            return (new_score - old_score) >= self.improvement_threshold
