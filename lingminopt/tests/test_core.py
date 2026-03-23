"""
Unit tests for MinOpt core components
"""

import pytest
import numpy as np
from lingminopt import (
    MinimalOptimizer,
    SearchSpace,
    EvaluatorBase,
    FunctionEvaluator,
    ExperimentConfig,
    Experiment,
    OptimizationResult,
)
from lingminopt.core.evaluator import TimedEvaluator
from lingminopt.core.strategy import RandomSearch, GridSearch, BayesianSearch


class TestSearchSpace:
    """Test SearchSpace class"""

    def test_empty_search_space(self):
        """Test creating empty search space"""
        space = SearchSpace()
        assert len(space) == 0

    def test_add_discrete(self):
        """Test adding discrete parameters"""
        space = SearchSpace()
        space.add_discrete("model", ["small", "medium", "large"])

        assert "model" in space
        assert len(space) == 1

    def test_add_continuous(self):
        """Test adding continuous parameters"""
        space = SearchSpace()
        space.add_continuous("lr", 1e-5, 1e-2)

        assert "lr" in space
        assert len(space) == 1

    def test_sample_discrete(self):
        """Test sampling discrete parameters"""
        space = SearchSpace()
        space.add_discrete("model", ["small", "medium", "large"])

        params = space.sample()
        assert "model" in params
        assert params["model"] in ["small", "medium", "large"]

    def test_sample_continuous(self):
        """Test sampling continuous parameters"""
        space = SearchSpace()
        space.add_continuous("lr", 0.0, 1.0)

        params = space.sample()
        assert "lr" in params
        assert 0.0 <= params["lr"] <= 1.0

    def test_sample_multiple(self):
        """Test sampling multiple parameters"""
        space = SearchSpace()
        space.add_discrete("model", ["small", "medium"])
        space.add_continuous("lr", 0.0, 1.0)

        params = space.sample()
        assert len(params) == 2
        assert "model" in params
        assert "lr" in params

    def test_from_dict(self):
        """Test creating search space from dictionary"""
        config = {
            "discrete": {"model": ["small", "medium"]},
            "continuous": {"lr": [0.0, 1.0]}
        }
        space = SearchSpace.from_dict(config)

        assert len(space) == 2
        assert "model" in space
        assert "lr" in space

    def test_invalid_discrete(self):
        """Test that discrete parameter without choices raises error"""
        space = SearchSpace()
        with pytest.raises(ValueError):
            space.add_discrete("param", [])

    def test_invalid_continuous(self):
        """Test that continuous parameter with min >= max raises error"""
        space = SearchSpace()
        with pytest.raises(ValueError):
            space.add_continuous("param", 1.0, 0.5)


class TestExperimentConfig:
    """Test ExperimentConfig class"""

    def test_default_config(self):
        """Test default configuration"""
        config = ExperimentConfig()
        assert config.max_experiments == 100
        assert config.improvement_threshold == 0.001
        assert config.time_budget == 300.0
        assert config.direction == "minimize"

    def test_custom_config(self):
        """Test custom configuration"""
        config = ExperimentConfig(
            max_experiments=50,
            improvement_threshold=0.01,
            time_budget=600.0,
            direction="maximize"
        )
        assert config.max_experiments == 50
        assert config.improvement_threshold == 0.01
        assert config.time_budget == 600.0
        assert config.direction == "maximize"

    def test_invalid_direction(self):
        """Test that invalid direction raises error"""
        with pytest.raises(ValueError):
            ExperimentConfig(direction="invalid")

    def test_invalid_max_experiments(self):
        """Test that invalid max_experiments raises error"""
        with pytest.raises(ValueError):
            ExperimentConfig(max_experiments=-1)

    def test_is_better_minimize(self):
        """Test is_better with minimize direction"""
        config = ExperimentConfig(direction="minimize")
        assert config.is_better(0.5, 1.0) is True   # Improved
        assert config.is_better(1.0, 1.0) is False  # No improvement

    def test_is_better_maximize(self):
        """Test is_better with maximize direction"""
        config = ExperimentConfig(direction="maximize")
        assert config.is_better(1.0, 0.5) is True   # Improved
        assert config.is_better(0.5, 0.5) is False  # No improvement


class TestEvaluators:
    """Test evaluator classes"""

    def test_function_evaluator(self):
        """Test FunctionEvaluator"""
        def objective(params):
            return params["x"] ** 2

        evaluator = FunctionEvaluator(objective)
        result = evaluator.evaluate({"x": 3.0})
        assert result == 9.0

    def test_timed_evaluator(self):
        """Test TimedEvaluator"""
        def objective(params):
            return params["x"]

        evaluator = FunctionEvaluator(objective)
        timed = TimedEvaluator(evaluator, time_budget=10.0)
        result = timed.evaluate({"x": 5.0})
        assert result == 5.0


class TestSearchStrategies:
    """Test search strategies"""

    def test_random_search(self):
        """Test RandomSearch strategy"""
        space = SearchSpace()
        space.add_continuous("x", 0.0, 1.0)

        strategy = RandomSearch(space, seed=42)
        params = strategy.suggest_next([])

        assert "x" in params
        assert 0.0 <= params["x"] <= 1.0

    def test_bayesian_search_without_history(self):
        """Test BayesianSearch without history"""
        space = SearchSpace()
        space.add_continuous("x", 0.0, 1.0)

        strategy = BayesianSearch(space, seed=42)
        params = strategy.suggest_next([])

        assert "x" in params
        assert 0.0 <= params["x"] <= 1.0


class TestOptimizer:
    """Test MinimalOptimizer"""

    def test_simple_optimization(self):
        """Test simple optimization problem"""
        def objective(params):
            x = params["x"]
            return (x - 2.0) ** 2

        space = SearchSpace()
        space.add_continuous("x", 0.0, 5.0)

        config = ExperimentConfig(
            max_experiments=20,
            time_budget=1.0,
            direction="minimize"
        )

        optimizer = MinimalOptimizer(
            evaluate=objective,
            search_space=space,
            config=config,
            search_strategy="random",
            seed=42
        )

        result = optimizer.run()

        assert result.total_experiments > 0
        assert result.total_time > 0
        assert "x" in result.best_params

        # Should find a value close to 2.0
        best_x = result.best_params["x"]
        assert abs(best_x - 2.0) < 2.0  # Reasonable tolerance

    def test_maximize_direction(self):
        """Test optimization with maximize direction"""
        def objective(params):
            x = params["x"]
            return -(x - 2.0) ** 2  # Negative quadratic, max at x=2

        space = SearchSpace()
        space.add_continuous("x", 0.0, 5.0)

        config = ExperimentConfig(
            max_experiments=20,
            time_budget=1.0,
            direction="maximize"
        )

        optimizer = MinimalOptimizer(
            evaluate=objective,
            search_space=space,
            config=config,
            search_strategy="random",
            seed=42
        )

        result = optimizer.run()

        best_x = result.best_params["x"]
        assert abs(best_x - 2.0) < 2.0

    def test_early_stopping(self):
        """Test early stopping when no improvement"""
        def objective(params):
            x = params["x"]
            return x ** 2

        space = SearchSpace()
        space.add_continuous("x", 0.0, 1.0)

        config = ExperimentConfig(
            max_experiments=100,
            early_stopping_patience=5,
            time_budget=1.0,
            direction="minimize"
        )

        optimizer = MinimalOptimizer(
            evaluate=objective,
            search_space=space,
            config=config,
            search_strategy="random",
            seed=42
        )

        result = optimizer.run()

        # Should stop early due to no improvement
        assert result.total_experiments < 100

    def test_get_status(self):
        """Test get_status method"""
        def objective(params):
            return params["x"] ** 2

        space = SearchSpace()
        space.add_continuous("x", 0.0, 1.0)

        optimizer = MinimalOptimizer(
            evaluate=objective,
            search_space=space,
            search_strategy="random",
            seed=42
        )

        status = optimizer.get_status()
        assert status["experiments_completed"] == 0
        assert status["best_score"] == float("inf")


class TestModels:
    """Test data models"""

    def test_experiment_to_dict(self):
        """Test Experiment serialization"""
        exp = Experiment(
            experiment_id=0,
            params={"x": 1.0},
            score=1.0
        )

        data = exp.to_dict()
        assert data["experiment_id"] == 0
        assert data["params"] == {"x": 1.0}
        assert data["score"] == 1.0

    def test_optimization_result_to_dict(self):
        """Test OptimizationResult serialization"""
        result = OptimizationResult(
            best_score=0.5,
            best_params={"x": 2.0},
            history=[],
            total_experiments=10,
            total_time=5.0,
            improvement=0.3
        )

        data = result.to_dict()
        assert data["best_score"] == 0.5
        assert data["best_params"] == {"x": 2.0}
        assert data["total_experiments"] == 10

    def test_optimization_result_save_load(self, tmp_path):
        """Test saving and loading OptimizationResult"""
        import os

        result = OptimizationResult(
            best_score=0.5,
            best_params={"x": 2.0},
            history=[],
            total_experiments=10,
            total_time=5.0,
            improvement=0.3
        )

        # Save
        filepath = os.path.join(tmp_path, "result.json")
        result.save(filepath)

        # Load
        loaded = OptimizationResult.load(filepath)

        assert loaded.best_score == result.best_score
        assert loaded.best_params == result.best_params
        assert loaded.total_experiments == result.total_experiments


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
