"""
Data models for the optimizer
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
import json
import math


@dataclass
class Experiment:
    """Single experiment result"""

    experiment_id: int
    params: Dict[str, Any]
    score: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.experiment_id < 0:
            raise ValueError("experiment_id must be non-negative")
        if math.isnan(self.score) or math.isinf(self.score):
            raise ValueError("score must be a finite number")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "experiment_id": self.experiment_id,
            "params": self.params,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Experiment":
        """Create from dictionary"""
        ts = data.get("timestamp")
        return cls(
            experiment_id=data["experiment_id"],
            params=data["params"],
            score=data["score"],
            timestamp=datetime.fromisoformat(ts) if ts else datetime.now(),
            metadata=data.get("metadata", {})
        )

    def save(self, filepath: str):
        """Save to JSON file"""
        with open(filepath, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> "Experiment":
        """Load from JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class OptimizationResult:
    """Complete optimization result"""

    best_score: float
    best_params: Dict[str, Any]
    history: List[Experiment] = field(default_factory=list)
    total_experiments: int = 0
    total_time: float = 0.0
    improvement: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "best_score": self.best_score,
            "best_params": self.best_params,
            "history": [exp.to_dict() for exp in self.history],
            "total_experiments": self.total_experiments,
            "total_time": self.total_time,
            "improvement": self.improvement
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptimizationResult":
        """Create from dictionary"""
        return cls(
            best_score=data["best_score"],
            best_params=data["best_params"],
            history=[Experiment.from_dict(exp) for exp in data.get("history", [])],
            total_experiments=data.get("total_experiments", 0),
            total_time=data.get("total_time", 0.0),
            improvement=data.get("improvement", 0.0)
        )

    def save(self, filepath: str):
        """Save to JSON file"""
        with open(filepath, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, filepath: str) -> "OptimizationResult":
        """Load from JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)
