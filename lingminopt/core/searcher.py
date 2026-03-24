import random
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class ParameterConfig:
    name: str
    param_type: str
    choices: List[Any] = None
    min_val: float = 0.0
    max_val: float = 1.0

class SearchSpace:
    def __init__(self):
        self.parameters = {}
        self._rng = random.Random()

    def add_discrete(self, name, choices):
        self.parameters[name] = ParameterConfig(name=name, param_type="discrete", choices=choices)

    def add_continuous(self, name, min_val, max_val):
        self.parameters[name] = ParameterConfig(name=name, param_type="continuous", min_val=min_val, max_val=max_val)

    def sample(self):
        sampled = {}
        for name, param in self.parameters.items():
            if param.param_type == "discrete":
                sampled[name] = self._rng.choice(param.choices)
            else:
                sampled[name] = self._rng.uniform(param.min_val, param.max_val)
        return sampled
