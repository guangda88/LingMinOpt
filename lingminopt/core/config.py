from dataclasses import dataclass

@dataclass
class ExperimentConfig:
    max_experiments: int = 50
    improvement_threshold: float = 0.01
    time_budget: float = 300
    early_stopping_patience: int = 10
    direction: str = "minimize"
    random_seed: int = 42
