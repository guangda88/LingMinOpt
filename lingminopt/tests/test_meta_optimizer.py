"""
Meta Optimizer Tests - 元知识优化模块测试
"""

from __future__ import annotations

import pytest
from pathlib import Path
import json
from typing import Any

from lingminopt.meta_optimizer.data_collector import DataCollector, SessionRecord
from lingminopt.meta_optimizer.feature_extractor import FeatureExtractor, TaskFeatures, IntentType, TaskComplexity
from lingminopt.meta_optimizer.search_spaces import (
    get_prompt_optimization_space,
    get_routing_optimization_space,
    get_retry_optimization_space,
)
from lingminopt.meta_optimizer.evaluators import (
    PromptEvaluator,
    RoutingEvaluator,
    RetryEvaluator,
)
from lingminopt.meta_optimizer.optimizer import MetaOptimizer
from lingminopt.meta_optimizer.report_generator import ReportGenerator


@pytest.fixture
def sample_session_data(tmp_path: Path) -> Path:
    """创建示例会话数据"""
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()

    # 创建 session_history.json
    history = [
        {
            "session_id": "session-001",
            "query": "帮我写一个用户登录的API",
            "created_at": 1649700000.0,
        },
        {
            "session_id": "session-002",
            "query": "修复登录接口的bug",
            "created_at": 1649700100.0,
        },
    ]

    with open(sessions_dir / "session_history.json", "w") as f:
        json.dump(history, f)

    # 创建详细 session 文件
    for i in range(1, 4):
        session_file = sessions_dir / f"session-{i:03d}.json"
        session_data = {
            "messages": [
                {"role": "user", "content": f"Query {i}"},
                {"role": "assistant", "content": f"Response {i}"},
            ],
            "input_tokens": 100 * i,
            "output_tokens": 200 * i,
            "model": "gpt-4o",
            "agent": "implementation",
            "success": True,
        }
        with open(session_file, "w") as f:
            json.dump(session_data, f)

    return sessions_dir


@pytest.fixture
def sample_session_records() -> list[dict[str, Any]]:
    """创建示例会话记录"""
    return [
        {
            "session_id": "001",
            "query": "帮我写一个用户登录的API",
            "model": "gpt-4o",
            "agent": "implementation",
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
            "latency_ms": 1000,
            "success": True,
            "quality_score": 0.9,
        },
        {
            "session_id": "002",
            "query": "修复登录接口的bug",
            "model": "gpt-4o-mini",
            "agent": "debugger",
            "input_tokens": 150,
            "output_tokens": 250,
            "total_tokens": 400,
            "latency_ms": 1500,
            "success": True,
            "quality_score": 0.85,
        },
        {
            "session_id": "003",
            "query": "代码审查",
            "model": "claude-3.5-sonnet",
            "agent": "reviewer",
            "input_tokens": 80,
            "output_tokens": 120,
            "total_tokens": 200,
            "latency_ms": 800,
            "success": True,
            "quality_score": 0.95,
        },
    ]


class TestSessionRecord:
    """SessionRecord 测试"""

    def test_total_tokens(self):
        """测试 total_tokens 属性"""
        record = SessionRecord(
            session_id="001",
            timestamp=1649700000.0,
            query="test",
            model="gpt-4o",
            agent="implementation",
            input_tokens=100,
            output_tokens=200,
            latency_ms=1000,
            success=True,
        )

        assert record.total_tokens == 300

    def test_datetime(self):
        """测试 datetime 属性"""
        import datetime

        timestamp = 1649700000.0
        record = SessionRecord(
            session_id="001",
            timestamp=timestamp,
            query="test",
            model="gpt-4o",
            agent="implementation",
            input_tokens=100,
            output_tokens=200,
            latency_ms=1000,
            success=True,
        )

        expected_dt = datetime.datetime.fromtimestamp(timestamp)
        assert record.datetime == expected_dt


class TestDataCollector:
    """DataCollector 测试"""

    def test_collect_sessions(self, sample_session_data: Path):
        """测试收集会话数据"""
        collector = DataCollector(sample_session_data)
        records = collector.collect_sessions()

        assert len(records) == 3
        assert records[0].session_id == "session-001"
        assert records[0].total_tokens == 300  # 100 + 200

    def test_collect_nonexistent_directory(self):
        """测试收集不存在的目录"""
        with pytest.raises(ValueError):
            DataCollector("/nonexistent/path")

    def test_sample_tasks(self, sample_session_data: Path):
        """测试采样任务"""
        collector = DataCollector(sample_session_data)
        sampled = collector.sample_tasks(n=2, random_seed=42)

        assert len(sampled) == 2
        assert "query" in sampled[0]
        assert "total_tokens" in sampled[0]

    def test_get_statistics(self, sample_session_data: Path):
        """测试获取统计信息"""
        collector = DataCollector(sample_session_data)
        stats = collector.get_statistics()

        assert stats["total_sessions"] == 3
        assert stats["avg_tokens_per_session"] > 0
        assert 0.0 <= stats["success_rate"] <= 1.0
        assert "model_distribution" in stats
        assert "agent_distribution" in stats


class TestTaskFeatures:
    """TaskFeatures 测试"""

    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "session_id": "001",
            "query": "帮我写一个用户登录的API",
            "model": "gpt-4o",
            "agent": "implementation",
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
            "latency_ms": 1000,
            "success": True,
        }

        features = TaskFeatures.from_dict(data)

        assert features.session_id == "001"
        assert features.query == data["query"]
        assert features.intent == IntentType.CODE_GENERATION
        assert features.complexity in TaskComplexity

    def test_infer_intent(self):
        """测试意图推断"""
        # 代码生成
        features1 = TaskFeatures.from_dict({"query": "帮我写一个用户登录的API"})
        assert features1.intent == IntentType.CODE_GENERATION

        # Bug 修复
        features2 = TaskFeatures.from_dict({"query": "修复登录接口的bug"})
        assert features2.intent == IntentType.BUG_FIXING

        # 代码审查
        features3 = TaskFeatures.from_dict({"query": "审查这段代码"})
        assert features3.intent == IntentType.CODE_REVIEW

    def test_infer_complexity(self):
        """测试复杂度推断"""
        # 低复杂度
        features1 = TaskFeatures.from_dict({"query": "hello"})
        assert features1.complexity == TaskComplexity.LOW

        # 高复杂度
        long_query = "x" * 400
        features2 = TaskFeatures.from_dict({"query": long_query})
        assert features2.complexity == TaskComplexity.HIGH


class TestFeatureExtractor:
    """FeatureExtractor 测试"""

    def test_extract_features(self, sample_session_records):
        """测试特征提取"""
        extractor = FeatureExtractor()
        features_list = extractor.extract_features(sample_session_records)

        assert len(features_list) == 3
        assert all(isinstance(f, TaskFeatures) for f in features_list)

    def test_extract_features_by_intent(self, sample_session_records):
        """测试按意图提取特征"""
        extractor = FeatureExtractor()
        features = extractor.extract_features_by_intent(
            sample_session_records,
            IntentType.CODE_GENERATION
        )

        # 所有提取的特征都应该是指定意图
        for f in features:
            assert f.intent == IntentType.CODE_GENERATION

    def test_get_intent_distribution(self, sample_session_records):
        """测试获取意图分布"""
        extractor = FeatureExtractor()
        distribution = extractor.get_intent_distribution(sample_session_records)

        assert isinstance(distribution, dict)
        assert IntentType.CODE_GENERATION in distribution
        assert IntentType.BUG_FIXING in distribution

    def test_get_token_statistics(self, sample_session_records):
        """测试获取 Token 统计"""
        extractor = FeatureExtractor()
        stats = extractor.get_token_statistics(sample_session_records)

        assert "avg_input_tokens" in stats
        assert "avg_output_tokens" in stats
        assert "avg_total_tokens" in stats
        assert "max_total_tokens" in stats
        assert "min_total_tokens" in stats


class TestSearchSpaces:
    """搜索空间测试"""

    def test_prompt_optimization_space(self):
        """测试提示词优化搜索空间"""
        space = get_prompt_optimization_space()

        assert "model" in space.parameters
        assert "temperature" in space.parameters
        assert "max_tokens" in space.parameters
        assert "system_prompt_template" in space.parameters

    def test_routing_optimization_space(self):
        """测试路由优化搜索空间"""
        space = get_routing_optimization_space()

        assert "code_intent_agent" in space.parameters
        assert "debug_intent_agent" in space.parameters
        assert "chat_intent_agent" in space.parameters
        assert "skill_routing_strategy" in space.parameters

    def test_retry_optimization_space(self):
        """测试重试优化搜索空间"""
        space = get_retry_optimization_space()

        assert "primary_retry_limit" in space.parameters
        assert "backoff_base" in space.parameters
        assert "backoff_max" in space.parameters


class TestPromptEvaluator:
    """PromptEvaluator 测试"""

    def test_evaluate(self, sample_session_records):
        """测试评估"""
        evaluator = PromptEvaluator(sample_session_records)

        params = {
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        score = evaluator.evaluate(params)

        assert 0.0 <= score <= 1.0

    def test_evaluate_different_models(self, sample_session_records):
        """测试不同模型的评分"""
        evaluator = PromptEvaluator(sample_session_records)

        params_mini = {"model": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 2048}
        params_full = {"model": "gpt-4o", "temperature": 0.7, "max_tokens": 2048}

        score_mini = evaluator.evaluate(params_mini)
        score_full = evaluator.evaluate(params_full)

        # mini 模型应该有更高的 Token 节省分数（或至少相等）
        assert score_mini >= score_full


class TestRoutingEvaluator:
    """RoutingEvaluator 测试"""

    def test_evaluate(self, sample_session_records):
        """测试评估"""
        evaluator = RoutingEvaluator(sample_session_records)

        params = {
            "code_intent_agent": "implementation",
            "debug_intent_agent": "debugger",
            "chat_intent_agent": "documentation",
            "skill_routing_strategy": "intent_based",
        }

        score = evaluator.evaluate(params)

        assert 0.0 <= score <= 1.0


class TestRetryEvaluator:
    """RetryEvaluator 测试"""

    def test_evaluate(self, sample_session_records):
        """测试评估"""
        evaluator = RetryEvaluator(sample_session_records)

        params = {
            "primary_retry_limit": 3,
            "backoff_base": 5.0,
            "backoff_max": 30.0,
        }

        score = evaluator.evaluate(params)

        assert 0.0 <= score <= 1.0


class TestMetaOptimizer:
    """MetaOptimizer 测试"""

    def test_optimize_prompt(self, sample_session_data: Path):
        """测试优化提示词配置"""
        optimizer = MetaOptimizer(sample_session_data)

        result = optimizer.optimize_prompt(
            max_experiments=5,
            search_strategy="random",
            random_seed=42
        )

        assert "optimization_type" in result
        assert result["optimization_type"] == "prompt"
        assert "best_params" in result
        assert "best_score" in result

    def test_optimize_routing(self, sample_session_data: Path):
        """测试优化路由配置"""
        optimizer = MetaOptimizer(sample_session_data)

        result = optimizer.optimize_routing(
            max_experiments=5,
            search_strategy="random",
            random_seed=42
        )

        assert "optimization_type" in result
        assert result["optimization_type"] == "routing"
        assert "best_params" in result

    def test_optimize_retry(self, sample_session_data: Path):
        """测试优化重试配置"""
        optimizer = MetaOptimizer(sample_session_data)

        result = optimizer.optimize_retry(
            max_experiments=5,
            search_strategy="random",
            random_seed=42
        )

        assert "optimization_type" in result
        assert result["optimization_type"] == "retry"
        assert "best_params" in result


class TestReportGenerator:
    """ReportGenerator 测试"""

    def test_generate_markdown_report(self, tmp_path: Path):
        """测试生成 Markdown 报告"""
        generator = ReportGenerator(tmp_path)

        results = {
            "combined_score": 0.85,
            "prompt_optimization": {"model": "gpt-4o-mini"},
            "routing_optimization": {"code_intent_agent": "implementation"},
            "retry_optimization": {"primary_retry_limit": 3},
        }

        report_path = generator.generate_markdown_report(results)

        assert report_path.exists()
        assert report_path.name == "meta_optimization_report.md"

        # 读取并验证内容
        content = report_path.read_text(encoding="utf-8")
        assert "# 元知识优化报告" in content
        assert "提示词优化" in content
        assert "路由优化" in content
        assert "重试优化" in content

    def test_generate_json_report(self, tmp_path: Path):
        """测试生成 JSON 报告"""
        generator = ReportGenerator(tmp_path)

        results = {
            "combined_score": 0.85,
            "prompt_optimization": {"model": "gpt-4o-mini"},
        }

        report_path = generator.generate_json_report(results)

        assert report_path.exists()

        # 读取并验证内容
        with open(report_path) as f:
            loaded = json.load(f)

        assert loaded["combined_score"] == 0.85
        assert "prompt_optimization" in loaded

    def test_generate_config_file(self, tmp_path: Path):
        """测试生成配置文件"""
        generator = ReportGenerator(tmp_path)

        results = {
            "prompt_optimization": {"model": "gpt-4o-mini"},
            "routing_optimization": {"code_intent_agent": "implementation"},
        }

        config_path = generator.generate_config_file(results)

        assert config_path.exists()
        assert config_path.name == "optimized_config.json"

        # 读取并验证内容
        with open(config_path) as f:
            config = json.load(f)

        assert "version" in config
        assert "generated_at" in config
        assert "prompt_optimization" in config
        assert "routing_optimization" in config
