"""灵极优 MCP Server — 优化工具 + 反馈闭环。

工具清单 (11):
  搜索空间: create_search_space
  优化执行: run_optimization, get_optimization_status
  策略管理: create_strategy_profile
  结果管理: load_results, compare_results, create_experiment_config
  反馈闭环: feedback_from_result, export_training_sample, list_feedback
  一键闭环: optimization_pipeline
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP

_FEEDBACK_DIR = Path("data/feedback")
_TRAINING_EXPORT_DIR = Path("data/training_exports")

mcp = FastMCP(
    name="LingMinOpt",
    instructions="灵极优（LingMinOpt）MCP Server — 超参数优化核心能力 + 反馈闭环",
)


@mcp.tool(name="create_search_space", description="创建搜索空间（灵空）")
def tool_create_search_space(config_json: str) -> dict:
    """从JSON配置创建搜索空间。config_json 格式: {"discrete": {"name": [choices]}, "continuous": {"name": [min, max]}}。"""
    from lingminopt import SearchSpace

    config = json.loads(config_json)
    space = SearchSpace.from_dict(config)
    sample = space.sample()
    return {"status": "created", "sample_params": sample}


@mcp.tool(name="run_optimization", description="运行优化（灵优）")
def tool_run_optimization(
    search_space_config: str,
    evaluate_code: str,
    max_experiments: int = 100,
    strategy: str = "random",
    direction: str = "minimize",
    time_budget: float = 300.0,
) -> dict:
    """运行一次优化任务。evaluate_code 为 Python 函数体，接收 params dict，返回 float 分数。"""
    from lingminopt import ExperimentConfig, MinimalOptimizer, SearchSpace

    space = SearchSpace.from_dict(json.loads(search_space_config))
    config = ExperimentConfig(
        max_experiments=max_experiments,
        direction=direction,
        time_budget=time_budget,
    )
    local_vars: dict[str, Any] = {}
    exec(f"def _evaluate(params):\n    {evaluate_code}", local_vars)
    optimizer = MinimalOptimizer(
        evaluate=local_vars["_evaluate"],
        search_space=space,
        config=config,
        search_strategy=strategy,
    )
    result = optimizer.run()
    return result.to_dict()


@mcp.tool(name="get_optimization_status", description="优化状态（灵态）")
def tool_get_optimization_status() -> dict:
    """返回当前优化运行状态（需要有正在运行的优化实例）。"""
    return {"status": "no_active_run", "message": "灵极优无活跃优化任务，请先调用 run_optimization"}


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


@mcp.tool(name="load_results", description="加载优化结果（灵果）")
def tool_load_results(filepath: str) -> dict:
    """从JSON文件加载历史优化结果。"""
    from lingminopt import OptimizationResult

    result = OptimizationResult.load(filepath)
    return result.to_dict()


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

    ra = OptimizationResult.load(filepath_a)
    rb = OptimizationResult.load(filepath_b)

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

    result = OptimizationResult.load(result_filepath)

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

    result = OptimizationResult.load(result_filepath)
    history = result.history

    if not history:
        return {"error": "No experiments in result history"}

    samples: List[Dict[str, Any]] = []

    if sample_type == "best_only":
        best_exp = min(history, key=lambda e: e.score)
        samples.append(_exp_to_training(best_exp, result, include_metadata))

    elif sample_type == "top_k":
        sorted_hist = sorted(history, key=lambda e: e.score)
        k = max(1, len(sorted_hist) // 10)
        for exp in sorted_hist[:k]:
            samples.append(_exp_to_training(exp, result, include_metadata))

    elif sample_type == "all":
        for exp in history:
            samples.append(_exp_to_training(exp, result, include_metadata))

    elif sample_type == "trajectory":
        for i, exp in enumerate(history):
            entry = _exp_to_training(exp, result, include_metadata)
            entry["step"] = i
            entry["is_best_so_far"] = exp.score == min(
                e.score for e in history[: i + 1]
            )
            samples.append(entry)
    else:
        return {"error": f"Invalid sample_type: {sample_type}"}

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


def _exp_to_training(
    exp: Any, result: Any, include_metadata: bool
) -> Dict[str, Any]:
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


@mcp.tool(name="optimization_pipeline", description="优化闭环流水线（灵环）")
def tool_optimization_pipeline(
    search_space_config: str,
    evaluate_code: str,
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
        evaluate_code: Python 函数体（接收 params，返回 float）
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
    local_vars: dict[str, Any] = {}
    exec(f"def _evaluate(params):\n    {evaluate_code}", local_vars)
    optimizer = MinimalOptimizer(
        evaluate=local_vars["_evaluate"],
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
