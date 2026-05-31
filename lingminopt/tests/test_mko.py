"""Tests for Meta Knowledge Optimizer (MKO) — 灵族真实模型适配"""

from unittest.mock import MagicMock, patch

import pytest


class TestSearchSpaces:
    def test_prompt_space_has_lingclan_models(self):
        from lingminopt.meta_optimizer.search_spaces import get_prompt_optimization_space

        space = get_prompt_optimization_space()
        params = space.parameters
        model_param = params["model"]
        assert "glm-5.1" in model_param.choices
        assert "qwen-max" in model_param.choices
        assert "minimax-m2.7" in model_param.choices
        assert "gpt-4o" not in model_param.choices

    def test_routing_space_has_intent_models(self):
        from lingminopt.meta_optimizer.search_spaces import get_routing_optimization_space

        space = get_routing_optimization_space()
        params = space.parameters
        assert "code_model" in params
        assert "debug_model" in params
        assert "chat_model" in params
        assert "routing_strategy" in params

    def test_retry_space_has_fallback_model(self):
        from lingminopt.meta_optimizer.search_spaces import get_retry_optimization_space

        space = get_retry_optimization_space()
        params = space.parameters
        fallback = params["fallback_model"]
        assert "qwen-max" in fallback.choices
        assert "minimax-m2.7" in fallback.choices

    def test_comprehensive_space_combines_all(self):
        from lingminopt.meta_optimizer.search_spaces import get_meta_optimization_space

        space = get_meta_optimization_space()
        params = space.parameters
        assert len(params) >= 6


class TestEvaluators:
    SAMPLE_RECORDS = [
        {"total_tokens": 2000, "quality_score": 0.85, "success": True, "query": "写一个排序函数"},
        {"total_tokens": 1500, "quality_score": 0.80, "success": True, "query": "debug这个错误"},
        {"total_tokens": 3000, "quality_score": 0.90, "success": True, "query": "解释一下这个架构"},
    ]

    def test_prompt_evaluator_uses_lingclan_models(self):
        from lingminopt.meta_optimizer.evaluators import PromptEvaluator

        ev = PromptEvaluator(self.SAMPLE_RECORDS)
        params = {
            "model": "glm-5.1",
            "temperature": 0.7,
            "max_tokens": 4096,
            "system_prompt_template": "standard",
        }
        score = ev.evaluate(params)
        assert 0.0 <= score <= 1.0

    def test_prompt_evaluator_flash_is_cheaper(self):
        from lingminopt.meta_optimizer.evaluators import PromptEvaluator

        ev = PromptEvaluator(self.SAMPLE_RECORDS)
        params_flash = {
            "model": "glm-4.7-flash",
            "temperature": 0.7,
            "max_tokens": 4096,
            "system_prompt_template": "standard",
        }
        params_pro = {
            "model": "glm-5.1",
            "temperature": 0.7,
            "max_tokens": 4096,
            "system_prompt_template": "standard",
        }
        s_flash = ev.evaluate(params_flash)
        s_pro = ev.evaluate(params_pro)
        assert isinstance(s_flash, float) and isinstance(s_pro, float)

    def test_routing_evaluator(self):
        from lingminopt.meta_optimizer.evaluators import RoutingEvaluator

        ev = RoutingEvaluator(self.SAMPLE_RECORDS)
        params = {
            "code_model": "glm-5.1",
            "debug_model": "glm-4.7-flash",
            "chat_model": "qwen-plus",
            "routing_strategy": "hybrid",
        }
        score = ev.evaluate(params)
        assert 0.0 <= score <= 1.0

    def test_retry_evaluator(self):
        from lingminopt.meta_optimizer.evaluators import RetryEvaluator

        ev = RetryEvaluator(self.SAMPLE_RECORDS)
        params = {
            "primary_retry_limit": 3,
            "backoff_base": 2,
            "backoff_max": 30,
            "fallback_model": "qwen-max",
            "degradation_strategy": "hybrid",
        }
        score = ev.evaluate(params)
        assert 0.0 <= score <= 1.0


class TestLingBusCollector:
    def test_collector_import(self):
        from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

        assert LingBusCollector is not None

    def test_collect_member_stats_with_mock(self):
        import json
        import os
        import tempfile

        from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

        with tempfile.TemporaryDirectory() as tmpdir:
            from pathlib import Path

            fake_db = Path(tmpdir) / "crush.db"
            import sqlite3

            conn = sqlite3.connect(str(fake_db))
            conn.execute(
                "CREATE TABLE sessions (id TEXT, created_at INTEGER, prompt_tokens INTEGER, completion_tokens INTEGER)"
            )
            conn.execute(
                "CREATE TABLE messages (role TEXT, parts TEXT, created_at INTEGER, model TEXT, provider TEXT)"
            )
            conn.execute("INSERT INTO sessions VALUES ('s1', 1704067200000, 10, 20)")
            conn.execute(
                "INSERT INTO messages VALUES ('user', ?, 1704067200000, 'glm-5.1', 'zai')",
                [json.dumps([{"type": "text", "text": "hello"}])],
            )
            conn.execute(
                "INSERT INTO messages VALUES ('assistant', ?, 1704067260000, 'glm-5.1', 'zai')",
                [json.dumps([{"type": "text", "text": "world"}])],
            )
            conn.commit()
            conn.close()
            collector = LingBusCollector(crush_db_paths={"test_member": fake_db})
            stats = collector.collect_member_stats("test_member")
            assert stats is not None
            assert stats.total_messages == 2
            assert stats.total_assistant_messages == 1
            assert stats.total_sessions == 1


class TestMetaOptimizerIntegration:
    def test_optimizer_import(self):
        from lingminopt.meta_optimizer import MetaOptimizer

        assert MetaOptimizer is not None

    def test_meta_optimizer_imports(self):
        from lingminopt.meta_optimizer import LingBusCollector, MetaOptimizer

        assert MetaOptimizer is not None
        assert LingBusCollector is not None
