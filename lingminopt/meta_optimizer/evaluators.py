"""
Evaluators - 元知识优化的评估函数
"""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """评估指标"""
    token_savings_percent: float
    quality_score: float
    success_rate: float
    latency_reduction_percent: float
    cost_reduction_percent: float
    composite_score: float


class PromptEvaluator:
    """提示词配置评估器"""

    def __init__(
        self,
        session_records: list[dict[str, Any]],
        baseline_avg_tokens: float | None = None,
    ):
        """
        初始化评估器

        Args:
            session_records: 会话记录列表
            baseline_avg_tokens: 基准平均 token 数
        """
        self.session_records = session_records
        self.baseline_avg_tokens = baseline_avg_tokens or self._compute_baseline_avg_tokens()

    def evaluate(self, params: dict[str, Any]) -> float:
        """
        评估提示词配置

        Args:
            params: 配置参数字典

        Returns:
            综合评分 (0-1)
        """
        total_tokens = 0
        total_quality = 0.0
        success_count = 0

        for record in self.session_records:
            # 模拟使用当前配置
            simulated = self._simulate_with_config(record, params)

            total_tokens += simulated["total_tokens"]
            total_quality += simulated["quality_score"]
            if simulated["success"]:
                success_count += 1

        n = len(self.session_records)
        avg_tokens = total_tokens / n if n > 0 else 0
        avg_quality = total_quality / n if n > 0 else 0
        success_rate = success_count / n if n > 0 else 0

        # 计算综合分数
        score = self._compute_composite_score(avg_tokens, avg_quality, success_rate)

        logger.debug(
            f"Prompt evaluation: tokens={avg_tokens:.0f}, quality={avg_quality:.3f}, "
            f"success_rate={success_rate:.3f}, score={score:.3f}"
        )

        return score

    def _compute_baseline_avg_tokens(self) -> float:
        """计算基准平均 token 数"""
        if not self.session_records:
            return 1000.0

        total = sum(r.get("total_tokens", 0) for r in self.session_records)
        return total / len(self.session_records)

    def _simulate_with_config(
        self,
        record: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """
        模拟使用给定配置执行任务

        Args:
            record: 原始记录
            params: 配置参数

        Returns:
            模拟结果字典
        """
        model = params.get("model", "gpt-4o")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 4096)
        system_prompt_template = params.get("system_prompt_template", "standard")

        # 基于模型调整 token 消耗
        model_token_multiplier = {
            "gpt-4o": 1.0,
            "gpt-4o-mini": 0.8,
            "claude-3.5-sonnet": 0.9,
            "qwen-plus": 0.7,
        }.get(model, 1.0)

        # 基于系统提示词模板调整
        template_multiplier = {
            "minimal": 0.7,
            "standard": 1.0,
            "detailed": 1.3,
        }.get(system_prompt_template, 1.0)

        # 基于温度调整输出稳定性（影响质量）
        temperature_quality_factor = 1.0 - abs(temperature - 0.7) * 0.3

        # 模拟 token 消耗
        base_tokens = record.get("total_tokens", 1000)
        simulated_tokens = base_tokens * model_token_multiplier * template_multiplier

        # 限制最大输出 token
        output_tokens = min(simulated_tokens * 0.6, max_tokens)
        input_tokens = simulated_tokens * 0.4
        total_tokens = input_tokens + output_tokens

        # 模拟质量分数（简化版）
        base_quality = record.get("quality_score", 0.8)
        simulated_quality = base_quality * temperature_quality_factor

        # 成功率
        success = record.get("success", True)

        return {
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "quality_score": simulated_quality,
            "success": success,
        }

    def _compute_composite_score(
        self,
        avg_tokens: float,
        avg_quality: float,
        success_rate: float,
    ) -> float:
        """
        计算综合分数

        目标：最小化 Token，最大化质量和成功率

        权重: Token 40%, 质量 40%, 成功率 20%
        """
        normalized_tokens = self._normalize(
            avg_tokens,
            min_val=500,
            max_val=10000,
            reverse=True
        )

        score = (
            0.4 * normalized_tokens +
            0.4 * avg_quality +
            0.2 * success_rate
        )

        return max(0.0, min(1.0, score))

    def _normalize(
        self,
        value: float,
        min_val: float,
        max_val: float,
        reverse: bool = False,
    ) -> float:
        """归一化到 [0, 1]"""
        if max_val == min_val:
            return 0.5

        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))

        if reverse:
            normalized = 1.0 - normalized

        return normalized


class RoutingEvaluator:
    """路由配置评估器"""

    def __init__(self, session_records: list[dict[str, Any]]):
        """
        初始化评估器

        Args:
            session_records: 会话记录列表
        """
        self.session_records = session_records

    def evaluate(self, params: dict[str, Any]) -> float:
        """
        评估路由配置

        Args:
            params: 配置参数字典

        Returns:
            综合评分 (0-1)
        """
        total_latency = 0.0
        total_cost = 0.0
        success_count = 0

        for record in self.session_records:
            # 根据配置路由
            agent = self._select_agent(record, params)
            skill = self._select_skill(record, agent, params)

            # 模拟执行
            simulated = self._simulate_execution(record, agent, skill)

            total_latency += simulated["latency_ms"]
            total_cost += simulated["cost_usd"]
            if simulated["success"]:
                success_count += 1

        n = len(self.session_records)
        avg_latency = total_latency / n if n > 0 else 0
        avg_cost = total_cost / n if n > 0 else 0
        success_rate = success_count / n if n > 0 else 0

        # 计算综合分数
        score = self._compute_routing_score(avg_latency, avg_cost, success_rate)

        logger.debug(
            f"Routing evaluation: latency={avg_latency:.0f}ms, cost=${avg_cost:.4f}, "
            f"success_rate={success_rate:.3f}, score={score:.3f}"
        )

        return score

    def _select_agent(
        self,
        record: dict[str, Any],
        params: dict[str, Any],
    ) -> str:
        """根据配置选择 Agent"""
        query = record.get("query", "").lower()

        # 简单意图分类
        if any(kw in query for kw in ["代码", "写", "实现", "code", "write", "implement"]):
            return params.get("code_intent_agent", "implementation")
        elif any(kw in query for kw in ["bug", "错误", "调试", "debug", "error"]):
            return params.get("debug_intent_agent", "debugger")
        else:
            return params.get("chat_intent_agent", "implementation")

    def _select_skill(
        self,
        record: dict[str, Any],
        agent: str,
        params: dict[str, Any],
    ) -> str:
        """根据配置选择 Skill"""
        strategy = params.get("skill_routing_strategy", "intent_based")

        if strategy == "intent_based":
            return "default_skill"
        elif strategy == "capability_based":
            return "capability_skill"
        elif strategy == "cost_based":
            return "low_cost_skill"
        else:  # hybrid
            return "hybrid_skill"

    def _simulate_execution(
        self,
        record: dict[str, Any],
        agent: str,
        skill: str,
    ) -> dict[str, Any]:
        """模拟任务执行"""
        # 基于 Agent 和 Skill 模拟性能
        agent_latency = {
            "implementation": 1000,
            "reviewer": 800,
            "architect": 1200,
            "debugger": 1500,
            "tester": 600,
        }.get(agent, 1000)

        skill_multiplier = {
            "default_skill": 1.0,
            "capability_skill": 1.2,
            "low_cost_skill": 0.8,
            "hybrid_skill": 1.0,
        }.get(skill, 1.0)

        latency_ms = agent_latency * skill_multiplier

        # 简单成本估算
        cost_usd = latency_ms * 0.000001

        # 成功率
        success = record.get("success", True)

        return {
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "success": success,
        }

    def _compute_routing_score(
        self,
        avg_latency: float,
        avg_cost: float,
        success_rate: float,
    ) -> float:
        """
        计算路由综合分数

        目标：最小化延迟和成本，最大化成功率

        权重: 延迟 40%, 成本 30%, 成功率 30%
        """
        normalized_latency = self._normalize(
            avg_latency,
            min_val=500,
            max_val=5000,
            reverse=True
        )

        normalized_cost = self._normalize(
            avg_cost,
            min_val=0.001,
            max_val=0.1,
            reverse=True
        )

        score = (
            0.4 * normalized_latency +
            0.3 * normalized_cost +
            0.3 * success_rate
        )

        return max(0.0, min(1.0, score))

    def _normalize(
        self,
        value: float,
        min_val: float,
        max_val: float,
        reverse: bool = False,
    ) -> float:
        """归一化到 [0, 1]"""
        if max_val == min_val:
            return 0.5

        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))

        if reverse:
            normalized = 1.0 - normalized

        return normalized


class RetryEvaluator:
    """重试配置评估器"""

    def __init__(self, session_records: list[dict[str, Any]]):
        """
        初始化评估器

        Args:
            session_records: 会话记录列表
        """
        self.session_records = session_records

    def evaluate(self, params: dict[str, Any]) -> float:
        """
        评估重试配置

        Args:
            params: 配置参数字典

        Returns:
            综合评分 (0-1)
        """
        total_time = 0.0
        final_success_count = 0

        # 模拟失败场景（假设 10% 的请求失败）
        failed_records = self.session_records[: max(10, len(self.session_records) // 10)]

        for record in failed_records:
            result = self._simulate_retry_process(record, params)

            total_time += result["total_time_ms"]
            if result["final_success"]:
                final_success_count += 1

        n = len(failed_records)
        avg_time = total_time / n if n > 0 else 0
        success_rate = final_success_count / n if n > 0 else 0

        # 计算综合分数
        score = self._compute_retry_score(avg_time, success_rate)

        logger.debug(
            f"Retry evaluation: avg_time={avg_time:.0f}ms, "
            f"success_rate={success_rate:.3f}, score={score:.3f}"
        )

        return score

    def _simulate_retry_process(
        self,
        record: dict[str, Any],
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """模拟重试过程"""
        primary_retry_limit = params.get("primary_retry_limit", 3)
        backoff_base = params.get("backoff_base", 5.0)
        backoff_max = params.get("backoff_max", 30.0)

        # 模拟重试
        total_time = 0.0
        success = False

        for attempt in range(primary_retry_limit + 1):
            # 指数退避
            if attempt > 0:
                backoff = min(backoff_base * (2 ** (attempt - 1)), backoff_max)
                total_time += backoff * 1000  # 转换为毫秒

            # 模拟单次请求延迟
            total_time += 1000  # 基础延迟

            # 模拟成功概率（每次重试增加 20% 成功率）
            success_probability = 0.3 + (attempt * 0.2)

            import random
            if random.random() < success_probability:
                success = True
                break

        return {
            "total_time_ms": total_time,
            "final_success": success,
        }

    def _compute_retry_score(self, avg_time: float, success_rate: float) -> float:
        """
        计算重试综合分数

        目标：最小化平均耗时，最大化最终成功率

        权重: 耗时 50%, 成功率 50%
        """
        normalized_time = self._normalize(
            avg_time,
            min_val=1000,
            max_val=30000,
            reverse=True
        )

        score = 0.5 * normalized_time + 0.5 * success_rate

        return max(0.0, min(1.0, score))

    def _normalize(
        self,
        value: float,
        min_val: float,
        max_val: float,
        reverse: bool = False,
    ) -> float:
        """归一化到 [0, 1]"""
        if max_val == min_val:
            return 0.5

        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))

        if reverse:
            normalized = 1.0 - normalized

        return normalized
