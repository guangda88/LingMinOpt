"""
Evaluators - 元知识优化的评估函数
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

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
        chosen_model = params.get("model", "glm-5.1")
        score = self._compute_composite_score(
            avg_tokens,
            avg_quality,
            success_rate,
            model=chosen_model,
            n_records=n,
        )

        logger.debug(
            f"Prompt evaluation: model={chosen_model}, tokens={avg_tokens:.0f}, "
            f"quality={avg_quality:.3f}, success_rate={success_rate:.3f}, score={score:.3f}"
        )

        return score

    def _compute_baseline_avg_tokens(self) -> float:
        """计算基准平均 token 数"""
        if not self.session_records:
            return 1000.0

        total = sum(r.get("total_tokens", 0) for r in self.session_records)
        return float(total / len(self.session_records))

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
        model = params.get("model", "glm-5.1")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 4096)
        system_prompt_template = params.get("system_prompt_template", "standard")

        model_token_multiplier = {
            "glm-5.1": 1.0,
            "glm-5-turbo": 0.75,
            "glm-4.7": 0.85,
            "glm-4.7-flash": 0.6,
            "qwen-max": 0.8,
            "qwen-plus": 0.55,
            "minimax-m2.7": 0.7,
            "llama-3.3-70b": 0.65,
        }.get(model, 1.0)

        model_quality_base = {
            "glm-5.1": 0.92,
            "glm-5-turbo": 0.85,
            "glm-4.7": 0.88,
            "glm-4.7-flash": 0.78,
            "qwen-max": 0.87,
            "qwen-plus": 0.75,
            "minimax-m2.7": 0.80,
            "llama-3.3-70b": 0.76,
        }.get(model, 0.8)

        template_multiplier = {
            "minimal": 0.7,
            "standard": 1.0,
            "detailed": 1.3,
        }.get(system_prompt_template, 1.0)

        temperature_quality_factor = 1.0 - abs(temperature - 0.7) * 0.3

        # 模拟 token 消耗
        base_tokens = record.get("total_tokens", 1000)
        simulated_tokens = base_tokens * model_token_multiplier * template_multiplier

        # 限制最大输出 token
        output_tokens = min(simulated_tokens * 0.6, max_tokens)
        input_tokens = simulated_tokens * 0.4
        total_tokens = input_tokens + output_tokens

        base_quality = record.get("quality_score", model_quality_base)
        simulated_quality = min(
            1.0, base_quality * temperature_quality_factor * (model_quality_base / 0.8)
        )

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
        model: str = "glm-5.1",
        n_records: int = 100,
    ) -> float:
        normalized_tokens = self._normalize(
            avg_tokens,
            min_val=500,
            max_val=10000,
            reverse=True,
        )

        prompts_per_5h = n_records
        glm_limit = 600
        is_glm = model.startswith("glm")
        if is_glm and prompts_per_5h > glm_limit * 0.95:
            quota_safety = max(0.0, 1.0 - (prompts_per_5h - glm_limit * 0.8) / (glm_limit * 0.2))
        elif is_glm:
            quota_safety = 1.0
        else:
            quota_safety = 1.0

        score = (
            0.3 * normalized_tokens + 0.35 * avg_quality + 0.15 * success_rate + 0.2 * quota_safety
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
        total_quota_risk = 0.0
        success_count = 0

        strategy = params.get("routing_strategy", "intent_based")
        for record in self.session_records:
            model = self._select_model_for_record(record, params)
            simulated = self._simulate_execution(record, model, strategy)

            total_latency += simulated["latency_ms"]
            total_cost += simulated["cost_usd"]
            total_quota_risk += simulated.get("quota_risk", 0.0)
            if simulated["success"]:
                success_count += 1

        n = len(self.session_records)
        avg_latency = total_latency / n if n > 0 else 0
        avg_cost = total_cost / n if n > 0 else 0
        avg_quota_risk = total_quota_risk / n if n > 0 else 0
        success_rate = success_count / n if n > 0 else 0

        score = self._compute_routing_score(avg_latency, avg_cost, success_rate, avg_quota_risk)

        logger.debug(
            f"Routing evaluation: latency={avg_latency:.0f}ms, cost=${avg_cost:.4f}, "
            f"success_rate={success_rate:.3f}, score={score:.3f}"
        )

        return score

    MODEL_LATENCY_MS = {
        "glm-5.1": 1200,
        "glm-5-turbo": 650,
        "glm-4.7": 1000,
        "glm-4.7-flash": 600,
        "qwen-max": 900,
        "qwen-plus": 500,
        "minimax-m2.7": 800,
        "llama-3.3-70b": 700,
    }
    MODEL_COST_PER_1K_TOKENS = {
        "glm-5.1": 0.0,
        "glm-5-turbo": 0.0,
        "glm-4.7": 0.0,
        "glm-4.7-flash": 0.0,
        "qwen-max": 0.0,
        "qwen-plus": 0.0,
        "minimax-m2.7": 0.0,
        "llama-3.3-70b": 0.0,
    }
    MODEL_RATE_LIMITS = {
        "glm-5.1": (600, 18000),
        "glm-5-turbo": (600, 18000),
        "glm-4.7": (600, 18000),
        "glm-4.7-flash": (600, 18000),
        "qwen-max": (120, 600000),
        "qwen-plus": (120, 600000),
        "minimax-m2.7": (100, 300000),
        "llama-3.3-70b": (100, 300000),
    }
    MODEL_BILLING = {
        "glm-5.1": "包月",
        "glm-5-turbo": "包月",
        "glm-4.7": "包月",
        "glm-4.7-flash": "包月",
        "qwen-max": "永久免费",
        "qwen-plus": "永久免费",
        "minimax-m2.7": "包月",
        "llama-3.3-70b": "免费(NIM)",
    }

    def _select_model_for_record(
        self,
        record: dict[str, Any],
        params: dict[str, Any],
    ) -> str:
        """根据配置和意图选择模型"""
        query = record.get("query", "").lower()
        code_kws = ["代码", "写", "实现", "code", "write", "implement", "refactor"]
        debug_kws = ["bug", "错误", "调试", "debug", "error", "fix"]

        if any(kw in query for kw in code_kws):
            return str(params.get("code_model", "glm-5.1"))
        elif any(kw in query for kw in debug_kws):
            return str(params.get("debug_model", "glm-5.1"))
        else:
            return str(params.get("chat_model", "glm-4.7-flash"))

    def _simulate_execution(
        self,
        record: dict[str, Any],
        model: str,
        strategy: str,
    ) -> dict[str, Any]:
        """模拟任务执行"""
        base_latency = self.MODEL_LATENCY_MS.get(model, 1000)
        strategy_multiplier = {
            "intent_based": 1.0,
            "capability_based": 0.9,
            "cost_based": 0.7,
            "hybrid": 0.95,
        }.get(strategy, 1.0)

        latency_ms = base_latency * strategy_multiplier
        cost_per_1k = self.MODEL_COST_PER_1K_TOKENS.get(model, 0.0)
        tokens = record.get("total_tokens", 2000)
        cost_usd = (tokens / 1000) * cost_per_1k
        success = record.get("success", True)

        is_glm = model.startswith("glm")
        n_records = len(self.session_records)
        glm_prompts_per_5h = n_records if is_glm else 0
        glm_limit = 600
        if glm_prompts_per_5h > glm_limit:
            quota_risk = min(1.0, (glm_prompts_per_5h - glm_limit) / glm_limit)
        elif glm_prompts_per_5h > glm_limit * 0.8:
            quota_risk = (glm_prompts_per_5h - glm_limit * 0.8) / (glm_limit * 0.2) * 0.5
        else:
            quota_risk = 0.0

        return {
            "latency_ms": latency_ms,
            "cost_usd": cost_usd,
            "success": success,
            "quota_risk": quota_risk,
        }

    def _compute_routing_score(
        self,
        avg_latency: float,
        avg_cost: float,
        success_rate: float,
        avg_quota_risk: float = 0.0,
    ) -> float:
        """
        计算路由综合分数

        权重: 延迟 30%, 成本 20%, 成功率 30%, 配额安全 20%
        """
        normalized_latency = self._normalize(avg_latency, min_val=500, max_val=5000, reverse=True)
        normalized_cost = self._normalize(avg_cost, min_val=0.0, max_val=0.01, reverse=True)
        quota_safety = 1.0 - avg_quota_risk

        score = (
            0.30 * normalized_latency
            + 0.20 * normalized_cost
            + 0.30 * success_rate
            + 0.20 * quota_safety
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
            success_probability = min(0.95, 0.3 + (attempt * 0.2))
            if success_probability >= 0.7:
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
        normalized_time = self._normalize(avg_time, min_val=1000, max_val=30000, reverse=True)

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
