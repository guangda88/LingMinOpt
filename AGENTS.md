# LingMinOpt Agent Guide

This guide helps AI agents work effectively with the LingMinOpt codebase.

## Project Overview

**LingMinOpt** (灵极优) is a minimalist self-optimization framework for automated hyperparameter tuning and optimization. It provides:

- **Simple API**: 5-line code to start optimizing
- **Multiple search strategies**: Random, Grid, Bayesian, Simulated Annealing
- **CLI interface**: Initialize projects and run optimization from command line
- **Extensible architecture**: Custom evaluators and search strategies
- **Template system**: Pre-built templates for ML, database, game, and algorithm optimization

## Essential Commands

### Installation & Setup
```bash
pip install -e .[dev]              # Install with dev dependencies
pip install -e .[visualization]    # Install with visualization deps
pip install -e .[bayesian]        # Install with Bayesian optimization deps
```

### Development
```bash
pytest tests/                      # Run tests
pytest --cov=lingminopt tests/     # Run tests with coverage
black .                            # Format code
isort .                            # Sort imports
mypy lingminopt/                   # Type checking
```

### CLI Usage
```bash
lingminopt init my-project --template ml-optimization    # Initialize project
lingminopt run --config config.json                      # Run optimization
lingminopt report --results results.json                # Generate report
```

### Package Installation
```bash
pip install lingminopt             # Install from PyPI (when published)
```

## Project Structure

```
lingminopt/
├── lingminopt/                   # Main package
│   ├── __init__.py              # Package exports (all public API)
│   ├── core/                     # Core optimization engine
│   │   ├── optimizer.py         # MinimalOptimizer
│   │   ├── searcher.py          # SearchSpace, ParameterConfig
│   │   ├── evaluator.py         # EvaluatorBase, FunctionEvaluator, TimedEvaluator
│   │   ├── strategy.py          # SearchStrategy implementations
│   │   ├── models.py            # Data models (Experiment, OptimizationResult)
│   │   └── __init__.py         # Core exports (MinimalOptimizer, SearchSpace, etc.)
│   ├── config/                   # Configuration
│   │   ├── config.py            # ExperimentConfig (validation logic)
│   │   └── __init__.py
│   ├── utils/                    # Utilities
│   │   └── logger.py            # Logging setup
│   ├── cli/                      # Command-line interface
│   │   ├── commands.py          # Click commands (init, run, report)
│   │   └── __init__.py
│   ├── tests/                    # Tests
│   │   └── test_core.py         # Core tests (26 tests, all passing)
│   └── examples/                 # Example scripts
│       ├── example1_quadratic.py
│       └── example2_ml_tuning.py
├── examples/                     # Additional examples
│   ├── ml-optimization/
│   ├── database-optimization/
│   ├── game-optimization/
│   └── ...
├── pyproject.toml                # Modern Python project config
├── CHANGELOG.md                  # Version history (see v0.2.0)
└── README.md
```

### Important Notes (v0.2.0)

**Single Source of Truth**:
- `ExperimentConfig` from `lingminopt.config.config` (with validation)
- `OptimizationResult` from `lingminopt.core.models` (with serialization)
- `Experiment` from `lingminopt.core.models`

**Package Exports**:
- Import from `lingminopt` for public API
- Import from `lingminopt.core`, `lingminopt.config` for internal use
- `__init__.py` exports all necessary classes

## Core Concepts

### Optimization Flow

1. **Define Search Space**: Specify parameters to optimize (discrete choices or continuous ranges)
2. **Define Evaluator**: Function that takes parameters and returns a score
3. **Configure Experiment**: Set max experiments, time budget, direction (minimize/maximize)
4. **Run Optimizer**: Framework samples parameters, evaluates, tracks best results
5. **Analyze Results**: Review best parameters and optimization history

### Key Classes

- **`MinimalOptimizer`**: Main optimization engine. Uses search strategies to explore parameter space.
- **`SearchSpace`**: Defines parameter bounds and types. Supports `add_discrete()` and `add_continuous()`.
- **`ExperimentConfig`**: Configuration for optimization (max experiments, time budget, direction, etc.)
- **`OptimizationResult`**: Contains best score, best params, full history, and statistics.
- **`SearchStrategy`**: Base class for search strategies (Random, Grid, Bayesian, Simulated Annealing).

### Search Strategies

| Strategy | Use Case | Notes |
|----------|----------|-------|
| `random` | Quick exploration | Pure random sampling |
| `grid` | Small spaces | Exhaustive search (5 points per continuous) |
| `bayesian` | Medium spaces | Explores around best params with 30% exploration |
| `annealing` | Avoid local optima | Temperature-based perturbation |

## Code Patterns & Conventions

### Style

- **Line length**: 100 characters (configured in pyproject.toml)
- **Formatting**: Use `black` and `isort` before committing
- **Type hints**: Use `typing` module; mypy enabled in dev dependencies
- **Docstrings**: Use Google-style or standard Python docstrings

### Naming

- **Classes**: PascalCase (`MinimalOptimizer`, `SearchSpace`)
- **Functions/variables**: snake_case (`add_discrete`, `max_experiments`)
- **Constants**: UPPER_SNAKE_CASE (`TIME_BUDGET`, `MAX_EXPERIMENTS`)
- **Private members**: Prefixed with underscore (`_rng`, `_generate_grid`)

### Data Models

Use `@dataclass` for data models with `to_dict()` and `from_dict()` methods for serialization:

```python
@dataclass
class Experiment:
    experiment_id: int
    params: Dict[str, Any]
    score: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {...}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Experiment":
        return cls(...)
```

### Base Classes

Use ABC for extensible components:

```python
class EvaluatorBase(ABC):
    @abstractmethod
    def evaluate(self, params: Dict[str, Any]) -> float:
        pass
```

### Factory Pattern

Use factory functions for strategy creation:

```python
def create_strategy(strategy_name: str, search_space: SearchSpace, **kwargs):
    strategies = {
        "random": RandomSearch,
        "grid": GridSearch,
        # ...
    }
    return strategies[strategy_name](search_space, **kwargs)
```

## Testing Patterns

### Test Structure

Tests are organized as classes using pytest:

```python
class TestSearchSpace:
    def test_add_discrete(self):
        space = SearchSpace()
        space.add_discrete("model", ["small", "medium"])
        assert "model" in space

    def test_invalid_continuous(self):
        space = SearchSpace()
        with pytest.raises(ValueError):
            space.add_continuous("param", 1.0, 0.5)  # min > max
```

### Fixtures

Use `tmp_path` for file operations:

```python
def test_save_load(self, tmp_path):
    result.save(tmp_path / "result.json")
    loaded = OptimizationResult.load(tmp_path / "result.json")
```

## Important Gotchas

### Duplicate ExperimentConfig

There are two `ExperimentConfig` classes:
- `lingminopt/core/optimizer.py:8` - Simple dataclass with basic validation
- `lingminopt/config/config.py:10` - More complete with `is_better()` method

**Prefer** the one in `config/config.py` as it has better validation and utility methods.

### Import Inconsistencies

CLI templates reference `minopt` instead of `lingminopt` (lines 251, 290 in cli/commands.py). This is a historical artifact; use `lingminopt` in actual code.

### Exception Handling

In `optimizer.py:66`, exceptions during evaluation are silently caught and ignored:

```python
try:
    score = self.evaluate(params)
except Exception as e:
    continue  # Silently skips failed experiments
```

This is intentional (robustness), but may hide errors during debugging.

### Search Space Sampling

`SearchSpace.sample()` uses internal `random.Random()` instance, not the global `random`. Set seed via `ExperimentConfig.random_seed` for reproducibility.

### Results History

**Note (v0.2.0+)**: Use `OptimizationResult` from `lingminopt.core.models` which uses typed `Experiment` objects with proper serialization. Duplicate classes have been removed from `optimizer.py`.

### CLI Project Structure

When using `lingminopt init`, the CLI creates:
- `fixed.py` - Environment constraints (DO NOT MODIFY)
- `variable.py` - Parameters to optimize (EDIT THIS)
- `config.json` - Configuration file
- `README.md` - Project documentation

The CLI loads `variable.py` dynamically at runtime with a warning:
```
UserWarning: Loading user code from variable.py. Only run code from trusted sources.
```

### Security Considerations

**Input Validation** (v0.2.0+):
- Project names validated to prevent path traversal (rejects `..`, `/`, `\`)
- Config files validate `results_file` paths and `direction` values
- SearchSpace validates parameters (discrete needs choices, continuous needs min < max)

**CLI Security**:
- Dynamic code loading triggers warnings
- Project creation prevents directory traversal
- Config validation ensures safe file paths

**Best Practices for Contributors**:
- Always validate user inputs at entry points
- Use provided validation functions in `cli/commands.py`
- Document security-critical code
- Test with malicious inputs (e.g., `../../../tmp`)

## Adding Features

### New Search Strategy

1. Inherit from `SearchStrategy` in `core/strategy.py`
2. Implement `suggest_next(history: List[Experiment]) -> Dict[str, Any]`
3. Add to factory `strategies` dict in `create_strategy()`
4. Add to CLI option choices in `cli/commands.py:41`

### New Evaluator

1. Inherit from `EvaluatorBase` in `core/evaluator.py`
2. Implement `evaluate(self, params: Dict[str, Any]) -> float`
3. Optionally implement `setup()` and `cleanup()` for resource management

### New Template

1. Add template name to CLI choices in `cli/commands.py:41`
2. Add `_get_fixed_template()`, `_get_variable_template()`, `_get_readme_template()` functions
3. Create example in `examples/<template-name>/`

## Common Tasks

### Add a New Parameter Type

Modify `ParameterConfig` and `SearchSpace` in `core/searcher.py`:
- Add new `param_type` value
- Implement sampling logic in `SearchSpace.sample()`
- Add `add_<type>()` helper method

### Improve Test Coverage

- Test edge cases (empty values, invalid inputs, boundaries)
- Test serialization/deserialization for data models
- Test each search strategy independently
- Mock slow evaluators to test timeout handling

### Fix Type Errors

Run `mypy lingminopt/` and address:
- Missing type hints in function signatures
- Incorrect return types
- Union types where needed (e.g., `Optional[int]`)

## Dependencies

### Core Dependencies
- `numpy>=1.20.0` - Numerical operations
- `click>=8.0` - CLI framework

### Optional Dependencies
- `pytest>=7.0`, `pytest-cov>=3.0` - Testing
- `black>=22.0`, `isort>=5.0` - Code formatting
- `mypy>=0.950` - Type checking
- `matplotlib>=3.5.0`, `seaborn>=0.12.0` - Visualization
- `scipy>=1.7.0` - Bayesian optimization (advanced)

## File Patterns

### Configuration Files
- `pyproject.toml` - Modern Python project config (preferred)
- `setup.py` - Fallback for older pip versions
- `config.json` - CLI project configuration

### Result Files
- `results.json` - Default optimization results
- `lingresearch_results_*.json` - Experiment results (ignored by git)

## Python Version Support

Supports Python 3.8-3.12. Use type hints compatible with 3.8 (avoid newer syntax like `|` union operator before 3.10).

## Debugging Tips

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Single Optimization
```python
from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig

space = SearchSpace()
space.add_continuous("x", 0, 10)

config = ExperimentConfig(max_experiments=5, time_budget=10.0)

def objective(params):
    return params["x"] ** 2

optimizer = MinimalOptimizer(objective, space, config, seed=42)
result = optimizer.run()
```

### Profile Evaluation Time
Use `TimedEvaluator` wrapper to track experiment duration:
```python
from lingminopt.core.evaluator import TimedEvaluator

timed_evaluator = TimedEvaluator(
    FunctionEvaluator(your_evaluator),
    time_budget=300.0
)
```

## Related Documentation

- `README.md` - User guide and quick start
- `examples/` - Working examples for different scenarios
- Inline docstrings - API documentation for each class/function

## 灵信收件箱

灵极优已接入灵信系统。使用CLI查看消息和回复：

```bash
lingminopt inbox                                    # 查看收件箱
lingminopt inbox --agent lingjiyou                  # 指定agent身份
lingminopt inbox --reply 328 --message '收到，开始执行'  # 回复线程
```

环境变量: `LINGMESSAGE_DB_URL` (默认连接zhineng知识库的lingmessage表)

---

## ⚡ 当前待办任务 (来自灵知 2026-04-08, 更新 2026-04-09)

**灵信线程 #328 — MCP封装进度更新**

### P0 进度 (5/7 完成 ✅, 1 部分完成 ⚠️, 1 未开始 ❌)

| # | P0 项 | 状态 | MCP工具名 |
|---|-------|------|-----------|
| 1 | 知识检索 (search+ask) | ✅ 完成 | `knowledge_search`, `ask_question` |
| 2 | 训练数据生成 | ✅ 完成 | `generate_training_data` |
| 3 | 自优化引擎 | ⚠️ 部分 | `optimization_status`, `submit_feedback` (只读+反馈，无执行触发) |
| 4 | 文件读写沙箱 | ❌ 未开始 | 需要新建 (低可行性=6) |
| 5 | 数据库查询 | ✅ 完成 | `safe_db_query` (白名单表) |
| 6 | 领域路由查询 | ✅ 完成 | `domain_query` |
| 7 | 命令执行白名单 | ❌ 未开始 | 需要新建 (最低可行性=5) |

### 剩余任务

**任务1: 完善自优化引擎 MCP**
- 当前只有 `optimization_status` (只读) 和 `submit_feedback` (提交)
- 需要添加: 触发优化执行的工具、优化结果查询

**任务2: 评估是否需要文件沙箱和命令执行**
- 这两项可行性评分最低 (6/5)，可能不需要自建
- 现有 Crush 工具已覆盖 view/write/edit/bash

**任务3: 反馈闭环优化**
- 对接 `data/training/` 训练数据流水线
- 建立优化→反馈→数据生成的闭环

### 可用资源
- MCP Server: `/home/ai/zhineng-knowledge-system/mcp_servers/zhineng_server.py` (474行, commit `3e70347`)
- 训练数据: `/home/ai/zhineng-knowledge-system/data/training/` (16K条)
- MCP报告: `/home/ai/zhineng-knowledge-system/docs/reports/MCP_ENCAPSULATION_ASSESSMENT.md`
- 灵信线程: #328

## License

MIT License - See LICENSE file for details.
