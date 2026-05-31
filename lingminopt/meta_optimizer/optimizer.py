"""
Meta Optimizer - 元知识优化器封装
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from lingminopt import ExperimentConfig, MinimalOptimizer
from lingminopt.meta_optimizer.data_collector import DataCollector
from lingminopt.meta_optimizer.evaluators import (
    PromptEvaluator,
    RetryEvaluator,
    RoutingEvaluator,
)
from lingminopt.meta_optimizer.search_spaces import (
    get_prompt_optimization_space,
    get_retry_optimization_space,
    get_routing_optimization_space,
)

if TYPE_CHECKING:
    from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

logger = logging.getLogger(__name__)


class MetaOptimizer:
    """元知识优化器"""

    def __init__(
        self,
        session_dir: str | Path | None = None,
        lingbus_collector: LingBusCollector | None = None,
    ):
        self.session_dir = Path(session_dir) if session_dir else None
        self.collector = DataCollector(session_dir) if session_dir else None
        self.lingbus_collector = lingbus_collector

    def _collect_records(self, random_seed: int | None = None) -> list[dict]:
        if self.lingbus_collector:
            records = self.lingbus_collector.collect_lingbus_messages(limit=500)
            return [
                {
                    "query": r.query,
                    "model": r.model,
                    "agent": r.agent,
                    "total_tokens": r.input_tokens + r.output_tokens,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "success": r.success,
                    "quality_score": 0.85,
                }
                for r in records
            ]
        if self.collector:
            return self.collector.sample_tasks(n=200, random_seed=random_seed)
        raise ValueError("No data source: provide session_dir or lingbus_collector")

    def optimize_prompt(
        self,
        max_experiments: int = 100,
        time_budget: int = 600,
        search_strategy: str = "bayesian",
        random_seed: int | None = None,
    ) -> dict[str, Any]:
        """
        优化提示词配置

        Args:
            max_experiments: 最大实验次数
            time_budget: 时间预算（秒）
            search_strategy: 搜索策略
            random_seed: 随机种子

        Returns:
            优化结果字典
        """
        logger.info("Starting prompt optimization...")

        # 收集数据
        records = self._collect_records(random_seed)

        search_space = get_prompt_optimization_space()

        evaluator = PromptEvaluator(records)

        def evaluate(params: dict[str, Any]) -> float:
            return evaluator.evaluate(params)

        # 配置优化器
        config = ExperimentConfig(
            max_experiments=max_experiments,
            time_budget=time_budget,
            direction="maximize",
            random_seed=random_seed,
        )

        # 运行优化
        optimizer = MinimalOptimizer(
            evaluate=evaluate,
            search_space=search_space,
            config=config,
            search_strategy=search_strategy,
        )

        result = optimizer.run()

        logger.info(
            f"Prompt optimization complete: best_score={result.best_score:.4f}, "
            f"best_params={result.best_params}"
        )

        return {
            "optimization_type": "prompt",
            "best_params": result.best_params,
            "best_score": result.best_score,
            "history": result.history,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time,
            "improvement": result.improvement,
        }

    def optimize_routing(
        self,
        max_experiments: int = 100,
        time_budget: int = 600,
        search_strategy: str = "bayesian",
        random_seed: int | None = None,
    ) -> dict[str, Any]:
        """
        优化路由配置

        Args:
            max_experiments: 最大实验次数
            time_budget: 时间预算（秒）
            search_strategy: 搜索策略
            random_seed: 随机种子

        Returns:
            优化结果字典
        """
        logger.info("Starting routing optimization...")

        records = self._collect_records(random_seed)

        search_space = get_routing_optimization_space()

        evaluator = RoutingEvaluator(records)

        def evaluate(params: dict[str, Any]) -> float:
            return evaluator.evaluate(params)

        # 配置优化器
        config = ExperimentConfig(
            max_experiments=max_experiments,
            time_budget=time_budget,
            direction="maximize",
            random_seed=random_seed,
        )

        # 运行优化
        optimizer = MinimalOptimizer(
            evaluate=evaluate,
            search_space=search_space,
            config=config,
            search_strategy=search_strategy,
        )

        result = optimizer.run()

        logger.info(
            f"Routing optimization complete: best_score={result.best_score:.4f}, "
            f"best_params={result.best_params}"
        )

        return {
            "optimization_type": "routing",
            "best_params": result.best_params,
            "best_score": result.best_score,
            "history": result.history,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time,
            "improvement": result.improvement,
        }

    def optimize_retry(
        self,
        max_experiments: int = 100,
        time_budget: int = 600,
        search_strategy: str = "bayesian",
        random_seed: int | None = None,
    ) -> dict[str, Any]:
        """
        优化重试配置

        Args:
            max_experiments: 最大实验次数
            time_budget: 时间预算（秒）
            search_strategy: 搜索策略
            random_seed: 随机种子

        Returns:
            优化结果字典
        """
        logger.info("Starting retry optimization...")

        records = self._collect_records(random_seed)

        search_space = get_retry_optimization_space()

        evaluator = RetryEvaluator(records)

        def evaluate(params: dict[str, Any]) -> float:
            return evaluator.evaluate(params)

        # 配置优化器
        config = ExperimentConfig(
            max_experiments=max_experiments,
            time_budget=time_budget,
            direction="maximize",
            random_seed=random_seed,
        )

        # 运行优化
        optimizer = MinimalOptimizer(
            evaluate=evaluate,
            search_space=search_space,
            config=config,
            search_strategy=search_strategy,
        )

        result = optimizer.run()

        logger.info(
            f"Retry optimization complete: best_score={result.best_score:.4f}, "
            f"best_params={result.best_params}"
        )

        return {
            "optimization_type": "retry",
            "best_params": result.best_params,
            "best_score": result.best_score,
            "history": result.history,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time,
            "improvement": result.improvement,
        }

    def optimize_all(
        self,
        max_experiments_per_task: int = 50,
        time_budget_per_task: int = 300,
        search_strategy: str = "bayesian",
        random_seed: int | None = None,
    ) -> dict[str, Any]:
        """
        运行所有优化任务

        Args:
            max_experiments_per_task: 每个任务的最大实验次数
            time_budget_per_task: 每个任务的时间预算（秒）
            search_strategy: 搜索策略
            random_seed: 随机种子

        Returns:
            综合优化结果字典
        """
        logger.info("Starting comprehensive meta optimization...")

        # 运行三个优化任务
        prompt_result = self.optimize_prompt(
            max_experiments=max_experiments_per_task,
            time_budget=time_budget_per_task,
            search_strategy=search_strategy,
            random_seed=random_seed,
        )

        routing_result = self.optimize_routing(
            max_experiments=max_experiments_per_task,
            time_budget=time_budget_per_task,
            search_strategy=search_strategy,
            random_seed=random_seed,
        )

        retry_result = self.optimize_retry(
            max_experiments=max_experiments_per_task,
            time_budget=time_budget_per_task,
            search_strategy=search_strategy,
            random_seed=random_seed,
        )

        # 计算综合分数
        combined_score = (
            prompt_result["best_score"] + routing_result["best_score"] + retry_result["best_score"]
        ) / 3

        logger.info(
            f"Comprehensive meta optimization complete: combined_score={combined_score:.4f}"
        )

        return {
            "combined_score": combined_score,
            "prompt_optimization": prompt_result["best_params"],
            "routing_optimization": routing_result["best_params"],
            "retry_optimization": retry_result["best_params"],
            "detailed_results": {
                "prompt": prompt_result,
                "routing": routing_result,
                "retry": retry_result,
            },
            "total_experiments": (
                prompt_result["total_experiments"]
                + routing_result["total_experiments"]
                + retry_result["total_experiments"]
            ),
            "total_time": (
                prompt_result["total_time"]
                + routing_result["total_time"]
                + retry_result["total_time"]
            ),
        }
