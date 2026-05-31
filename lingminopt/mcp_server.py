"""灵极优 MCP Server — 优化工具 + 反馈闭环 + MKO元知识优化。

工具清单 (15):
  搜索空间: create_search_space
  优化执行: run_optimization, get_optimization_status
  策略管理: create_strategy_profile
  结果管理: load_results, compare_results, create_experiment_config
  反馈闭环: feedback_from_result, export_training_sample, list_feedback
  一键闭环: optimization_pipeline
  MKO优化: mko_token_ranking, mko_run, mko_recommendations
  审计日志: list_audit_log

安全: 无exec()/eval()/compile()，使用声明式评估器注册表。
"""

from __future__ import annotations

import functools
import json
import math
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# 声明式评估器注册表（替代exec()）
# ---------------------------------------------------------------------------


def _sphere(params: dict) -> float:
    return sum(v**2 for v in params.values())


def _rastrigin(params: dict) -> float:
    n = len(params)
    return 10 * n + sum(v**2 - 10 * math.cos(2 * math.pi * v) for v in params.values())


def _rosenbrock(params: dict) -> float:
    vals = list(params.values())
    return sum(
        (1 - vals[i]) ** 2 + 100 * (vals[i + 1] - vals[i] ** 2) ** 2 for i in range(len(vals) - 1)
    )


def _ackley(params: dict) -> float:
    vals = list(params.values())
    n = len(vals)
    s1 = sum(v**2 for v in vals)
    s2 = sum(math.cos(2 * math.pi * v) for v in vals)
    return -20 * math.exp(-0.2 * math.sqrt(s1 / n)) - math.exp(s2 / n) + 20 + math.e


def _quadratic(params: dict) -> float:
    return sum((v - 0.5) ** 2 for v in params.values())


def _neg_mean(params: dict) -> float:
    vals = list(params.values())
    return -sum(vals) / max(len(vals), 1)


_EVALUATOR_REGISTRY: Dict[str, dict] = {
    "sphere": {"fn": _sphere, "description": "Sphere function (sum of squares). Min=0 at origin."},
    "rastrigin": {
        "fn": _rastrigin,
        "description": "Rastrigin function. Many local minima, global min=0 at origin.",
    },
    "rosenbrock": {
        "fn": _rosenbrock,
        "description": "Rosenbrock function. Narrow valley, global min=0 at (1,...,1).",
    },
    "ackley": {
        "fn": _ackley,
        "description": "Ackley function. Many local minima, global min≈0 at origin.",
    },
    "quadratic": {
        "fn": _quadratic,
        "description": "Quadratic bowl centered at 0.5. Min=0 at all params=0.5.",
    },
    "neg_mean": {"fn": _neg_mean, "description": "Negative mean. Maximizes sum of params."},
}


def _get_evaluator(name: str) -> Any:
    entry = _EVALUATOR_REGISTRY.get(name)
    if entry is None:
        available = ", ".join(sorted(_EVALUATOR_REGISTRY.keys()))
        raise ValueError(f"Unknown evaluator: {name}. Available: {available}")
    return entry["fn"]


def _validate_data_path(filepath: str) -> Path:
    resolved = Path(filepath).resolve()
    allowed = [Path("data").resolve(), Path("results").resolve()]
    if not any(resolved == d or d in resolved.parents for d in allowed):
        raise ValueError(f"Path outside allowed directories: {filepath}")
    if ".." in Path(filepath).parts:
        raise ValueError(f"Path traversal denied: {filepath}")
    return resolved


# ---------------------------------------------------------------------------
# 审计日志
# ---------------------------------------------------------------------------

_FEEDBACK_DIR = Path("data/feedback")
_TRAINING_EXPORT_DIR = Path("data/training_exports")
_AUDIT_LOG_PATH = Path("data/audit_log.jsonl")


def _audit_log(tool_name: str, params: dict, result_summary: dict | None = None) -> None:
    _AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "params_keys": list(params.keys()),
        "result_summary": result_summary or {},
    }
    with open(_AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _audit_wrap(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = getattr(func, "__name__", str(func))
        _audit_log(tool_name, kwargs)
        result = func(*args, **kwargs)
        if isinstance(result, dict):
            summary_keys = [
                k for k in ("status", "error", "id", "saved_to", "count") if k in result
            ]
            _audit_log(f"{tool_name}_result", {k: result[k] for k in summary_keys})
        return result

    return wrapper


mcp = FastMCP(
    name="lingminopt",
    instructions="灵极优（lingminopt）MCP Server — 超参数优化核心能力 + 反馈闭环",
)


# ---------------------------------------------------------------------------
# 搜索空间 + 优化执行
# ---------------------------------------------------------------------------


@_audit_wrap
@mcp.tool(name="create_search_space", description="创建搜索空间（灵空）")
def tool_create_search_space(config_json: str) -> dict:
    """从JSON配置创建搜索空间。config_json 格式: {"discrete": {"name": [choices]}, "continuous": {"name": [min, max]}}。"""
    from lingminopt import SearchSpace

    config = json.loads(config_json)
    space = SearchSpace.from_dict(config)
    sample = space.sample()
    return {"status": "created", "sample_params": sample}


@_audit_wrap
@mcp.tool(name="run_optimization", description="运行优化（灵优）")
def tool_run_optimization(
    search_space_config: str,
    evaluator: str = "sphere",
    max_experiments: int = 100,
    strategy: str = "random",
    direction: str = "minimize",
    time_budget: float = 300.0,
) -> dict:
    """运行一次优化任务。evaluator 为注册表中的评估函数名（sphere/rastrigin/rosenbrock/ackley/quadratic/neg_mean），接收 params dict，返回 float 分数。"""
    from lingminopt import ExperimentConfig, MinimalOptimizer, SearchSpace

    space = SearchSpace.from_dict(json.loads(search_space_config))
    config = ExperimentConfig(
        max_experiments=max_experiments,
        direction=direction,
        time_budget=time_budget,
    )
    evaluate_fn = _get_evaluator(evaluator)
    optimizer = MinimalOptimizer(
        evaluate=evaluate_fn,
        search_space=space,
        config=config,
        search_strategy=strategy,
    )
    result = optimizer.run()
    return result.to_dict()


@_audit_wrap
@mcp.tool(name="list_evaluators", description="列出可用评估器（灵列评）")
def tool_list_evaluators() -> dict:
    """列出所有已注册的声明式评估器及其描述。"""
    evaluators = {}
    for name, entry in sorted(_EVALUATOR_REGISTRY.items()):
        evaluators[name] = entry["description"]
    return {"evaluators": evaluators, "count": len(evaluators)}


@_audit_wrap
@mcp.tool(name="get_optimization_status", description="优化状态（灵态）")
def tool_get_optimization_status() -> dict:
    """返回当前优化运行状态（需要有正在运行的优化实例）。"""
    return {"status": "no_active_run", "message": "灵极优无活跃优化任务，请先调用 run_optimization"}


@_audit_wrap
@mcp.tool(name="create_strategy_profile", description="创建优化策略（灵策）")
def tool_create_strategy_profile(
    strategy_name: str,
    search_space_config: str,
    seed: int | None = None,
) -> dict:
    """创建优化策略。strategy_name: random/grid/bayesian/annealing。"""
    from lingminopt import SearchSpace
    from lingminopt.core.strategy import create_strategy

    space = SearchSpace.from_dict(json.loads(search_space_config))
    create_strategy(strategy_name, space, seed=seed)
    return {"strategy": strategy_name, "space_params": list(space.sample().keys())}


@_audit_wrap
@mcp.tool(name="load_results", description="加载优化结果（灵果）")
def tool_load_results(filepath: str) -> dict:
    """从JSON文件加载历史优化结果。仅允许data/和results/目录。"""
    from lingminopt import OptimizationResult

    safe_path = _validate_data_path(filepath)
    if not safe_path.exists():
        return {"error": f"File not found: {filepath}"}
    result = OptimizationResult.load(str(safe_path))
    return result.to_dict()


@_audit_wrap
@mcp.tool(name="compare_results", description="对比优化结果（灵比）")
def tool_compare_results(filepath_a: str, filepath_b: str) -> dict:
    """对比两次优化结果，返回差异分析。

    Args:
        filepath_a: 第一次优化结果JSON路径
        filepath_b: 第二次优化结果JSON路径

    Returns:
        对比分析：分数差异、参数差异、实验效率
    """
    from lingminopt import OptimizationResult

    safe_a = _validate_data_path(filepath_a)
    safe_b = _validate_data_path(filepath_b)
    if not safe_a.exists():
        return {"error": f"File not found: {filepath_a}"}
    if not safe_b.exists():
        return {"error": f"File not found: {filepath_b}"}

    ra = OptimizationResult.load(str(safe_a))
    rb = OptimizationResult.load(str(safe_b))

    all_keys = set(ra.best_params.keys()) | set(rb.best_params.keys())
    param_diff = {}
    for k in all_keys:
        va = ra.best_params.get(k, "<missing>")
        vb = rb.best_params.get(k, "<missing>")
        if va != vb:
            param_diff[k] = {"a": va, "b": vb}

    score_delta = rb.best_score - ra.best_score
    time_delta = rb.total_time - ra.total_time
    exp_delta = rb.total_experiments - ra.total_experiments

    return {
        "score": {"a": ra.best_score, "b": rb.best_score, "delta": score_delta},
        "total_time": {"a": ra.total_time, "b": rb.total_time, "delta": time_delta},
        "experiments": {
            "a": ra.total_experiments,
            "b": rb.total_experiments,
            "delta": exp_delta,
        },
        "param_diff": param_diff,
        "params_changed": len(param_diff),
        "params_same": len(all_keys) - len(param_diff),
    }


@_audit_wrap
@mcp.tool(name="create_experiment_config", description="创建实验配置（灵配）")
def tool_create_experiment_config(
    max_experiments: int = 100,
    direction: str = "minimize",
    time_budget: float = 300.0,
    early_stopping_patience: int = 10,
    improvement_threshold: float = 0.001,
    parallel_jobs: int = 1,
) -> dict:
    """创建实验配置参数。返回配置字典。"""
    from lingminopt import ExperimentConfig

    config = ExperimentConfig(
        max_experiments=max_experiments,
        direction=direction,
        time_budget=time_budget,
        early_stopping_patience=early_stopping_patience,
        improvement_threshold=improvement_threshold,
        parallel_jobs=parallel_jobs,
    )
    return {
        "max_experiments": config.max_experiments,
        "direction": config.direction,
        "time_budget": config.time_budget,
        "early_stopping_patience": config.early_stopping_patience,
        "improvement_threshold": config.improvement_threshold,
        "parallel_jobs": config.parallel_jobs,
    }


# ---------------------------------------------------------------------------
# 反馈闭环工具
# ---------------------------------------------------------------------------


@_audit_wrap
@mcp.tool(name="feedback_from_result", description="从优化结果生成反馈（灵馈）")
def tool_feedback_from_result(
    result_filepath: str,
    feedback_type: str = "improvement",
    rating: int | None = None,
    comment: str = "",
    tags: list[str] | None = None,
) -> dict:
    """解析优化结果并生成结构化反馈，用于自优化引擎闭环。

    Args:
        result_filepath: OptimizationResult JSON 文件路径
        feedback_type: 反馈类型 (improvement/regression/insight/waste)
        rating: 1-5 评分（可选）
        comment: 人工注释
        tags: 自定义标签列表

    Returns:
        反馈记录，已持久化至 data/feedback/
    """
    from lingminopt import OptimizationResult

    safe_path = _validate_data_path(result_filepath)
    if not safe_path.exists():
        return {"error": f"File not found: {result_filepath}"}
    result = OptimizationResult.load(str(safe_path))

    if feedback_type not in ("improvement", "regression", "insight", "waste"):
        return {"error": f"Invalid feedback_type: {feedback_type}"}
    if rating is not None and not (1 <= rating <= 5):
        return {"error": "Rating must be 1-5"}

    feedback = {
        "id": uuid.uuid4().hex[:12],
        "timestamp": datetime.now().isoformat(),
        "source": "lingminopt",
        "feedback_type": feedback_type,
        "result_summary": {
            "best_score": result.best_score,
            "best_params": result.best_params,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time,
            "improvement": result.improvement,
        },
        "rating": rating,
        "comment": comment,
        "tags": tags or [],
    }

    _FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _FEEDBACK_DIR / f"feedback_{feedback['id']}.json"
    with open(out_path, "w") as f:
        json.dump(feedback, f, indent=2, ensure_ascii=False)

    feedback["saved_to"] = str(out_path)
    return feedback


def _sample_best_only(history: list, result: Any, include_metadata: bool) -> List[Dict[str, Any]]:
    best_exp = min(history, key=lambda e: e.score)
    return [_exp_to_training(best_exp, result, include_metadata)]


def _sample_top_k(history: list, result: Any, include_metadata: bool) -> List[Dict[str, Any]]:
    sorted_hist = sorted(history, key=lambda e: e.score)
    k = max(1, len(sorted_hist) // 10)
    return [_exp_to_training(exp, result, include_metadata) for exp in sorted_hist[:k]]


def _sample_all(history: list, result: Any, include_metadata: bool) -> List[Dict[str, Any]]:
    return [_exp_to_training(exp, result, include_metadata) for exp in history]


def _sample_trajectory(history: list, result: Any, include_metadata: bool) -> List[Dict[str, Any]]:
    samples = []
    for i, exp in enumerate(history):
        entry = _exp_to_training(exp, result, include_metadata)
        entry["step"] = i
        entry["is_best_so_far"] = exp.score == min(e.score for e in history[: i + 1])
        samples.append(entry)
    return samples


_SAMPLE_DISPATCH = {
    "best_only": _sample_best_only,
    "top_k": _sample_top_k,
    "all": _sample_all,
    "trajectory": _sample_trajectory,
}


@_audit_wrap
@mcp.tool(name="export_training_sample", description="导出训练样本（灵出）")
def tool_export_training_sample(
    result_filepath: str,
    sample_type: str = "best_only",
    output_format: str = "jsonl",
    include_metadata: bool = True,
) -> dict:
    """将优化历史导出为训练数据格式，用于下游训练流水线。

    Args:
        result_filepath: OptimizationResult JSON 文件路径
        sample_type: 采样方式
            - best_only: 仅最优实验
            - top_k: 前 10% 实验
            - all: 全部实验
            - trajectory: 优化轨迹（含时间顺序）
        output_format: 输出格式 (jsonl/json)
        include_metadata: 是否包含元数据

    Returns:
        导出统计 + 文件路径
    """
    from lingminopt import OptimizationResult

    sampler = _SAMPLE_DISPATCH.get(sample_type)
    if sampler is None:
        return {"error": f"Invalid sample_type: {sample_type}"}

    safe_path = _validate_data_path(result_filepath)
    if not safe_path.exists():
        return {"error": f"File not found: {result_filepath}"}
    result = OptimizationResult.load(str(safe_path))
    history = result.history
    if not history:
        return {"error": "No experiments in result history"}

    samples = sampler(history, result, include_metadata)

    _TRAINING_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"training_{sample_type}_{timestamp}.{output_format}"
    out_path = _TRAINING_EXPORT_DIR / filename

    if output_format == "jsonl":
        with open(out_path, "w") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
    else:
        with open(out_path, "w") as f:
            json.dump(samples, f, indent=2, ensure_ascii=False)

    return {
        "sample_type": sample_type,
        "count": len(samples),
        "output_format": output_format,
        "saved_to": str(out_path),
    }


def _exp_to_training(exp: Any, result: Any, include_metadata: bool) -> Dict[str, Any]:
    """Convert an Experiment to a training data dict."""
    entry: Dict[str, Any] = {
        "params": exp.params,
        "score": exp.score,
    }
    if include_metadata:
        entry["metadata"] = {
            "experiment_id": exp.experiment_id,
            "timestamp": exp.timestamp.isoformat() if exp.timestamp else None,
            "best_score": result.best_score,
            "total_experiments": result.total_experiments,
        }
    return entry


@_audit_wrap
@mcp.tool(name="list_feedback", description="列出反馈记录（灵列）")
def tool_list_feedback(
    feedback_type: str = "",
    limit: int = 20,
) -> dict:
    """列出已保存的反馈记录。可按类型过滤。

    Args:
        feedback_type: 过滤类型 (improvement/regression/insight/waste)，空=全部
        limit: 返回数量上限

    Returns:
        反馈列表
    """
    if not _FEEDBACK_DIR.exists():
        return {"feedbacks": [], "count": 0}

    feedbacks: List[Dict[str, Any]] = []
    for fp in sorted(_FEEDBACK_DIR.glob("feedback_*.json"), reverse=True):
        with open(fp) as f:
            fb = json.load(f)
        if feedback_type and fb.get("feedback_type") != feedback_type:
            continue
        feedbacks.append(fb)
        if len(feedbacks) >= limit:
            break

    return {"feedbacks": feedbacks, "count": len(feedbacks)}


@_audit_wrap
@mcp.tool(name="optimization_pipeline", description="优化闭环流水线（灵环）")
def tool_optimization_pipeline(
    search_space_config: str,
    evaluator: str = "sphere",
    max_experiments: int = 50,
    strategy: str = "random",
    direction: str = "minimize",
    time_budget: float = 120.0,
    feedback_type: str = "improvement",
    export_sample_type: str = "top_k",
) -> dict:
    """一键执行完整闭环：运行优化 → 生成反馈 → 导出训练样本。

    Args:
        search_space_config: 搜索空间 JSON 配置
        evaluator: 注册表中的评估函数名
        max_experiments: 最大实验次数
        strategy: 搜索策略
        direction: minimize/maximize
        time_budget: 时间预算（秒）
        feedback_type: 反馈类型
        export_sample_type: 训练样本采样方式

    Returns:
        闭环结果：优化结果 + 反馈记录 + 训练样本路径
    """
    from lingminopt import ExperimentConfig, MinimalOptimizer, SearchSpace

    space = SearchSpace.from_dict(json.loads(search_space_config))
    config = ExperimentConfig(
        max_experiments=max_experiments,
        direction=direction,
        time_budget=time_budget,
    )
    evaluate_fn = _get_evaluator(evaluator)
    optimizer = MinimalOptimizer(
        evaluate=evaluate_fn,
        search_space=space,
        config=config,
        search_strategy=strategy,
    )
    result = optimizer.run()

    _FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = _FEEDBACK_DIR / f"result_{timestamp}.json"
    result.save(str(result_path))

    fb = tool_feedback_from_result(
        result_filepath=str(result_path),
        feedback_type=feedback_type,
        rating=4 if result.improvement > 0 else 2,
        comment=f"Auto feedback from pipeline run ({strategy}, {max_experiments} exps)",
        tags=["pipeline", strategy],
    )

    export = tool_export_training_sample(
        result_filepath=str(result_path),
        sample_type=export_sample_type,
    )

    return {
        "optimization": {
            "best_score": result.best_score,
            "best_params": result.best_params,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time,
            "improvement": result.improvement,
        },
        "feedback": {"id": fb.get("id"), "saved_to": fb.get("saved_to")},
        "training_export": {
            "count": export.get("count"),
            "saved_to": export.get("saved_to"),
        },
    }


@_audit_wrap
@mcp.tool(name="list_audit_log", description="查看审计日志（灵审）")
def tool_list_audit_log(limit: int = 50, tool_filter: str = "") -> dict:
    """查看MCP工具调用审计日志。"""
    if not _AUDIT_LOG_PATH.exists():
        return {"entries": [], "count": 0}
    entries = []
    with open(_AUDIT_LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if tool_filter and entry.get("tool", "") != tool_filter:
                continue
            entries.append(entry)
    entries = entries[-limit:]
    return {"entries": entries, "count": len(entries)}


@_audit_wrap
@mcp.tool(name="mko_token_ranking", description="灵族Token消耗排名（灵排）")
def tool_mko_token_ranking(limit: int = 13) -> dict:
    """从灵族crush.db提取真实会话数据，按token消耗排名并给出优化建议。

    Returns:
        各成员token消耗排名 + 优化建议
    """
    from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector

    collector = LingBusCollector()
    stats = collector.collect_all_stats()
    if not stats:
        return {"members": [], "total_tokens": 0}

    ranked = sorted(
        stats.values(),
        key=lambda s: s.estimated_input_tokens + s.estimated_output_tokens,
        reverse=True,
    )
    total_tokens = sum(s.estimated_input_tokens + s.estimated_output_tokens for s in ranked)

    members = []
    for s in ranked[:limit]:
        total = s.estimated_input_tokens + s.estimated_output_tokens
        out_in = s.estimated_output_tokens / max(s.estimated_input_tokens, 1)
        pct = total / max(total_tokens, 1) * 100
        if pct > 10:
            suggestion = "高优: CRUSH.md瘦身 + max_tokens限制 + 输出截断检查"
        elif pct > 5:
            suggestion = "中优: 非code任务用qwen-plus路由"
        else:
            suggestion = "低优: 维持现状"
        members.append(
            {
                "member": s.member,
                "total_tokens": total,
                "percentage": round(pct, 1),
                "out_in_ratio": round(out_in, 1),
                "tool_calls": s.total_tool_calls,
                "suggestion": suggestion,
            }
        )
    return {"members": members, "total_tokens": total_tokens, "count": len(members)}


@_audit_wrap
@mcp.tool(name="mko_run", description="运行MKO元知识优化（灵优MKO）")
def tool_mko_run(
    optimization_type: str = "prompt",
    n_trials: int = 30,
    data_limit: int = 500,
) -> dict:
    """运行MKO优化：基于灵族真实会话数据优化token消耗。

    Args:
        optimization_type: prompt / routing / retry
        n_trials: 优化尝试次数
        data_limit: 从LingBus拉取的数据量

    Returns:
        最优参数 + token节省估计
    """
    from lingminopt import ExperimentConfig
    from lingminopt.core.optimizer import MinimalOptimizer
    from lingminopt.meta_optimizer.evaluators import (
        PromptEvaluator,
        RetryEvaluator,
        RoutingEvaluator,
    )
    from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector
    from lingminopt.meta_optimizer.search_spaces import (
        get_prompt_optimization_space,
        get_retry_optimization_space,
        get_routing_optimization_space,
    )

    collector = LingBusCollector()
    records = collector.collect_lingbus_messages(limit=data_limit)
    if not records:
        return {"error": "No LingBus data available"}

    session_data = [
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

    if optimization_type == "prompt":
        space = get_prompt_optimization_space()
        evaluator = PromptEvaluator(session_data)
    elif optimization_type == "routing":
        space = get_routing_optimization_space()
        evaluator = RoutingEvaluator(session_data)
    elif optimization_type == "retry":
        space = get_retry_optimization_space()
        evaluator = RetryEvaluator(session_data)
    else:
        return {"error": f"Unknown optimization_type: {optimization_type}"}

    config = ExperimentConfig(max_experiments=n_trials, direction="maximize")
    opt = MinimalOptimizer(
        evaluate=evaluator.evaluate,
        search_space=space,
        config=config,
        search_strategy="bayesian",
    )
    result = opt.run()

    return {
        "optimization_type": optimization_type,
        "best_score": round(result.best_score, 4),
        "best_params": result.best_params,
        "total_experiments": result.total_experiments,
        "data_points": len(session_data),
    }


@_audit_wrap
@mcp.tool(name="mko_recommendations", description="MKO全族优化建议（灵建）")
def tool_mko_recommendations() -> dict:
    """综合运行prompt/routing/retry三种优化，生成灵族全族token优化建议。

    Returns:
        三维度最优配置 + 全族节省估计
    """
    from lingminopt import ExperimentConfig
    from lingminopt.core.optimizer import MinimalOptimizer
    from lingminopt.meta_optimizer.evaluators import (
        PromptEvaluator,
        RetryEvaluator,
        RoutingEvaluator,
    )
    from lingminopt.meta_optimizer.lingbus_collector import LingBusCollector
    from lingminopt.meta_optimizer.search_spaces import (
        get_prompt_optimization_space,
        get_retry_optimization_space,
        get_routing_optimization_space,
    )

    collector = LingBusCollector()
    records = collector.collect_lingbus_messages(limit=300)
    if not records:
        return {"error": "No LingBus data available"}

    session_data = [
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

    baseline_tokens = sum(d["total_tokens"] for d in session_data)
    results = {}

    for name, space_fn, eval_cls in [
        ("prompt", get_prompt_optimization_space, PromptEvaluator),
        ("routing", get_routing_optimization_space, RoutingEvaluator),
        ("retry", get_retry_optimization_space, RetryEvaluator),
    ]:
        space = space_fn()
        evaluator = eval_cls(session_data)
        cfg = ExperimentConfig(max_experiments=25, direction="maximize")
        opt = MinimalOptimizer(
            evaluate=evaluator.evaluate,
            search_space=space,
            config=cfg,
            search_strategy="bayesian",
        )
        result = opt.run()
        results[name] = {
            "best_score": round(result.best_score, 4),
            "best_params": result.best_params,
        }

    model_mult_map = {
        "glm-5.1": 1.0,
        "glm-5-turbo": 0.75,
        "glm-4.7": 0.85,
        "glm-4.7-flash": 0.6,
        "qwen-max": 0.8,
        "qwen-plus": 0.55,
        "minimax-m2.7": 0.7,
        "llama-3.3-70b": 0.65,
    }
    template_mult_map = {"minimal": 0.7, "standard": 1.0, "detailed": 1.3}
    best_model = results["prompt"]["best_params"].get("model", "glm-5.1")
    best_template = results["prompt"]["best_params"].get("system_prompt_template", "standard")
    mm = model_mult_map.get(best_model, 1.0)
    tm = template_mult_map.get(best_template, 1.0)
    optimized = int(baseline_tokens * mm * tm)
    savings = (1 - optimized / max(baseline_tokens, 1)) * 100

    return {
        "prompt_optimization": results["prompt"],
        "routing_optimization": results["routing"],
        "retry_optimization": results["retry"],
        "savings_estimate": {
            "baseline_tokens": baseline_tokens,
            "optimized_tokens": optimized,
            "savings_percent": round(savings, 1),
            "recommended_model": best_model,
            "recommended_template": best_template,
        },
        "data_points": len(session_data),
        "generated_at": datetime.now().isoformat(),
    }


def main():
    try:
        from lingmessage.registry import register_fastmcp_server

        register_fastmcp_server("lingminopt", "灵极优", mcp, "极简优化")
    except ImportError as e:
        import logging

        logger = logging.getLogger("lingminopt")
        logger.debug(f"lingmessage registry not available: {e}")
    mcp.run()


if __name__ == "__main__":
    main()
