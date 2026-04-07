"""
Evaluator base class and implementations
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class EvaluatorBase(ABC):
    """Base class for evaluators"""

    @abstractmethod
    def evaluate(self, params: Dict[str, Any]) -> float:
        """
        Evaluate parameters and return a score.

        Args:
            params: Dictionary of parameters to evaluate

        Returns:
            Evaluation score (float)
        """
        pass

    def setup(self, params: Dict[str, Any]) -> None:
        """
        Setup before evaluation (optional).

        Args:
            params: Parameters that will be evaluated
        """
        pass

    def cleanup(self, params: Dict[str, Any]) -> None:
        """
        Cleanup after evaluation (optional).

        Args:
            params: Parameters that were evaluated
        """
        pass


class FunctionEvaluator(EvaluatorBase):
    """Wrapper for a simple evaluation function"""

    def __init__(self, func: Callable[[Dict[str, Any]], float]):
        """
        Initialize with an evaluation function.

        Args:
            func: Function that takes params dict and returns a score
        """
        self.func = func

    def evaluate(self, params: Dict[str, Any]) -> float:
        """
        Call the wrapped function.

        Args:
            params: Parameters to evaluate

        Returns:
            Evaluation score
        """
        return self.func(params)


class TimedEvaluator(EvaluatorBase):
    """Wrapper that adds timing to any evaluator"""

    def __init__(self, evaluator: EvaluatorBase, time_budget: float = 300.0):
        """
        Initialize with an evaluator and time budget.

        Args:
            evaluator: The evaluator to wrap
            time_budget: Maximum time per experiment in seconds
        """
        self.evaluator = evaluator
        self.time_budget = time_budget

    def evaluate(self, params: Dict[str, Any]) -> float:
        """
        Evaluate with timing and timeout.

        Args:
            params: Parameters to evaluate

        Returns:
            Evaluation score

        Raises:
            TimeoutError: If evaluation exceeds time budget
        """
        start_time = time.time()

        try:
            self.evaluator.setup(params)
            score = self.evaluator.evaluate(params)
            elapsed = time.time() - start_time

            if elapsed > self.time_budget:
                logger.warning(
                    f"Experiment exceeded time budget: {elapsed:.2f}s > {self.time_budget}s"
                )

            return score
        finally:
            self.evaluator.cleanup(params)

            elapsed = time.time() - start_time
            if elapsed > self.time_budget * 1.5:  # Allow 50% grace
                raise TimeoutError(
                    f"Evaluation took {elapsed:.2f}s, exceeding budget of {self.time_budget}s"
                )
