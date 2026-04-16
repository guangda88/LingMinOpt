"""
Tests for v0.3.0 features: callbacks, SimulatedAnnealing fixes,
Experiment serialization, improved logger, GridSearch configurable points.
"""

import json
import os
import tempfile

import pytest

from lingminopt import (
    MinimalOptimizer,
    SearchSpace,
    Experiment,
    create_strategy,
    GridSearch,
    SimulatedAnnealing,
    setup_logger,
)


class TestSimulatedAnnealingAcceptance:
    """Test that SimulatedAnnealing uses proper acceptance criterion."""

    def test_accepts_improvements(self):
        """SA should always accept improvements."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)
        strategy = SimulatedAnnealing(space, seed=42, initial_temp=1.0)

        exp_better = Experiment(experiment_id=1, params={"x": 5.1}, score=5.0)

        strategy.history = [exp_better]
        _ = strategy.suggest_next(strategy.history)

        assert strategy.current_score == 5.0

    def test_accepts_worse_with_probability(self):
        """SA should accept worse solutions based on temperature."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)
        strategy = SimulatedAnnealing(space, seed=42, initial_temp=10.0)

        exp_good = Experiment(experiment_id=0, params={"x": 5.0}, score=5.0)
        exp_worse = Experiment(experiment_id=1, params={"x": 5.5}, score=8.0)

        strategy.history = [exp_good]
        params = strategy.suggest_next([exp_good, exp_worse])

        assert params is not None

    def test_rejects_worse_at_low_temp(self):
        """SA should reject worse solutions at very low temperature."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)
        strategy = SimulatedAnnealing(space, seed=42, initial_temp=0.0001, cooling_rate=0.5)

        # Build up history starting with best score
        history = [Experiment(experiment_id=0, params={"x": 5.0}, score=5.0)]
        for i in range(1, 10):
            exp_worse = Experiment(experiment_id=i, params={"x": 5.0 + i * 0.1}, score=5.0 + i)
            history.append(exp_worse)
            strategy.suggest_next(history)

        assert strategy.current_score == 5.0

    def test_first_call_returns_random(self):
        """First suggestion should be random sampling."""
        space = SearchSpace()
        space.add_discrete("model", ["small", "medium", "large"])
        strategy = SimulatedAnnealing(space, seed=42)
        params = strategy.suggest_next([])
        assert params is not None
        assert strategy.current_params is not None


class TestGridSearchConfigurablePoints:
    """Test that GridSearch supports configurable grid points."""

    def test_custom_grid_points_per_axis(self):
        """GridSearch should respect grid_points_per_axis parameter."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)
        space.add_continuous("y", 0, 5)

        strategy = GridSearch(space, grid_points_per_axis=3)
        assert len(strategy.grid_points) == 3 * 3 == 9

        for p in strategy.grid_points:
            assert p["x"] in [0.0, 5.0, 10.0]
            assert p["y"] in [0.0, 2.5, 5.0]

    def test_default_five_points(self):
        """GridSearch should use 5 points by default."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)
        strategy = GridSearch(space)
        assert len(strategy.grid_points) == 5

    def test_discrete_uses_all_choices(self):
        """GridSearch should use all discrete choices."""
        space = SearchSpace()
        space.add_discrete("model", ["small", "medium", "large"])
        strategy = GridSearch(space)
        assert len(strategy.grid_points) == 3


class TestExperimentSerialization:
    """Test Experiment to_json, save, load methods."""

    def test_to_json(self):
        """to_json should return valid JSON string."""
        exp = Experiment(
            experiment_id=1,
            params={"x": 5.0, "y": "medium"},
            score=0.123,
        )
        json_str = exp.to_json()
        data = json.loads(json_str)
        assert data["experiment_id"] == 1
        assert data["score"] == 0.123
        assert data["params"]["x"] == 5.0

    def test_save_and_load(self):
        """save and load should be symmetric."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "exp.json")
            original = Experiment(
                experiment_id=42,
                params={"model": "small", "lr": 0.001},
                score=1.5,
                metadata={"epoch": 100},
            )
            original.save(filepath)

            loaded = Experiment.load(filepath)
            assert loaded.experiment_id == 42
            assert loaded.score == 1.5
            assert loaded.params["model"] == "small"
            assert loaded.metadata["epoch"] == 100

    def test_from_dict_handles_missing_timestamp(self):
        """from_dict should handle missing timestamp gracefully."""
        data = {
            "experiment_id": 1,
            "params": {"x": 5.0},
            "score": 0.5,
        }
        exp = Experiment.from_dict(data)
        assert exp.experiment_id == 1
        assert exp.timestamp is not None

    def test_validation_negative_id(self):
        """__post_init__ should reject negative experiment_id."""
        with pytest.raises(ValueError):
            Experiment(experiment_id=-1, params={}, score=0.0)

    def test_validation_invalid_score(self):
        """__post_init__ should reject NaN or inf scores."""
        with pytest.raises(ValueError):
            Experiment(experiment_id=0, params={}, score=float("nan"))
        with pytest.raises(ValueError):
            Experiment(experiment_id=0, params={}, score=float("inf"))


class TestOptimizerCallbacks:
    """Test callback mechanism in MinimalOptimizer."""

    def test_callback_invoked_on_each_experiment(self):
        """Callbacks should be invoked after each experiment."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)

        calls = []

        def callback(info):
            calls.append(info["experiment_id"])

        optimizer = MinimalOptimizer(
            evaluate=lambda p: p["x"] ** 2,
            search_space=space,
            config=None,
            callbacks=[callback],
        )

        result = optimizer.run()
        assert len(calls) == result.total_experiments
        assert set(calls) == set(range(result.total_experiments))

    def test_callback_receives_correct_info(self):
        """Callback should receive complete experiment info."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)

        captured = {}

        def callback(info):
            captured.update(info)

        optimizer = MinimalOptimizer(
            evaluate=lambda p: p["x"] ** 2,
            search_space=space,
            config=None,
            callbacks=[callback],
        )

        optimizer.run()

        assert "experiment_id" in captured
        assert "params" in captured
        assert "score" in captured
        assert "best_score" in captured
        assert "best_params" in captured
        assert "improved" in captured
        assert "elapsed" in captured
        assert "total_experiments" in captured

    def test_multiple_callbacks_all_executed(self):
        """All callbacks in the list should execute."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)

        call_order = []

        def cb1(info): call_order.append(1)
        def cb2(info): call_order.append(2)
        def cb3(info): call_order.append(3)

        optimizer = MinimalOptimizer(
            evaluate=lambda p: p["x"] ** 2,
            search_space=space,
            config=None,
            callbacks=[cb1, cb2, cb3],
        )

        optimizer.run()
        assert all(x in call_order for x in [1, 2, 3])


class TestCreateStrategyKwargsForwarding:
    """Test that create_strategy passes kwargs correctly."""

    def test_gridsearch_receives_kwargs(self):
        """GridSearch should receive grid_points_per_axis kwarg."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)

        strategy = create_strategy("grid", space, grid_points_per_axis=7)
        assert isinstance(strategy, GridSearch)
        assert len(strategy.grid_points) == 7

    def test_annealing_receives_kwargs(self):
        """SimulatedAnnealing should receive temp kwargs."""
        space = SearchSpace()
        space.add_continuous("x", 0, 10)

        strategy = create_strategy(
            "annealing", space, initial_temp=5.0, cooling_rate=0.9
        )
        assert isinstance(strategy, SimulatedAnnealing)
        assert strategy.initial_temp == 5.0
        assert strategy.cooling_rate == 0.9

    def test_invalid_strategy_raises(self):
        """create_strategy should raise ValueError for unknown strategies."""
        space = SearchSpace()
        with pytest.raises(ValueError):
            create_strategy("unknown", space)


class TestSetupLogger:
    """Test improved setup_logger functionality."""

    def test_rotating_file_handler(self):
        """Logger should use RotatingFileHandler for file output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logger("test", log_file=log_file)

            logger.info("Test message 1")
            logger.info("Test message 2")

            assert os.path.exists(log_file)
            with open(log_file) as f:
                content = f.read()
            assert "Test message 1" in content
            assert "Test message 2" in content

    def test_separate_console_and_file_levels(self):
        """Console and file should support different log levels."""
        import logging

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")

            logger = setup_logger(
                "test",
                level=logging.WARNING,
                log_file=log_file,
                file_level=logging.DEBUG,
            )

            logger.debug("Debug message")
            logger.warning("Warning message")

            with open(log_file) as f:
                file_content = f.read()
            assert "Debug message" in file_content
            assert "Warning message" in file_content


class TestPackageExports:
    """Test that v0.3.0 features are properly exported."""

    def test_create_strategy_exported(self):
        """create_strategy should be importable from lingminopt."""
        from lingminopt import create_strategy
        assert callable(create_strategy)

    def test_setup_logger_exported(self):
        """setup_logger should be importable from lingminopt."""
        from lingminopt import setup_logger
        assert callable(setup_logger)

    def test_search_strategy_base_exported(self):
        """SearchStrategy base class should be importable."""
        from lingminopt import SearchStrategy
        assert SearchStrategy is not None

    def test_version_updated(self):
        """__version__ should reflect v0.5.0."""
        from lingminopt import __version__
        assert __version__ == "0.5.0"
