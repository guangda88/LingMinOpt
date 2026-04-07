import random
from dataclasses import dataclass
from typing import List, Any, Dict, Optional

@dataclass
class ParameterConfig:
    name: str
    param_type: str
    choices: Optional[List[Any]] = None
    min_val: float = 0.0
    max_val: float = 1.0

class SearchSpace:
    def __init__(self) -> None:
        self.parameters: Dict[str, ParameterConfig] = {}
        self._rng = random.Random()

    def add_discrete(self, name: str, choices: List[Any]) -> None:
        if not choices or len(choices) == 0:
            raise ValueError(f"Discrete parameter '{name}' must have at least one choice")
        self.parameters[name] = ParameterConfig(name=name, param_type="discrete", choices=choices)

    def add_continuous(self, name: str, min_val: float, max_val: float) -> None:
        if min_val >= max_val:
            raise ValueError(f"Continuous parameter '{name}' must have min < max (got min={min_val}, max={max_val})")
        self.parameters[name] = ParameterConfig(name=name, param_type="continuous", min_val=min_val, max_val=max_val)

    def __len__(self) -> int:
        return len(self.parameters)

    def __contains__(self, name: str) -> bool:
        return name in self.parameters

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "SearchSpace":
        """Create SearchSpace from dictionary config"""
        space = cls()
        if "discrete" in config:
            for name, choices in config["discrete"].items():
                space.add_discrete(name, choices)
        if "continuous" in config:
            for name, bounds in config["continuous"].items():
                space.add_continuous(name, bounds[0], bounds[1])
        return space

    def add_from_dict(self, config: Dict[str, Any]) -> None:
        """Add parameters from dictionary config"""
        if "discrete" in config:
            for name, choices in config["discrete"].items():
                self.add_discrete(name, choices)
        if "continuous" in config:
            for name, bounds in config["continuous"].items():
                self.add_continuous(name, bounds[0], bounds[1])

    def sample(self) -> Dict[str, Any]:
        sampled: Dict[str, Any] = {}
        for name, param in self.parameters.items():
            if param.param_type == "discrete":
                sampled[name] = self._rng.choice(param.choices)
            else:
                sampled[name] = self._rng.uniform(param.min_val, param.max_val)
        return sampled
