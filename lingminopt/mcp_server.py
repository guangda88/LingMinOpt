"""灵极优 MCP Server — 6个优化工具封装为MCP工具。

工具清单:
  搜索空间: create_search_space
  优化执行: run_optimization, get_optimization_status
  策略管理: create_strategy_profile
  结果管理: load_results, create_experiment_config
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    name="LingMinOpt",
    instructions="灵极优（LingMinOpt）MCP Server — 超参数优化核心能力",
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
    strat = create_strategy(strategy_name, space, seed=seed)
    return {"strategy": strategy_name, "space_params": list(space.sample().keys())}


@mcp.tool(name="load_results", description="加载优化结果（灵果）")
def tool_load_results(filepath: str) -> dict:
    """从JSON文件加载历史优化结果。"""
    from lingminopt import OptimizationResult

    result = OptimizationResult.load(filepath)
    return result.to_dict()


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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
