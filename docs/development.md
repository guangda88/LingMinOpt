# LingMinOpt Development Guide

> 从 AGENTS.md 迁出，2026-05-06 瘦身。

## Core Concepts

### Optimization Flow

1. **Define Search Space**: Specify parameters to optimize (discrete choices or continuous ranges)
2. **Define Evaluator**: Function that takes parameters and returns a score
3. **Configure Experiment**: Set max experiments, time budget, direction (minimize/maximize)
4. **Run Optimizer**: Framework samples parameters, evaluates, tracks best results
5. **Analyze Results**: Review best parameters and optimization history

### Key Classes

- **`MinimalOptimizer`**: Main optimization engine
- **`SearchSpace`**: Parameter bounds and types. `add_discrete()` / `add_continuous()`
- **`ExperimentConfig`**: Optimization configuration (from `lingminopt.config.config`)
- **`OptimizationResult`**: Best score, params, history, statistics (from `lingminopt.core.models`)
- **`SearchStrategy`**: Base class (Random, Grid, Bayesian, Simulated Annealing)

### Search Strategies

| Strategy | Use Case | Notes |
|----------|----------|-------|
| `random` | Quick exploration | Pure random sampling |
| `grid` | Small spaces | Exhaustive (5 pts/continuous) |
| `bayesian` | Medium spaces | 30% exploration |
| `annealing` | Avoid local optima | Temperature-based perturbation |

## Code Patterns

### Style
- **Line length**: 100 chars (pyproject.toml)
- **Formatting**: `black` + `isort`
- **Type hints**: `typing` module; mypy in dev deps
- **Docstrings**: Google-style

### Naming
- Classes: PascalCase | Functions/vars: snake_case | Constants: UPPER_SNAKE_CASE | Private: `_` prefix

### Data Models
`@dataclass` with `to_dict()` / `from_dict()` for serialization.

### Base Classes
ABC for extensible components (`EvaluatorBase`, `SearchStrategy`).

### Factory Pattern
`create_strategy()` in `core/strategy.py`.

## Adding Features

### New Search Strategy
1. Inherit `SearchStrategy` in `core/strategy.py`
2. Implement `suggest_next(history) -> Dict[str, Any]`
3. Add to factory dict + CLI choices (`cli/commands.py:41`)

### New Evaluator
1. Inherit `EvaluatorBase` in `core/evaluator.py`
2. Implement `evaluate(params) -> float`
3. Optional: `setup()`, `cleanup()`

### New Template
1. Add to CLI choices
2. Add template functions (`_get_fixed_template`, etc.)
3. Example in `examples/<name>/`

## Important Gotchas

- **Two ExperimentConfig**: Prefer `lingminopt/config/config.py` (better validation + `is_better()`)
- **CLI import bug**: Templates reference `minopt`, use `lingminopt`
- **Silent exceptions**: `optimizer.py:66` catches and continues (intentional)
- **Random seed**: `SearchSpace.sample()` uses internal `random.Random()`, set via `ExperimentConfig.random_seed`
- **CLI project files**: `fixed.py` (don't edit), `variable.py` (edit this), `config.json`
- **Dynamic loading**: CLI loads `variable.py` with `UserWarning`

## Security

- Project names: reject `..`, `/`, `\`
- Config: validate `results_file` paths + `direction` values
- SearchSpace: discrete needs choices, continuous needs min < max
- CLI: dynamic code loading triggers warnings

## Testing

```bash
pytest tests/                      # Run tests
pytest --cov=lingminopt tests/     # With coverage
```

Test structure: classes with pytest, `tmp_path` for file ops.

## Dependencies

Core: `numpy>=1.20.0`, `click>=8.0`
Dev: `pytest>=7.0`, `black>=22.0`, `isort>=5.0`, `mypy>=0.950`
Optional: `matplotlib>=3.5.0`, `seaborn>=0.12.0`, `scipy>=1.7.0`

Python 3.8-3.12 (avoid `|` union operator before 3.10).

## Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

```python
from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
space = SearchSpace()
space.add_continuous("x", 0, 10)
config = ExperimentConfig(max_experiments=5, time_budget=10.0)
result = MinimalOptimizer(lambda p: p["x"]**2, space, config, seed=42).run()
```
