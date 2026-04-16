"""
Search Spaces - 元知识优化的搜索空间定义
"""

from __future__ import annotations

from lingminopt import SearchSpace


def get_prompt_optimization_space() -> SearchSpace:
    """
    提示词优化搜索空间

    优化维度:
    - model: 使用的模型
    - temperature: 温度参数
    - max_tokens: 最大输出 token 数
    - system_prompt_template: 系统提示词模板

    Returns:
        SearchSpace 对象
    """
    space = SearchSpace()
    space.add_discrete("model", ["gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet", "qwen-plus"])
    space.add_continuous("temperature", 0.0, 1.0)
    space.add_discrete("max_tokens", [1024, 2048, 3072, 4096, 5120, 6144, 7168, 8192])
    space.add_discrete("system_prompt_template", ["minimal", "standard", "detailed"])

    return space


def get_routing_optimization_space() -> SearchSpace:
    """
    路由优化搜索空间

    优化维度:
    - code_intent_agent: 代码生成意图的路由目标
    - debug_intent_agent: 调试意图的路由目标
    - chat_intent_agent: 对话语意图的路由目标
    - skill_routing_strategy: skill 路由策略

    Returns:
        SearchSpace 对象
    """
    space = SearchSpace()
    space.add_discrete("code_intent_agent", ["implementation", "reviewer", "architect"])
    space.add_discrete("debug_intent_agent", ["debugger", "tester"])
    space.add_discrete("chat_intent_agent", ["implementation", "documentation"])
    space.add_discrete("skill_routing_strategy", [
        "intent_based",
        "capability_based",
        "cost_based",
        "hybrid"
    ])

    return space


def get_retry_optimization_space() -> SearchSpace:
    """
    重试优化搜索空间

    优化维度:
    - primary_retry_limit: 主模型重试次数
    - backoff_base: 退避基数
    - backoff_max: 最大退避时间
    - degraded_call_threshold: 降级调用阈值
    - degraded_time_threshold: 降级时间阈值
    - degradation_strategy: 降级策略

    Returns:
        SearchSpace 对象
    """
    space = SearchSpace()
    space.add_discrete("primary_retry_limit", [1, 2, 3, 4, 5])
    space.add_continuous("backoff_base", 1.0, 10.0)
    space.add_continuous("backoff_max", 10.0, 60.0)
    space.add_discrete("degraded_call_threshold", [5, 10, 15, 20])
    space.add_continuous("degraded_time_threshold", 30.0, 120.0)
    space.add_discrete("degradation_strategy", [
        "model_downgrade",
        "timeout_increase",
        "hybrid"
    ])

    return space


def get_meta_optimization_space() -> SearchSpace:
    """
    综合元知识优化搜索空间（包含所有优化维度）

    Returns:
        SearchSpace 对象
    """
    space = SearchSpace()

    # 提示词优化维度
    space.add_discrete("model", ["gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet", "qwen-plus"])
    space.add_continuous("temperature", 0.0, 1.0)
    space.add_discrete("max_tokens", [1024, 2048, 3072, 4096, 5120, 6144, 7168, 8192])

    # 路由优化维度
    space.add_discrete("code_intent_agent", ["implementation", "reviewer", "architect"])
    space.add_discrete("debug_intent_agent", ["debugger", "tester"])
    space.add_discrete("skill_routing_strategy", ["intent_based", "capability_based", "cost_based", "hybrid"])

    # 重试优化维度
    space.add_discrete("primary_retry_limit", [1, 2, 3, 4, 5])
    space.add_continuous("backoff_base", 1.0, 10.0)
    space.add_continuous("backoff_max", 10.0, 60.0)

    return space
