"""
Search space definition and sampling
"""

import random
from typing import Dict, Any, List, Union
from dataclasses import dataclass, field


@dataclass
class ParameterConfig:
    """Configuration for a single parameter"""

    name: str
    param_type: str  # "discrete" or "continuous"
    choices: List[Any] = field(default_factory=list)
    min_val: float = 0.0
    max_val: float = 1.0

    def validate(self):
        """Validate parameter configuration"""
        if self.param_type not in ["discrete", "continuous"]:
            raise ValueError(f"param_type must be 'discrete' or 'continuous', got {self.param_type}")

        if self.param_type == "discrete" and not self.choices:
            raise ValueError(f"discrete parameter '{self.name}' must have choices")

        if self.param_type == "continuous":
            if self.min_val >= self.max_val:
                raise ValueError(
                    f"continuous parameter '{self.name}' min ({self.min_val}) "
                    f"must be less than max ({self.max_val})"
                )


class SearchSpace:
    """Search space for optimization parameters"""

    def __init__(self):
        """Initialize empty search space"""
        self.parameters: Dict[str, ParameterConfig] = {}
        self._rng = random.Random()

    def add_discrete(self, name: str, choices: List[Any]):
        """
        Add a discrete parameter.

        Args:
            name: Parameter name
            choices: List of possible values
        """
        param = ParameterConfig(
            name=name,
            param_type="discrete",
            choices=choices
        )
        param.validate()
        self.parameters[name] = param

    def add_continuous(self, name: str, min_val: float, max_val: float):
        """
        Add a continuous parameter.

        Args:
            name: Parameter name
            min_val: Minimum value
            max_val: Maximum value
        """
        param = ParameterConfig(
            name=name,
            param_type="continuous",
            min_val=min_val,
            max_val=max_val
        )
        param.validate()
        self.parameters[name] = param

    def add_from_dict(self, config: Dict[str, Dict[str, Any]]):
        """
        Add parameters from configuration dictionary.

        Args:
            config: Dictionary with "discrete" and "continuous" keys

        Example:
            config = {
                "discrete": {"model": ["small", "medium"]},
                "continuous": {"lr": [1e-5, 1e-2]}
            }
        """
        for param_type in ["discrete", "continuous"]:
            if param_type in config:
                for name, value in config[param_type].items():
                    if param_type == "discrete":
                        self.add_discrete(name, value)
                    else:  # continuous
                        self.add_continuous(name, value[0], value[1])

    def sample(self, seed: Union[int, None] = None) -> Dict[str, Any]:
        """
        Randomly sample a set of parameters.

        Args:
            seed: Random seed (optional)

        Returns:
            Dictionary of sampled parameters
        """
        if seed is not None:
            rng = random.Random(seed)
        else:
            rng = self._rng

        params = {}
        for name, config in self.parameters.items():
            if config.param_type == "discrete":
                params[name] = rng.choice(config.choices)
            else:  # continuous
                params[name] = rng.uniform(config.min_val, config.max_val)

        return params

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert search space to dictionary.

        Returns:
            Dictionary with "discrete" and "continuous" keys
        """
        result = {"discrete": {}, "continuous": {}}

        for name, config in self.parameters.items():
            if config.param_type == "discrete":
                result["discrete"][name] = config.choices
            else:  # continuous
                result["continuous"][name] = [config.min_val, config.max_val]

        return result

    @classmethod
    def from_dict(cls, config: Dict[str, Dict[str, Any]]) -> "SearchSpace":
        """
        Create search space from dictionary.

        Args:
            config: Dictionary with "discrete" and "continuous" keys

        Returns:
            New SearchSpace instance
        """
        space = cls()
        space.add_from_dict(config)
        return space

    def __len__(self) -> int:
        """Return number of parameters"""
        return len(self.parameters)

    def __contains__(self, name: str) -> bool:
        """Check if parameter exists"""
        return name in self.parameters

    def __repr__(self) -> str:
        """String representation"""
        discrete_count = sum(
            1 for p in self.parameters.values() if p.param_type == "discrete"
        )
        continuous_count = sum(
            1 for p in self.parameters.values() if p.param_type == "continuous"
        )
        return f"SearchSpace({discrete_count} discrete, {continuous_count} continuous)"
