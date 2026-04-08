"""
Tests for v0.4.0 features: TPESearch strategy, visualization module,
MCP feedback tools, compare_results.
"""

from pathlib import Path

import pytest

from lingminopt import (
    MinimalOptimizer,
    SearchSpace,
    Experiment,
    OptimizationResult,
    ExperimentConfig,
    TPESearch,
    create_strategy,
)


class TestTPESearchStrategy:
    """Test TPESearch strategy."""

    def test_tpe_returns_valid_params(self):
        space = SearchSpace()
        space.add_continuous("x", -5, 5)
        tpe = TPESearch(space, seed=42)
        params = tpe.suggest_next([])
        assert "x" in params
        assert -5 <= params["x"] <= 5

    def test_tpe_with_history(self):
        space = SearchSpace()
        space.add_continuous("x", -5, 5)
        tpe = TPESearch(space, seed=42)
        history = [
            Experiment(experiment_id=i, params={"x": float(i)}, score=float(i))
            for i in range(10)
        ]
        params = tpe.suggest_next(history)
        assert "x" in params
        assert -5 <= params["x"] <= 5

    def test_tpe_with_discrete_params(self):
        space = SearchSpace()
        space.add_discrete("model", ["a", "b", "c"])
        space.add_continuous("lr", 0.001, 0.1)
        tpe = TPESearch(space, seed=42)
        history = [
            Experiment(
                experiment_id=i,
                params={"model": "a" if i % 2 == 0 else "b", "lr": 0.01 * (i + 1)},
                score=float(i),
            )
            for i in range(10)
        ]
        params = tpe.suggest_next(history)
        assert params["model"] in ["a", "b", "c"]
        assert 0.001 <= params["lr"] <= 0.1

    def test_tpe_factory(self):
        space = SearchSpace()
        space.add_continuous("x", 0, 1)
        strategy = create_strategy("tpe", space, seed=123)
        assert isinstance(strategy, TPESearch)

    def test_tpe_unknown_raises(self):
        space = SearchSpace()
        space.add_continuous("x", 0, 1)
        with pytest.raises(ValueError, match="Unknown strategy"):
            create_strategy("unknown", space)

    def test_tpe_full_optimization(self):
        space = SearchSpace()
        space.add_continuous("x", -5, 5)

        def objective(params):
            return params["x"] ** 2

        config = ExperimentConfig(max_experiments=20, time_budget=10.0)
        optimizer = MinimalOptimizer(objective, space, config, search_strategy="tpe", seed=42)
        result = optimizer.run()
        assert result.best_score < 1.0
        assert abs(result.best_params["x"]) < 2.0


class TestVisualizationModule:
    """Test visualization module imports and basic functionality."""

    def test_import(self):
        from lingminopt.utils.visualization import (  # noqa: F401
            plot_convergence,
            plot_score_distribution,
            plot_param_importance,
            plot_timeline,
            generate_report,
        )

    def test_plot_convergence_no_history(self):
        from lingminopt.utils.visualization import plot_convergence
        result = OptimizationResult(best_score=0.0, best_params={})
        fig = plot_convergence(result)
        assert fig is None

    def test_plot_convergence_with_history(self, tmp_path):
        from lingminopt.utils.visualization import plot_convergence
        history = [
            Experiment(experiment_id=i, params={"x": float(i)}, score=float(10 - i))
            for i in range(10)
        ]
        result = OptimizationResult(
            best_score=0.0, best_params={"x": 10.0}, history=history, total_experiments=10
        )
        save_path = str(tmp_path / "conv.png")
        fig = plot_convergence(result, save_path=save_path)
        assert fig is not None
        assert Path(save_path).exists()

    def test_plot_distribution(self, tmp_path):
        from lingminopt.utils.visualization import plot_score_distribution
        history = [
            Experiment(experiment_id=i, params={"x": float(i)}, score=float(i * 0.5))
            for i in range(20)
        ]
        result = OptimizationResult(
            best_score=0.0, best_params={"x": 0.0}, history=history
        )
        save_path = str(tmp_path / "dist.png")
        fig = plot_score_distribution(result, save_path=save_path)
        assert fig is not None
        assert Path(save_path).exists()

    def test_plot_importance(self, tmp_path):
        from lingminopt.utils.visualization import plot_param_importance
        history = [
            Experiment(
                experiment_id=i,
                params={"x": float(i), "y": float(i * 2)},
                score=float(i),
            )
            for i in range(20)
        ]
        result = OptimizationResult(
            best_score=0.0, best_params={"x": 0.0, "y": 0.0}, history=history
        )
        save_path = str(tmp_path / "importance.png")
        fig = plot_param_importance(result, save_path=save_path)
        assert fig is not None
        assert Path(save_path).exists()

    def test_generate_report(self, tmp_path):
        from lingminopt.utils.visualization import generate_report
        history = [
            Experiment(
                experiment_id=i,
                params={"x": float(i)},
                score=float(i),
                timestamp=__import__("datetime").datetime.now(),
            )
            for i in range(10)
        ]
        result = OptimizationResult(
            best_score=0.0, best_params={"x": 0.0}, history=history
        )
        saved = generate_report(result, output_dir=str(tmp_path))
        assert len(saved) >= 3
        for path in saved:
            assert Path(path).exists()


class TestMCPFeedbackTools:
    """Test MCP feedback tools from mcp_server."""

    def test_feedback_from_result(self, tmp_path):
        from lingminopt.mcp_server import tool_feedback_from_result

        history = [
            Experiment(experiment_id=i, params={"x": float(i)}, score=float(10 - i))
            for i in range(5)
        ]
        result = OptimizationResult(
            best_score=0.0, best_params={"x": 10.0}, history=history, total_experiments=5
        )
        result_path = str(tmp_path / "result.json")
        result.save(result_path)

        import os
        old_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        try:
            fb = tool_feedback_from_result(result_path, feedback_type="improvement", rating=4)
            assert fb["feedback_type"] == "improvement"
            assert fb["rating"] == 4
            assert "result_summary" in fb
            assert "saved_to" in fb
        finally:
            os.chdir(old_cwd)

    def test_export_training_sample(self, tmp_path):
        from lingminopt.mcp_server import tool_export_training_sample

        history = [
            Experiment(experiment_id=i, params={"x": float(i)}, score=float(10 - i))
            for i in range(20)
        ]
        result = OptimizationResult(
            best_score=0.0, best_params={"x": 10.0}, history=history, total_experiments=20
        )
        result_path = str(tmp_path / "result.json")
        result.save(result_path)

        import os
        old_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        try:
            export = tool_export_training_sample(result_path, sample_type="top_k")
            assert export["count"] >= 1
            assert "saved_to" in export
        finally:
            os.chdir(old_cwd)


class TestCompareResults:
    """Test compare_results MCP tool."""

    def test_compare(self, tmp_path):
        from lingminopt.mcp_server import tool_compare_results

        r1 = OptimizationResult(
            best_score=5.0, best_params={"x": 1.0, "y": 2.0},
            total_experiments=10, total_time=1.0,
        )
        r2 = OptimizationResult(
            best_score=3.0, best_params={"x": 1.5, "y": 2.0},
            total_experiments=20, total_time=2.0,
        )
        p1 = str(tmp_path / "r1.json")
        p2 = str(tmp_path / "r2.json")
        r1.save(p1)
        r2.save(p2)

        result = tool_compare_results(p1, p2)
        assert result["score"]["delta"] == -2.0
        assert result["params_changed"] == 1
        assert result["param_diff"]["x"]["a"] == 1.0
        assert result["param_diff"]["x"]["b"] == 1.5
