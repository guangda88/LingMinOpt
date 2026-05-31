"""Tests for MCP server tool functions."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lingminopt import OptimizationResult, Experiment, ExperimentConfig


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "results").mkdir()
    yield


class TestEvaluatorRegistry:
    def test_get_evaluator_known(self):
        from lingminopt.mcp_server import _get_evaluator

        fn = _get_evaluator("sphere")
        assert callable(fn)
        assert fn({"x": 0.0}) == 0.0

    def test_get_evaluator_unknown_raises(self):
        from lingminopt.mcp_server import _get_evaluator

        with pytest.raises(ValueError, match="Unknown evaluator"):
            _get_evaluator("nonexistent")

    def test_all_evaluators_callable(self):
        from lingminopt.mcp_server import _EVALUATOR_REGISTRY

        for name, entry in _EVALUATOR_REGISTRY.items():
            fn = entry["fn"]
            assert callable(fn)
            result = fn({"x": 1.0, "y": 2.0})
            assert isinstance(result, float)


def _make_experiment(i, score=None):
    from lingminopt import Experiment
    return Experiment(experiment_id=i, params={"x": float(i)}, score=score if score is not None else float(i))


class TestValidateDataPath:
    def test_valid_data_path(self):
        from lingminopt.mcp_server import _validate_data_path

        p = _validate_data_path("data/test.json")
        assert "data" in str(p)

    def test_valid_results_path(self):
        from lingminopt.mcp_server import _validate_data_path

        p = _validate_data_path("results/test.json")
        assert "results" in str(p)

    def test_traversal_denied(self):
        from lingminopt.mcp_server import _validate_data_path

        with pytest.raises(ValueError):
            _validate_data_path("data/../../../etc/passwd")

    def test_outside_denied(self):
        from lingminopt.mcp_server import _validate_data_path

        with pytest.raises(ValueError, match="outside allowed"):
            _validate_data_path("/tmp/evil.json")


class TestCreateSearchSpace:
    def test_creates_space(self):
        from lingminopt.mcp_server import tool_create_search_space

        cfg = json.dumps({"continuous": {"x": [-5, 5]}})
        result = tool_create_search_space(config_json=cfg)
        assert result["status"] == "created"
        assert "x" in result["sample_params"]


class TestRunOptimization:
    def test_runs_sphere(self):
        from lingminopt.mcp_server import tool_run_optimization

        cfg = json.dumps({"continuous": {"x": [-2, 2]}})
        result = tool_run_optimization(
            search_space_config=cfg,
            evaluator="sphere",
            max_experiments=5,
            strategy="random",
        )
        assert "best_score" in result
        assert "best_params" in result

    def test_unknown_evaluator_returns_error(self):
        from lingminopt.mcp_server import tool_run_optimization

        cfg = json.dumps({"continuous": {"x": [-2, 2]}})
        with pytest.raises(ValueError, match="Unknown evaluator"):
            tool_run_optimization(
                search_space_config=cfg,
                evaluator="bad_name",
                max_experiments=5,
            )


class TestListEvaluators:
    def test_lists_all(self):
        from lingminopt.mcp_server import tool_list_evaluators

        result = tool_list_evaluators()
        assert result["count"] >= 6
        assert "sphere" in result["evaluators"]
        assert "rastrigin" in result["evaluators"]


class TestGetOptimizationStatus:
    def test_no_active_run(self):
        from lingminopt.mcp_server import tool_get_optimization_status

        result = tool_get_optimization_status()
        assert result["status"] == "no_active_run"


class TestCreateStrategyProfile:
    def test_creates_random(self):
        from lingminopt.mcp_server import tool_create_strategy_profile

        cfg = json.dumps({"continuous": {"x": [-1, 1]}})
        result = tool_create_strategy_profile(
            strategy_name="random",
            search_space_config=cfg,
        )
        assert result["strategy"] == "random"

    def test_creates_tpe(self):
        from lingminopt.mcp_server import tool_create_strategy_profile

        cfg = json.dumps({"continuous": {"x": [-1, 1]}})
        result = tool_create_strategy_profile(
            strategy_name="tpe",
            search_space_config=cfg,
            seed=42,
        )
        assert result["strategy"] == "tpe"


class TestLoadResults:
    def test_load_missing_file(self):
        from lingminopt.mcp_server import tool_load_results

        result = tool_load_results(filepath="data/missing.json")
        assert "error" in result

    def test_load_valid_file(self, tmp_path):
        from lingminopt.mcp_server import tool_load_results

        exp = _make_experiment(0, score=2.0)
        r = OptimizationResult(
            best_params={"x": 0.0},
            best_score=0.0,
            total_experiments=1,
            total_time=0.1,
            history=[exp],
            improvement=2.0,
        )
        fp = str(tmp_path / "data" / "test_result.json")
        r.save(fp)

        result = tool_load_results(filepath="data/test_result.json")
        assert result["best_score"] == 0.0


class TestCompareResults:
    def test_compare_two(self, tmp_path):
        from lingminopt.mcp_server import tool_compare_results

        r1 = OptimizationResult(
            best_params={"x": 1.0}, best_score=1.0,
            total_experiments=10, total_time=1.0, history=[], improvement=0.0,
        )
        r2 = OptimizationResult(
            best_params={"x": 0.5}, best_score=0.5,
            total_experiments=20, total_time=2.0, history=[], improvement=0.5,
        )
        r1.save(str(tmp_path / "data" / "r1.json"))
        r2.save(str(tmp_path / "data" / "r2.json"))

        result = tool_compare_results(
            filepath_a="data/r1.json", filepath_b="data/r2.json"
        )
        assert result["score"]["delta"] == -0.5
        assert result["experiments"]["delta"] == 10

    def test_compare_missing_file(self):
        from lingminopt.mcp_server import tool_compare_results

        result = tool_compare_results(
            filepath_a="data/missing.json", filepath_b="data/also_missing.json"
        )
        assert "error" in result


class TestCreateExperimentConfig:
    def test_creates_config(self):
        from lingminopt.mcp_server import tool_create_experiment_config

        result = tool_create_experiment_config(max_experiments=50, direction="maximize")
        assert result["max_experiments"] == 50
        assert result["direction"] == "maximize"


class TestFeedbackFromResult:
    def test_generates_feedback(self, tmp_path):
        from lingminopt.mcp_server import tool_feedback_from_result

        r = OptimizationResult(
            best_params={"x": 0.0}, best_score=0.1,
            total_experiments=5, total_time=0.5, history=[], improvement=0.1,
        )
        fp = str(tmp_path / "data" / "fb_result.json")
        r.save(fp)

        result = tool_feedback_from_result(
            result_filepath="data/fb_result.json",
            feedback_type="improvement",
            rating=4,
            comment="good",
        )
        assert result["feedback_type"] == "improvement"
        assert result["rating"] == 4
        assert "saved_to" in result

    def test_invalid_feedback_type(self, tmp_path):
        from lingminopt.mcp_server import tool_feedback_from_result

        r = OptimizationResult(
            best_params={"x": 0.0}, best_score=0.1,
            total_experiments=1, total_time=0.1, history=[], improvement=0.0,
        )
        fp = str(tmp_path / "data" / "fb2.json")
        r.save(fp)

        result = tool_feedback_from_result(
            result_filepath="data/fb2.json", feedback_type="bad_type"
        )
        assert "error" in result

    def test_invalid_rating(self, tmp_path):
        from lingminopt.mcp_server import tool_feedback_from_result

        r = OptimizationResult(
            best_params={"x": 0.0}, best_score=0.1,
            total_experiments=1, total_time=0.1, history=[], improvement=0.0,
        )
        fp = str(tmp_path / "data" / "fb3.json")
        r.save(fp)

        result = tool_feedback_from_result(
            result_filepath="data/fb3.json", rating=10
        )
        assert "error" in result


class TestExportTrainingSample:
    def test_export_best_only(self, tmp_path):
        from lingminopt.mcp_server import tool_export_training_sample

        exp = _make_experiment(0, score=1.0)
        r = OptimizationResult(
            best_params={"x": 1.0}, best_score=1.0,
            total_experiments=1, total_time=0.1, history=[exp], improvement=0.0,
        )
        fp = str(tmp_path / "data" / "exp_result.json")
        r.save(fp)

        result = tool_export_training_sample(
            result_filepath="data/exp_result.json", sample_type="best_only"
        )
        assert result["count"] == 1
        assert "saved_to" in result

    def test_export_all(self, tmp_path):
        from lingminopt.mcp_server import tool_export_training_sample

        exps = [_make_experiment(i) for i in range(5)]
        r = OptimizationResult(
            best_params={"x": 0.0}, best_score=0.0,
            total_experiments=5, total_time=0.5, history=exps, improvement=0.0,
        )
        fp = str(tmp_path / "data" / "exp_all.json")
        r.save(fp)

        result = tool_export_training_sample(
            result_filepath="data/exp_all.json", sample_type="all"
        )
        assert result["count"] == 5

    def test_export_trajectory(self, tmp_path):
        from lingminopt.mcp_server import tool_export_training_sample

        exps = [_make_experiment(i) for i in range(3)]
        r = OptimizationResult(
            best_params={"x": 0.0}, best_score=0.0,
            total_experiments=3, total_time=0.3, history=exps, improvement=0.0,
        )
        fp = str(tmp_path / "data" / "exp_traj.json")
        r.save(fp)

        result = tool_export_training_sample(
            result_filepath="data/exp_traj.json", sample_type="trajectory"
        )
        assert result["count"] == 3

    def test_export_invalid_type(self, tmp_path):
        from lingminopt.mcp_server import tool_export_training_sample

        r = OptimizationResult(
            best_params={"x": 0.0}, best_score=0.0,
            total_experiments=1, total_time=0.1, history=[], improvement=0.0,
        )
        fp = str(tmp_path / "data" / "exp_inv.json")
        r.save(fp)

        result = tool_export_training_sample(
            result_filepath="data/exp_inv.json", sample_type="invalid"
        )
        assert "error" in result


class TestListFeedback:
    def test_empty_feedback_dir(self):
        from lingminopt.mcp_server import tool_list_feedback

        result = tool_list_feedback()
        assert result["count"] == 0

    def test_lists_existing_feedback(self, tmp_path):
        from lingminopt.mcp_server import tool_list_feedback

        fb_dir = tmp_path / "data" / "feedback"
        fb_dir.mkdir(parents=True)
        for i in range(3):
            fb = {"id": f"fb_{i}", "feedback_type": "improvement"}
            with open(fb_dir / f"feedback_fb_{i}.json", "w") as f:
                json.dump(fb, f)

        result = tool_list_feedback()
        assert result["count"] == 3

    def test_filters_by_type(self, tmp_path):
        from lingminopt.mcp_server import tool_list_feedback

        fb_dir = tmp_path / "data" / "feedback"
        fb_dir.mkdir(parents=True)
        for i, ft in enumerate(["improvement", "regression", "improvement"]):
            fb = {"id": f"fb_{i}", "feedback_type": ft}
            with open(fb_dir / f"feedback_fb_{i}.json", "w") as f:
                json.dump(fb, f)

        result = tool_list_feedback(feedback_type="improvement")
        assert result["count"] == 2


class TestListAuditLog:
    def test_reads_from_fresh_log(self, tmp_path):
        from lingminopt.mcp_server import tool_list_audit_log
        import lingminopt.mcp_server as mod

        orig = mod._AUDIT_LOG_PATH
        fresh = tmp_path / "data" / "audit_fresh.jsonl"
        mod._AUDIT_LOG_PATH = fresh
        try:
            result = tool_list_audit_log()
            assert result["count"] >= 1
            assert result["entries"][0]["tool"] == "tool_list_audit_log"
        finally:
            mod._AUDIT_LOG_PATH = orig

    def test_reads_entries(self, tmp_path):
        from lingminopt.mcp_server import tool_list_audit_log
        import lingminopt.mcp_server as mod

        orig = mod._AUDIT_LOG_PATH
        mod._AUDIT_LOG_PATH = tmp_path / "data" / "audit_test.jsonl"
        mod._AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            for i in range(5):
                entry = {"tool": f"tool_{i}", "params_keys": []}
                with open(mod._AUDIT_LOG_PATH, "a") as f:
                    f.write(json.dumps(entry) + "\n")

            result = tool_list_audit_log(limit=3)
            assert result["count"] == 3
        finally:
            mod._AUDIT_LOG_PATH = orig

    def test_filters_by_tool(self, tmp_path):
        from lingminopt.mcp_server import tool_list_audit_log
        import lingminopt.mcp_server as mod

        orig = mod._AUDIT_LOG_PATH
        mod._AUDIT_LOG_PATH = tmp_path / "data" / "audit_filter.jsonl"
        mod._AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(mod._AUDIT_LOG_PATH, "w") as f:
                f.write(json.dumps({"tool": "run_optimization"}) + "\n")
                f.write(json.dumps({"tool": "list_evaluators"}) + "\n")
                f.write(json.dumps({"tool": "run_optimization"}) + "\n")

            result = tool_list_audit_log(tool_filter="run_optimization")
            assert result["count"] == 2
        finally:
            mod._AUDIT_LOG_PATH = orig


class TestOptimizationPipeline:
    def test_pipeline_runs(self):
        from lingminopt.mcp_server import tool_optimization_pipeline

        cfg = json.dumps({"continuous": {"x": [-1, 1]}})
        result = tool_optimization_pipeline(
            search_space_config=cfg,
            evaluator="sphere",
            max_experiments=3,
            strategy="random",
        )
        assert "optimization" in result
        assert "feedback" in result
        assert "training_export" in result
        assert result["optimization"]["total_experiments"] == 3


_COLLECTOR_PATH = "lingminopt.meta_optimizer.lingbus_collector.LingBusCollector"


def _fake_member(name, inp, out, calls=10):
    s = MagicMock()
    s.member = name
    s.estimated_input_tokens = inp
    s.estimated_output_tokens = out
    s.total_tool_calls = calls
    return s


def _fake_record(query="test", model="glm-5.1", agent="lingminopt", inp=100, out=200):
    return MagicMock(query=query, model=model, agent=agent,
                     input_tokens=inp, output_tokens=out, success=True)


class TestMKOTokenRanking:
    def test_empty_stats(self):
        from lingminopt.mcp_server import tool_mko_token_ranking

        with patch(_COLLECTOR_PATH) as MockCls:
            MockCls.return_value.collect_all_stats.return_value = {}
            result = tool_mko_token_ranking()
            assert result["members"] == []
            assert result["total_tokens"] == 0

    def test_with_stats(self):
        from lingminopt.mcp_server import tool_mko_token_ranking

        fake = {
            "lingzhi": _fake_member("lingzhi", 1000, 10000),
            "lingminopt": _fake_member("lingminopt", 100, 700),
            "lingxi": _fake_member("lingxi", 300, 600),
        }
        with patch(_COLLECTOR_PATH) as MockCls:
            MockCls.return_value.collect_all_stats.return_value = fake
            result = tool_mko_token_ranking(limit=3)
            assert result["count"] == 3
            assert result["members"][0]["member"] == "lingzhi"
            assert result["members"][0]["percentage"] > 10
            assert "高优" in result["members"][0]["suggestion"]
            assert "中优" in result["members"][1]["suggestion"]


class TestMKORun:
    def test_no_lingbus_data(self):
        from lingminopt.mcp_server import tool_mko_run

        with patch(_COLLECTOR_PATH) as MockCls:
            MockCls.return_value.collect_lingbus_messages.return_value = []
            result = tool_mko_run()
            assert "error" in result

    def test_prompt_optimization(self):
        from lingminopt.mcp_server import tool_mko_run

        with patch(_COLLECTOR_PATH) as MockCls:
            MockCls.return_value.collect_lingbus_messages.return_value = [_fake_record()]
            result = tool_mko_run(optimization_type="prompt", n_trials=2, data_limit=10)
            assert result["optimization_type"] == "prompt"
            assert "best_score" in result
            assert result["data_points"] == 1

    def test_unknown_type(self):
        from lingminopt.mcp_server import tool_mko_run

        with patch(_COLLECTOR_PATH) as MockCls:
            MockCls.return_value.collect_lingbus_messages.return_value = [_fake_record()]
            result = tool_mko_run(optimization_type="unknown")
            assert "error" in result

    def test_routing_optimization(self):
        from lingminopt.mcp_server import tool_mko_run

        with patch(_COLLECTOR_PATH) as MockCls:
            MockCls.return_value.collect_lingbus_messages.return_value = [_fake_record()]
            result = tool_mko_run(optimization_type="routing", n_trials=2)
            assert result["optimization_type"] == "routing"

    def test_retry_optimization(self):
        from lingminopt.mcp_server import tool_mko_run

        with patch(_COLLECTOR_PATH) as MockCls:
            MockCls.return_value.collect_lingbus_messages.return_value = [_fake_record()]
            result = tool_mko_run(optimization_type="retry", n_trials=2)
            assert result["optimization_type"] == "retry"


class TestMKORecommendations:
    def test_no_data(self):
        from lingminopt.mcp_server import tool_mko_recommendations

        with patch(_COLLECTOR_PATH) as MockCls:
            MockCls.return_value.collect_lingbus_messages.return_value = []
            result = tool_mko_recommendations()
            assert "error" in result

    def test_with_data(self):
        from lingminopt.mcp_server import tool_mko_recommendations

        with patch(_COLLECTOR_PATH) as MockCls:
            MockCls.return_value.collect_lingbus_messages.return_value = [_fake_record(inp=500, out=800)]
            result = tool_mko_recommendations()
            assert "prompt_optimization" in result
            assert "routing_optimization" in result
            assert "retry_optimization" in result
            assert "savings_estimate" in result
            assert result["data_points"] == 1


class TestMainFunction:
    def test_main_calls_mcp_run(self):
        import lingminopt.mcp_server as mod

        with patch.object(mod.mcp, "run") as mock_run:
            mod.main()
            mock_run.assert_called_once()
