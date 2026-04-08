"""
Search strategies for parameter optimization
"""

from abc import ABC, abstractmethod
from itertools import product
from typing import List, Dict, Any, Optional
import math
import random
from .models import Experiment
from .searcher import SearchSpace
import logging

logger = logging.getLogger(__name__)


class SearchStrategy(ABC):
    """Base class for search strategies"""

    def __init__(self, search_space: SearchSpace, seed: Optional[int] = None):
        """
        Initialize search strategy.

        Args:
            search_space: The search space to optimize
            seed: Random seed for reproducibility
        """
        self.search_space = search_space
        self.rng = random.Random(seed)
        self.history: List[Experiment] = []

    @abstractmethod
    def suggest_next(self, history: List[Experiment]) -> Dict[str, Any]:
        """
        Suggest the next set of parameters to evaluate.

        Args:
            history: List of previous experiments

        Returns:
            Dictionary of parameters to evaluate
        """
        pass


class RandomSearch(SearchStrategy):
    """Random search strategy"""

    def suggest_next(self, history: List[Experiment]) -> Dict[str, Any]:
        """Suggest random parameters"""
        self.history = history
        return self.search_space.sample()


class GridSearch(SearchStrategy):
    """Grid search strategy (exhaustive search)"""

    def __init__(
        self,
        search_space: SearchSpace,
        seed: Optional[int] = None,
        grid_points_per_axis: int = 5,
    ):
        """Initialize grid search

        Args:
            search_space: The search space to explore
            seed: Random seed for reproducibility
            grid_points_per_axis: Number of grid points per continuous parameter
        """
        super().__init__(search_space, seed)
        self.grid_points_per_axis = grid_points_per_axis
        self.grid_points = self._generate_grid()
        self.current_index = 0

    def _generate_grid(self) -> List[Dict[str, Any]]:
        """Generate all grid points"""
        # For continuous parameters, use 5 points
        grid_points = []

        # Get all parameter names
        param_names = list(self.search_space.parameters.keys())

        # Generate values for each parameter
        param_values = {}
        for name, config in self.search_space.parameters.items():
            if config.param_type == "discrete":
                param_values[name] = config.choices
            else:  # continuous
                param_values[name] = [
                    config.min_val + (i / max(1, self.grid_points_per_axis - 1)) * (config.max_val - config.min_val)
                    for i in range(self.grid_points_per_axis)
                ]

        # Generate all combinations
        for values in product(*[param_values[name] for name in param_names]):
            params = dict(zip(param_names, values))
            grid_points.append(params)

        # Shuffle for variety
        self.rng.shuffle(grid_points)

        return grid_points

    def suggest_next(self, history: List[Experiment]) -> Dict[str, Any]:
        """Suggest next grid point"""
        if self.current_index >= len(self.grid_points):
            logger.warning("Grid search exhausted, falling back to random search")
            return self.search_space.sample()

        params = self.grid_points[self.current_index]
        self.current_index += 1
        return params


class BayesianSearch(SearchStrategy):
    """Simplified Bayesian optimization search strategy"""

    def __init__(self, search_space: SearchSpace, seed: Optional[int] = None):
        """Initialize Bayesian search"""
        super().__init__(search_space, seed)
        self.exploration_rate = 0.3  # Exploration probability

    def suggest_next(self, history: List[Experiment]) -> Dict[str, Any]:
        """Suggest parameters using exploitation/exploration balance"""
        self.history = history

        # If no history, use random
        if not history:
            return self.search_space.sample()

        # Decide between exploration and exploitation
        if self.rng.random() < self.exploration_rate:
            # Exploration: random sample
            logger.debug("Exploration: random sample")
            return self.search_space.sample()
        else:
            # Exploitation: sample around best params
            logger.debug("Exploitation: sample around best")
            return self._sample_around_best()

    def _sample_around_best(self) -> Dict[str, Any]:
        """Sample around the best parameters found so far"""
        # Find best experiment
        best = min(self.history, key=lambda e: e.score)

        # Sample around best with Gaussian noise
        params = {}
        for name, config in self.search_space.parameters.items():
            if name in best.params:
                if config.param_type == "discrete":
                    # With 70% probability, use same value, otherwise random
                    if self.rng.random() < 0.7:
                        params[name] = best.params[name]
                    else:
                        params[name] = self.rng.choice(config.choices)
                else:  # continuous
                    # Add Gaussian noise
                    std_dev = (config.max_val - config.min_val) * 0.1
                    value = best.params[name] + self.rng.gauss(0, std_dev)
                    # Clamp to valid range
                    params[name] = max(config.min_val, min(config.max_val, value))
            else:
                # Parameter not in best, use random
                if config.param_type == "discrete":
                    params[name] = self.rng.choice(config.choices)
                else:
                    params[name] = self.rng.uniform(config.min_val, config.max_val)

        return params


class SimulatedAnnealing(SearchStrategy):
    """Simulated annealing search strategy"""

    def __init__(
        self,
        search_space: SearchSpace,
        seed: Optional[int] = None,
        initial_temp: float = 1.0,
        cooling_rate: float = 0.95
    ):
        """
        Initialize simulated annealing.

        Args:
            search_space: The search space
            seed: Random seed
            initial_temp: Initial temperature
            cooling_rate: Temperature cooling rate
        """
        super().__init__(search_space, seed)
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.current_temp = initial_temp
        self.current_params: Optional[Dict[str, Any]] = None
        self.current_score: Optional[float] = None

    def suggest_next(self, history: List[Experiment]) -> Dict[str, Any]:
        """Suggest parameters using simulated annealing"""
        self.history = history

        # First suggestion: initialize from history if available
        if self.current_params is None:
            if history and len(history) > 0:
                # Initialize from best experiment in history
                best = min(history, key=lambda e: e.score)
                self.current_params = best.params
                self.current_score = best.score
            else:
                # No history, use random sample
                self.current_params = self.search_space.sample()
            # Generate and return suggestion (don't cool down yet)
            new_params = self._perturb(self.current_params)
            return new_params

        # If we have history, update current_score from latest result
        if history:
            latest = history[-1]
            new_score = latest.score

            if self.current_score is not None:
                delta = new_score - self.current_score
                if delta < 0:
                    # Improvement (minimizing): always accept
                    self.current_score = new_score
                    self.current_params = latest.params
                elif self.current_temp > 1e-10:
                    # Worse: accept with probability exp(-delta / temp)
                    acceptance_prob = math.exp(-delta / self.current_temp)
                    if self.rng.random() < acceptance_prob:
                        self.current_score = new_score
                        self.current_params = latest.params
                    # else: keep current_params and current_score
                else:
                    # Temperature too low: reject
                    pass
            else:
                # First score recorded (shouldn't happen if initialized from history)
                self.current_score = new_score
                self.current_params = latest.params

        # Generate neighbor by perturbing current
        new_params = self._perturb(self.current_params)

        # Cool down
        self.current_temp *= self.cooling_rate

        return new_params

    def _perturb(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perturb parameters to generate neighbor"""
        new_params = {}
        for name, config in self.search_space.parameters.items():
            if name in params:
                if config.param_type == "discrete":
                    # 30% chance to change value
                    if self.rng.random() < 0.3:
                        new_params[name] = self.rng.choice(config.choices)
                    else:
                        new_params[name] = params[name]
                else:  # continuous
                    # Add Gaussian noise
                    std_dev = (config.max_val - config.min_val) * 0.1
                    value = params[name] + self.rng.gauss(0, std_dev)
                    new_params[name] = max(config.min_val, min(config.max_val, value))
            else:
                # Missing parameter, use random
                if config.param_type == "discrete":
                    new_params[name] = self.rng.choice(config.choices)
                else:
                    new_params[name] = self.rng.uniform(config.min_val, config.max_val)

        return new_params


class TPESearch(SearchStrategy):
    """Tree-structured Parzen Estimator (TPE) search strategy.

    Maintains two distributions over parameter values:
    - l(x): distribution of params from good (below quantile) experiments
    - g(x): distribution of params from bad (above quantile) experiments
    Samples candidates from l(x), evaluates EI = l(x)/g(x), picks the best.
    """

    def __init__(
        self,
        search_space: SearchSpace,
        seed: Optional[int] = None,
        gamma: float = 0.25,
        n_candidates: int = 24,
    ):
        super().__init__(search_space, seed)
        self.gamma = gamma
        self.n_candidates = n_candidates

    def suggest_next(self, history: List[Experiment]) -> Dict[str, Any]:
        self.history = history

        if len(history) < 3:
            return self.search_space.sample()

        scores = [e.score for e in history]
        threshold = sorted(scores)[max(0, int(len(scores) * self.gamma) - 1)]

        good = [e for e in history if e.score <= threshold]
        bad = [e for e in history if e.score > threshold]

        if not good:
            good = [min(history, key=lambda e: e.score)]
        if not bad:
            bad = [max(history, key=lambda e: e.score)]

        best_params = None
        best_ei = -1.0

        for _ in range(self.n_candidates):
            candidate = {}
            log_ei = 0.0
            for name, config in self.search_space.parameters.items():
                if config.param_type == "discrete":
                    val, score = self._tpe_discrete(config, good, bad, name)
                    candidate[name] = val
                    log_ei += score
                else:
                    val, score = self._tpe_continuous(config, good, bad, name)
                    candidate[name] = val
                    log_ei += score

            if log_ei > best_ei:
                best_ei = log_ei
                best_params = candidate

        return best_params if best_params is not None else self.search_space.sample()

    def _tpe_discrete(
        self, config: Any, good: List[Experiment], bad: List[Experiment], name: str
    ) -> tuple:
        good_vals = [e.params.get(name) for e in good if name in e.params]
        bad_vals = [e.params.get(name) for e in bad if name in e.params]

        if not good_vals:
            return self.rng.choice(config.choices), 0.0

        choice = self.rng.choice(config.choices)

        good_counts: Dict[Any, int] = {}
        for v in good_vals:
            good_counts[v] = good_counts.get(v, 0) + 1
        bad_counts: Dict[Any, int] = {}
        for v in bad_vals:
            bad_counts[v] = bad_counts.get(v, 0) + 1

        total_good = len(good_vals) + len(config.choices)
        total_bad = len(bad_vals) + len(config.choices)

        p_good = (good_counts.get(choice, 0) + 1) / total_good
        p_bad = (bad_counts.get(choice, 0) + 1) / total_bad

        log_ei = math.log(p_good) - math.log(p_bad)
        return choice, log_ei

    def _tpe_continuous(
        self, config: Any, good: List[Experiment], bad: List[Experiment], name: str
    ) -> tuple:
        good_vals = [e.params.get(name) for e in good if name in e.params]
        bad_vals = [e.params.get(name) for e in bad if name in e.params]

        if not good_vals:
            return self.rng.uniform(config.min_val, config.max_val), 0.0

        bandwidth = (config.max_val - config.min_val) * 0.1

        if self.rng.random() < 0.7:
            base = self.rng.choice(good_vals)
        else:
            base = self.rng.uniform(config.min_val, config.max_val)

        val = base + self.rng.gauss(0, bandwidth)
        val = max(config.min_val, min(config.max_val, val))

        p_good = self._kde_density(val, good_vals, bandwidth, config.max_val - config.min_val)
        p_bad = self._kde_density(val, bad_vals, bandwidth, config.max_val - config.min_val)

        log_ei = math.log(max(p_good, 1e-12)) - math.log(max(p_bad, 1e-12))
        return val, log_ei

    @staticmethod
    def _kde_density(x: float, values: list, bw: float, range_size: float) -> float:
        n = len(values)
        if n == 0:
            return 1.0 / range_size
        density = 0.0
        for v in values:
            u = (x - v) / bw
            density += math.exp(-0.5 * u * u)
        density /= n * bw * math.sqrt(2 * math.pi)
        return density


# Strategy factory
def create_strategy(
    strategy_name: str,
    search_space: SearchSpace,
    seed: Optional[int] = None,
    **kwargs
) -> SearchStrategy:
    """
    Create a search strategy by name.

    Args:
        strategy_name: Name of the strategy ("random", "grid", "bayesian", "annealing", "tpe")
        search_space: The search space
        seed: Random seed
        **kwargs: Additional arguments for specific strategies

    Returns:
        SearchStrategy instance
    """
    strategies = {
        "random": RandomSearch,
        "grid": GridSearch,
        "bayesian": BayesianSearch,
        "annealing": SimulatedAnnealing,
        "tpe": TPESearch,
    }

    if strategy_name not in strategies:
        raise ValueError(
            f"Unknown strategy: {strategy_name}. "
            f"Available strategies: {list(strategies.keys())}"
        )

    return strategies[strategy_name](search_space, seed, **kwargs)
