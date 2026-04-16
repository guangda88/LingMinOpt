# 元知识优化模型实施方案

> **项目**: Meta Knowledge Optimizer (MKO)
> **负责方**: 灵极优 (LingMinOpt)
> **协作方**: 灵克 (LingClaude) + 灵研 (lingresearch)
> **版本**: v1.0.0
> **日期**: 2026-04-12

---

## 一、概述

元知识优化模型（Meta Knowledge Optimizer, MKO）是一个基于灵极优框架的自适应优化系统，用于动态优化灵克的提示词、路由策略、重试策略，提升整体性能和降低成本。

### 1.1 核心价值

- **降低成本**: 通过优化参数减少 API Token 消耗 10-20%
- **提升质量**: 通过数据驱动决策提高任务完成质量 5-15%
- **加速响应**: 通过智能路由减少平均响应时间 15-30%

### 1.2 优化维度

| 优化维度 | 目标 | 搜索空间 | 评估指标 |
|---------|------|----------|----------|
| **提示词优化** | 最小化 Token | 系统提示词长度、温度 | Token 数量 + 任务质量 |
| **路由优化** | 最大化成功率 | Agent 类型、Skill 名称 | 成功率 + 响应时间 |
| **重试优化** | 最小化延迟 | 重试次数、退避时间、降级策略 | 成功率 + 总耗时 |

---

## 二、架构设计

### 2.1 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              LingClaude 会话历史                        │
│         (session_history.json + logs)                    │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│           数据预处理与特征提取                           │
│   - 统计分析 (Token, 成功率, 延迟)                   │
│   - 特征提取 (任务类型, 模型, Agent)                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│            LingMinOpt 优化引擎                          │
│   - 贝叶斯优化 (Hyperopt/Optuna)                      │
│   - 搜索空间定义 (SearchSpace)                         │
│   - 实验管理 (ExperimentConfig)                       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              评估函数 (Evaluator)                      │
│   - 模拟评估 (历史数据回放)                           │
│   - 在线评估 (实时采样测试)                           │
│   - 多目标优化 (Pareto Front)                         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│               优化结果输出                              │
│   - 最优参数配置 (best_params.json)                    │
│   - 性能对比报告 (report.md)                           │
│   - 配置更新建议 (suggestions.json)                    │
└─────────────────────────────────────────────────────────┘
```

### 2.2 优化流程

```python
# 伪代码
def optimization_pipeline():
    # Step 1: 数据收集
    session_data = load_session_history("/path/to/.lingclaude/sessions/")

    # Step 2: 特征提取
    features = extract_features(session_data)

    # Step 3: 定义搜索空间
    search_space = define_search_space()

    # Step 4: 定义评估函数
    def evaluate_config(params):
        # 模拟或在线测试配置效果
        metrics = test_configuration(params, features)
        return composite_score(metrics)

    # Step 5: 运行优化
    optimizer = MinimalOptimizer(
        evaluate=evaluate_config,
        search_space=search_space,
        config=ExperimentConfig(max_experiments=100)
    )
    result = optimizer.run()

    # Step 6: 生成报告
    generate_report(result)

    # Step 7: 应用配置
    apply_configuration(result.best_params)
```

---

## 三、详细设计

### 3.1 提示词优化

**目标**: 在保证任务质量的前提下最小化 Token 消耗

**搜索空间**:
```python
search_space = SearchSpace()
search_space.add_discrete("model", ["gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet"])
search_space.add_continuous("temperature", 0.0, 1.0)
search_space.add_integer("max_tokens", 1024, 8192, step=512)
search_space.add_discrete("system_prompt_template", [
    "minimal",      # 最小化提示
    "standard",     # 标准提示
    "detailed"      # 详细提示
])
```

**评估函数**:
```python
def evaluate_prompt_optimization(params):
    """
    评估提示词配置效果
    """
    # 从历史数据中采样任务
    sample_tasks = sample_tasks_from_history(n=50)

    total_tokens = 0
    total_quality = 0
    success_count = 0

    for task in sample_tasks:
        # 模拟使用当前配置完成任务
        result = simulate_task_execution(task, params)

        total_tokens += result.input_tokens + result.output_tokens
        total_quality += result.quality_score
        if result.success:
            success_count += 1

    # 计算综合分数（加权）
    avg_tokens = total_tokens / len(sample_tasks)
    avg_quality = total_quality / len(sample_tasks)
    success_rate = success_count / len(sample_tasks)

    # 目标：最小化 Token，最大化质量和成功率
    score = (
        0.4 * normalize(avg_tokens, min_val=1000, max_val=5000, reverse=True) +
        0.4 * avg_quality +
        0.2 * success_rate
    )

    return score
```

**输出配置**:
```json
{
  "prompt_optimization": {
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 2048,
    "system_prompt_template": "minimal",
    "expected_improvement": {
      "token_savings_percent": 18.5,
      "quality_impact": -0.02,
      "success_rate_impact": 0.01
    }
  }
}
```

---

### 3.2 路由优化

**目标**: 根据任务类型、复杂度智能路由到最优 Agent/Skill

**搜索空间**:
```python
search_space = SearchSpace()
search_space.add_discrete("code_intent_agent", [
    "implementation",
    "reviewer",
    "architect"
])
search_space.add_discrete("debug_intent_agent", [
    "debugger",
    "tester"
])
search_space.add_discrete("chat_intent_agent", [
    "implementation",
    "documentation"
])
search_space.add_discrete("skill_routing_strategy", [
    "intent_based",      # 基于意图
    "capability_based",   # 基于能力
    "cost_based",         # 基于成本
    "hybrid"              # 混合策略
])
```

**评估函数**:
```python
def evaluate_routing_optimization(params):
    """
    评估路由配置效果
    """
    sample_tasks = sample_tasks_by_intent(n=100)

    total_latency = 0
    total_cost = 0
    success_count = 0

    for task in sample_tasks:
        # 根据配置路由任务
        agent = select_agent(task, params)
        skill = select_skill(task, agent, params)

        # 模拟执行
        result = simulate_task_execution(task, agent, skill)

        total_latency += result.latency_ms
        total_cost += result.api_cost_usd
        if result.success:
            success_count += 1

    avg_latency = total_latency / len(sample_tasks)
    avg_cost = total_cost / len(sample_tasks)
    success_rate = success_count / len(sample_tasks)

    # 目标：最小化延迟和成本，最大化成功率
    score = (
        0.4 * normalize(avg_latency, min_val=500, max_val=5000, reverse=True) +
        0.3 * normalize(avg_cost, min_val=0.01, max_val=0.50, reverse=True) +
        0.3 * success_rate
    )

    return score
```

**输出配置**:
```json
{
  "routing_optimization": {
    "intent_to_agent_map": {
      "code_generation": "implementation",
      "code_refactoring": "implementation",
      "bug_fixing": "debugger",
      "code_review": "reviewer",
      "architecture_design": "architect"
    },
    "skill_routing_strategy": "hybrid",
    "expected_improvement": {
      "latency_reduction_percent": 22.3,
      "cost_reduction_percent": 15.7,
      "success_rate_increase_percent": 3.2
    }
  }
}
```

---

### 3.3 重试优化

**目标**: 优化重试策略，平衡成功率和总耗时

**搜索空间**:
```python
search_space = SearchSpace()
search_space.add_integer("primary_retry_limit", 1, 5, step=1)
search_space.add_continuous("backoff_base", 1.0, 10.0)
search_space.add_continuous("backoff_max", 10.0, 60.0)
search_space.add_integer("degraded_call_threshold", 5, 20, step=5)
search_space.add_continuous("degraded_time_threshold", 30.0, 120.0)
search_space.add_discrete("degradation_strategy", [
    "model_downgrade",     # 模型降级
    "timeout_increase",     # 超时增加
    "hybrid"               # 混合策略
])
```

**评估函数**:
```python
def evaluate_retry_optimization(params):
    """
    评估重试配置效果
    """
    sample_failures = sample_failed_requests(n=100)

    total_time = 0
    final_success_count = 0

    for failure in sample_failures:
        # 模拟使用当前配置的重试过程
        result = simulate_retry_process(failure, params)

        total_time += result.total_time_ms
        if result.final_success:
            final_success_count += 1

    avg_time = total_time / len(sample_failures)
    success_rate = final_success_count / len(sample_failures)

    # 目标：最小化平均耗时，最大化最终成功率
    score = (
        0.5 * normalize(avg_time, min_val=1000, max_val=30000, reverse=True) +
        0.5 * success_rate
    )

    return score
```

**输出配置**:
```json
{
  "retry_optimization": {
    "primary_retry_limit": 3,
    "backoff_base": 5.0,
    "backoff_max": 30.0,
    "degraded_call_threshold": 10,
    "degraded_time_threshold": 60.0,
    "degradation_strategy": "model_downgrade",
    "expected_improvement": {
      "success_rate_increase_percent": 8.5,
      "avg_time_reduction_percent": 12.3
    }
  }
}
```

---

## 四、实现方案

### 4.1 项目结构

```
lingminopt/
├── meta_optimizer/              # 元知识优化模块
│   ├── __init__.py
│   ├── data_collector.py        # 数据收集
│   ├── feature_extractor.py     # 特征提取
│   ├── search_spaces.py        # 搜索空间定义
│   ├── evaluators.py           # 评估函数
│   ├── optimizer.py            # 优化器封装
│   ├── report_generator.py     # 报告生成
│   └── config_applier.py      # 配置应用
├── examples/
│   ├── prompt_optimization.py  # 提示词优化示例
│   ├── routing_optimization.py # 路由优化示例
│   └── retry_optimization.py  # 重试优化示例
└── tests/
    ├── test_data_collector.py
    ├── test_feature_extractor.py
    ├── test_evaluators.py
    └── test_optimizer.py
```

### 4.2 核心代码示例

**data_collector.py**:
```python
"""
数据收集器 - 从 LingClaude 收集会话历史数据
"""
from pathlib import Path
import json
from typing import Any
from dataclasses import dataclass

@dataclass
class SessionRecord:
    session_id: str
    timestamp: float
    query: str
    model: str
    agent: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    success: bool
    quality_score: float | None = None
    api_cost_usd: float | None = None

class DataCollector:
    """从 LingClaude 会话历史收集数据"""

    def __init__(self, session_dir: str):
        self.session_dir = Path(session_dir)

    def collect_sessions(self) -> list[SessionRecord]:
        """收集所有会话数据"""
        records = []

        # 读取 session_history.json
        history_path = self.session_dir / "session_history.json"
        if history_path.exists():
            with open(history_path) as f:
                history = json.load(f)

            for item in history:
                record = SessionRecord(
                    session_id=item.get("session_id", ""),
                    timestamp=item.get("created_at", 0),
                    query=item.get("query", ""),
                    model="",  # 从 session 文件读取
                    agent="",
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=0,
                    success=True
                )
                records.append(record)

        # 读取详细 session 文件
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    session_data = json.load(f)
                # 解析详细数据...
            except Exception:
                continue

        return records

    def sample_tasks(self, n: int = 100) -> list[dict]:
        """采样 n 个任务用于评估"""
        records = self.collect_sessions()
        # 按意图类型分层采样
        # ...

        return sampled_records
```

**search_spaces.py**:
```python
"""
搜索空间定义
"""
from lingminopt import SearchSpace

def get_prompt_optimization_space() -> SearchSpace:
    """提示词优化搜索空间"""
    space = SearchSpace()
    space.add_discrete("model", ["gpt-4o", "gpt-4o-mini", "claude-3.5-sonnet"])
    space.add_continuous("temperature", 0.0, 1.0)
    space.add_integer("max_tokens", 1024, 8192, step=512)
    space.add_discrete("system_prompt_template", ["minimal", "standard", "detailed"])
    return space

def get_routing_optimization_space() -> SearchSpace:
    """路由优化搜索空间"""
    space = SearchSpace()
    space.add_discrete("code_intent_agent", ["implementation", "reviewer", "architect"])
    space.add_discrete("debug_intent_agent", ["debugger", "tester"])
    space.add_discrete("chat_intent_agent", ["implementation", "documentation"])
    space.add_discrete("skill_routing_strategy", ["intent_based", "capability_based", "cost_based", "hybrid"])
    return space

def get_retry_optimization_space() -> SearchSpace:
    """重试优化搜索空间"""
    space = SearchSpace()
    space.add_integer("primary_retry_limit", 1, 5, step=1)
    space.add_continuous("backoff_base", 1.0, 10.0)
    space.add_continuous("backoff_max", 10.0, 60.0)
    space.add_integer("degraded_call_threshold", 5, 20, step=5)
    space.add_continuous("degraded_time_threshold", 30.0, 120.0)
    space.add_discrete("degradation_strategy", ["model_downgrade", "timeout_increase", "hybrid"])
    return space
```

**evaluators.py**:
```python
"""
评估函数
"""
from typing import Any, Callable
from dataclasses import dataclass

@dataclass
class EvaluationMetrics:
    """评估指标"""
    token_savings_percent: float
    quality_score: float
    success_rate: float
    latency_reduction_percent: float
    cost_reduction_percent: float
    composite_score: float

class Evaluator:
    """评估器基类"""

    def __init__(self, session_records: list[dict]):
        self.session_records = session_records

    def evaluate_prompt_config(self, params: dict) -> float:
        """评估提示词配置"""
        total_tokens = 0
        total_quality = 0
        success_count = 0

        for record in self.session_records:
            # 模拟使用当前配置
            simulated = self._simulate_with_config(record, params)

            total_tokens += simulated["total_tokens"]
            total_quality += simulated["quality_score"]
            if simulated["success"]:
                success_count += 1

        n = len(self.session_records)
        avg_tokens = total_tokens / n
        avg_quality = total_quality / n
        success_rate = success_count / n

        # 计算综合分数
        score = self._compute_composite_score(avg_tokens, avg_quality, success_rate)

        return score

    def evaluate_routing_config(self, params: dict) -> float:
        """评估路由配置"""
        total_latency = 0
        total_cost = 0
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
        avg_latency = total_latency / n
        avg_cost = total_cost / n
        success_rate = success_count / n

        score = self._compute_routing_score(avg_latency, avg_cost, success_rate)
        return score

    def evaluate_retry_config(self, params: dict) -> float:
        """评估重试配置"""
        # 类似实现...
        pass

    def _compute_composite_score(self, tokens: float, quality: float, success_rate: float) -> float:
        """计算综合分数"""
        normalized_tokens = self._normalize(tokens, 1000, 5000, reverse=True)
        return 0.4 * normalized_tokens + 0.4 * quality + 0.2 * success_rate

    def _normalize(self, value: float, min_val: float, max_val: float, reverse: bool = False) -> float:
        """归一化到 [0, 1]"""
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0, min(1, normalized))
        if reverse:
            normalized = 1 - normalized
        return normalized
```

**optimizer.py**:
```python
"""
优化器封装
"""
from lingminopt import MinimalOptimizer, ExperimentConfig
from .search_spaces import (
    get_prompt_optimization_space,
    get_routing_optimization_space,
    get_retry_optimization_space
)
from .evaluators import Evaluator
from .data_collector import DataCollector

class MetaOptimizer:
    """元知识优化器"""

    def __init__(self, session_dir: str):
        self.session_dir = session_dir
        self.collector = DataCollector(session_dir)

    def optimize_prompt(self, max_experiments: int = 100) -> dict:
        """优化提示词配置"""
        # 收集数据
        records = self.collector.collect_sessions()

        # 定义搜索空间
        search_space = get_prompt_optimization_space()

        # 定义评估函数
        evaluator = Evaluator(records)
        def evaluate(params):
            return evaluator.evaluate_prompt_config(params)

        # 配置优化器
        config = ExperimentConfig(
            max_experiments=max_experiments,
            time_budget=600,  # 10分钟
            direction="maximize"
        )

        # 运行优化
        optimizer = MinimalOptimizer(
            evaluate=evaluate,
            search_space=search_space,
            config=config,
            search_strategy="bayesian"
        )

        result = optimizer.run()

        return {
            "best_params": result.best_params,
            "best_score": result.best_score,
            "history": result.history
        }

    def optimize_routing(self, max_experiments: int = 100) -> dict:
        """优化路由配置"""
        records = self.collector.collect_sessions()
        search_space = get_routing_optimization_space()
        evaluator = Evaluator(records)

        def evaluate(params):
            return evaluator.evaluate_routing_config(params)

        config = ExperimentConfig(
            max_experiments=max_experiments,
            time_budget=600,
            direction="maximize"
        )

        optimizer = MinimalOptimizer(
            evaluate=evaluate,
            search_space=search_space,
            config=config,
            search_strategy="bayesian"
        )

        result = optimizer.run()

        return {
            "best_params": result.best_params,
            "best_score": result.best_score,
            "history": result.history
        }

    def optimize_retry(self, max_experiments: int = 100) -> dict:
        """优化重试配置"""
        # 类似实现...
        pass
```

---

## 五、集成方案

### 5.1 与 LingClaude 集成

**1. 配置更新接口**:
```python
# LingClaude/lingclaude/core/config.py
from lingminopt.meta_optimizer import MetaOptimizer

class LingClaudeConfig:
    """灵克配置"""

    def __init__(self):
        # ... 现有配置 ...

        # 元知识优化配置
        self.enable_meta_optimization = True
        self.meta_optimization_config_path = ".lingclaude/meta_optimization.json"

    def load_meta_optimization_config(self) -> dict:
        """加载元知识优化配置"""
        if not self.enable_meta_optimization:
            return {}

        config_path = Path.home() / ".lingclaude" / "meta_optimization.json"
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}

    def apply_meta_optimization(self) -> None:
        """应用元知识优化配置"""
        config = self.load_meta_optimization_config()

        # 应用提示词优化
        if "prompt_optimization" in config:
            prompt_cfg = config["prompt_optimization"]
            self.model = prompt_cfg["model"]
            self.temperature = prompt_cfg["temperature"]
            self.max_tokens = prompt_cfg["max_tokens"]

        # 应用路由优化
        if "routing_optimization" in config:
            routing_cfg = config["routing_optimization"]
            self.agent_routing_map = routing_cfg["intent_to_agent_map"]

        # 应用重试优化
        if "retry_optimization" in config:
            retry_cfg = config["retry_optimization"]
            # 更新 GlmRetryPolicy 参数...
```

**2. 定期优化触发**:
```python
# LingClaude/lingclaude/self_optimizer/daemon.py
from lingminopt.meta_optimizer import MetaOptimizer

class OptimizationDaemon:
    """优化守护进程"""

    def __init__(self):
        self.session_dir = Path.home() / ".lingclaude" / "sessions"
        self.meta_optimizer = MetaOptimizer(str(self.session_dir))

    def run_optimization_cycle(self) -> None:
        """运行优化周期"""
        logger.info("开始元知识优化周期...")

        # 提示词优化
        prompt_result = self.meta_optimizer.optimize_prompt(max_experiments=50)
        logger.info(f"提示词优化完成: {prompt_result['best_params']}")

        # 路由优化
        routing_result = self.meta_optimizer.optimize_routing(max_experiments=50)
        logger.info(f"路由优化完成: {routing_result['best_params']}")

        # 重试优化
        retry_result = self.meta_optimizer.optimize_retry(max_experiments=50)
        logger.info(f"重试优化完成: {retry_result['best_params']}")

        # 合并配置
        merged_config = {
            "prompt_optimization": prompt_result["best_params"],
            "routing_optimization": routing_result["best_params"],
            "retry_optimization": retry_result["best_params"]
        }

        # 保存配置
        config_path = Path.home() / ".lingclaude" / "meta_optimization.json"
        with open(config_path, "w") as f:
            json.dump(merged_config, f, indent=2)

        logger.info("元知识优化周期完成")
```

### 5.2 CLI 接口

```bash
# 手动触发优化
lingminopt meta-optimize --target prompt --max-experiments 100
lingminopt meta-optimize --target routing --max-experiments 100
lingminopt meta-optimize --target retry --max-experiments 100

# 批量优化
lingminopt meta-optimize --all --max-experiments 50

# 查看优化结果
lingminopt meta-optimize --report

# 应用优化配置
lingminopt meta-optimize --apply
```

---

## 六、测试方案

### 6.1 单元测试

```python
# tests/test_evaluator.py
import pytest

def test_prompt_optimization_evaluator():
    records = load_sample_records(n=10)
    evaluator = Evaluator(records)

    params = {
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 2048
    }

    score = evaluator.evaluate_prompt_config(params)
    assert 0 <= score <= 1

def test_routing_optimization_evaluator():
    records = load_sample_records(n=10)
    evaluator = Evaluator(records)

    params = {
        "code_intent_agent": "implementation",
        "skill_routing_strategy": "intent_based"
    }

    score = evaluator.evaluate_routing_config(params)
    assert 0 <= score <= 1
```

### 6.2 集成测试

```python
# tests/test_meta_optimizer.py
import pytest
from lingminopt.meta_optimizer import MetaOptimizer

def test_end_to_end_prompt_optimization():
    optimizer = MetaOptimizer(session_dir="tests/fixtures/sessions")

    result = optimizer.optimize_prompt(max_experiments=10)

    assert "best_params" in result
    assert "best_score" in result
    assert len(result["history"]) <= 10

def test_end_to_end_routing_optimization():
    optimizer = MetaOptimizer(session_dir="tests/fixtures/sessions")

    result = optimizer.optimize_routing(max_experiments=10)

    assert "best_params" in result
    assert "intent_to_agent_map" in result["best_params"]
```

---

## 七、部署方案

### 7.1 开发环境

```bash
# 安装依赖
pip install -e lingminopt
pip install -e LingClaude

# 运行优化
python -m lingminopt.cli meta-optimize --all
```

### 7.2 生产环境

```bash
# 启用定期优化
systemctl enable lingclaude-optimizer.service
systemctl start lingclaude-optimizer.service

# 查看优化状态
lingminopt meta-optimize --status
```

### 7.3 监控

```python
# 监控优化效果
def monitor_optimization():
    optimizer = MetaOptimizer(session_dir="/path/to/sessions")

    # 收集优化前后的指标
    before_metrics = collect_current_metrics()
    optimizer.run_optimization_cycle()
    after_metrics = collect_current_metrics()

    # 计算改进
    improvements = {
        "token_savings": (before_metrics["avg_tokens"] - after_metrics["avg_tokens"]) / before_metrics["avg_tokens"],
        "quality_improvement": after_metrics["avg_quality"] - before_metrics["avg_quality"],
        "success_rate_improvement": after_metrics["success_rate"] - before_metrics["success_rate"]
    }

    # 发送报告
    send_optimization_report(improvements)
```

---

## 八、成功指标

### 8.1 性能指标

- **Token 节省率**: > 15%
- **API 成本降低**: > 20%
- **平均响应时间降低**: > 25%
- **任务成功率提升**: > 5%

### 8.2 质量指标

- **优化收敛速度**: < 50 次实验
- **配置稳定性**: 连续 3 次优化参数变化 < 5%
- **覆盖率**: 优化覆盖 > 80% 的任务类型

### 8.3 可靠性指标

- **优化成功率**: > 95%
- **配置应用成功率**: > 99%
- **平均优化时间**: < 10 分钟

---

## 九、后续优化

1. **多目标优化**: 使用 Pareto Front 找到非劣解
2. **在线学习**: 实时更新优化策略
3. **联邦优化**: 多节点协同优化
4. **A/B 测试**: 自动化 A/B 测试框架
5. **异常检测**: 自动识别异常性能模式

---

**文档版本**: v1.0.0
**最后更新**: 2026-04-12
**下次审查**: 2026-04-19
