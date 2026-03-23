# LingMinOpt (灵极优)

**LingMinOpt** - 灵研极简自优化框架

A universal minimalist self-optimization framework inspired by 灵研 (LingResearch) and autoresearch.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 核心理念

**极简主义 + 自动化 + 数据驱动 = 强大的优化能力**

给 AI 一个真实的环境，让它自主实验。修改代码、运行几分钟、检查结果是否改进、保留或丢弃更改，然后重复。

**核心公式**：
```
最优配置 = 搜索空间探索 + 快速反馈 + 数据驱动决策 + 极简主义
```

## ✨ 特性

- **极简**：5 行代码开始
- **通用**：适用于机器学习、数据库、游戏等多种场景
- **可扩展**：插件系统和中间件
- **易用**：CLI 工具和项目模板
- **高效**：多种搜索策略
- **数据驱动**：基于结果做决策，而非直觉

## 🚀 快速开始

### 安装

```bash
pip install lingminopt
```

### 5 行代码优化

```python
from lingminopt import MinimalOptimizer, SearchSpace

# 定义要优化的内容
search_space = SearchSpace()
search_space.add_continuous("x", -10, 10)
search_space.add_continuous("y", -10, 10)

# 定义评估函数
def evaluate(params):
    return params["x"]**2 + params["y"]**2  # 最小化

# 运行优化
optimizer = MinimalOptimizer(evaluate, search_space)
result = optimizer.run()

print(f"最佳分数: {result.best_score}")  # 应该接近 0
print(f"最佳参数: {result.best_params}")  # 应该接近 {x: 0, y: 0}
```

### 使用模板

```bash
# 初始化新项目
lingminopt init my-ml-project --template ml-optimization

# 编辑 variable.py 定义实验
vim my-ml-project/variable.py

# 运行优化
cd my-ml-project
lingminopt run

# 查看结果
lingminopt report
```

## 📖 使用方法

### API 使用

#### 简单函数

```python
from lingminopt import MinimalOptimizer, SearchSpace

def objective(params):
    """要最小化的目标函数"""
    x = params["x"]
    y = params["y"]
    return (x - 2)**2 + (y + 3)**2

search_space = SearchSpace()
search_space.add_continuous("x", -10, 10)
search_space.add_continuous("y", -10, 10)

optimizer = MinimalOptimizer(objective, search_space)
result = optimizer.run()
```

#### 带配置

```python
from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig

search_space = SearchSpace()
search_space.add_continuous("learning_rate", 1e-5, 1e-2)
search_space.add_discrete("optimizer", ["adam", "adamw", "sgd"])

config = ExperimentConfig(
    max_experiments=100,
    improvement_threshold=0.001,
    time_budget=300,  # 每次实验 5 分钟
    search_strategy="bayesian"
)

optimizer = MinimalOptimizer(
    evaluate=train_and_evaluate,
    search_space=search_space,
    config=config
)
result = optimizer.run()
```

### CLI 使用

```bash
# 初始化项目
lingminopt init my-project --template ml-optimization

# 运行优化
lingminopt run --config config.json --max-experiments 50

# 生成报告
lingminopt report --results results.json
```

## 🔧 搜索策略

LingMinOpt 包含多种搜索策略：

| 策略 | 描述 | 适用场景 |
|------|------|----------|
| `random` | 随机采样 | 快速探索 |
| `grid` | 网格搜索 | 小搜索空间 |
| `bayesian` | 利用/探索平衡 | 中等搜索空间 |
| `annealing` | 模拟退火 | 避免局部最优 |

```python
# 使用不同策略
optimizer = MinimalOptimizer(
    evaluate=func,
    search_space=space,
    search_strategy="bayesian"  # random, grid, bayesian, annealing
)
```

## 📚 应用场景

LingMinOpt 适用于任何具有以下特征的优化问题：

1. ✅ 可量化指标（清晰的数值评估）
2. ✅ 快速反馈（几分钟/几小时内得到结果）
3. ✅ 大搜索空间（手动探索参数组合太多）
4. ✅ 可自动化（可以脚本化）
5. ✅ 清晰约束（预算、时间、资源）

### 机器学习

```python
def train_and_evaluate(params):
    model = build_model(params)  # model_type, layers, activation
    history = train(model, params)  # lr, optimizer, batch_size
    metrics = evaluate(model, val_data)
    return metrics["val_loss"]  # 最小化
```

### 数据库优化

```python
def benchmark_config(params):
    apply_db_config(params)  # index_type, cache_size, pool_size
    results = run_benchmark()
    return results["qps"]  # 最大化（设置 direction="maximize"）
```

### 游戏策略

```python
def evaluate_strategy(params):
    strategy = create_strategy(params)  # strategy, risk_tolerance
    metrics = play_games(strategy, opponent)
    return metrics["win_rate"]  # 最大化
```

## 🏗️ 项目结构

```
lingminopt/
├── lingminopt/              # 核心包
│   ├── core/               # 核心引擎
│   │   ├── optimizer.py    # 优化引擎
│   │   ├── searcher.py     # 搜索空间
│   │   ├── evaluator.py    # 评估器
│   │   └── strategy.py     # 搜索策略
│   ├── config/             # 配置
│   │   └── config.py
│   ├── utils/              # 工具
│   │   └── logger.py
│   └── cli/               # 命令行接口
│       └── commands.py
├── setup.py                # 安装配置
├── pyproject.toml          # 现代配置
└── README.md              # 本文件
```

## 🎯 模板

LingMinOpt 提供常用场景模板：

- `minimal` - 最简起点
- `ml-optimization` - 机器学习优化
- `database-optimization` - 数据库调优
- `game-optimization` - 游戏策略优化

```bash
lingminopt init my-project --template ml-optimization
```

## 📊 结果

结果保存为 JSON 格式：

```json
{
  "best_score": 0.4523,
  "best_params": {
    "learning_rate": 0.0001,
    "dropout": 0.2,
    "optimizer": "adamw"
  },
  "history": [
    {
      "experiment_id": 0,
      "params": {"lr": 0.001, "dropout": 0.5},
      "score": 0.5234,
      "timestamp": "2024-01-01T10:00:00"
    }
  ],
  "total_experiments": 42,
  "total_time": 126.5,
  "improvement": 0.0711
}
```

## 🔌 可扩展性

### 自定义评估器

```python
from lingminopt import EvaluatorBase

class MyEvaluator(EvaluatorBase):
    def evaluate(self, params):
        # 你的自定义评估逻辑
        result = run_my_experiment(params)
        return result["score"]

optimizer = MinimalOptimizer(
    evaluator=MyEvaluator(),
    search_space=search_space
)
```

### 自定义搜索策略

```python
from lingminopt import SearchStrategy

class MyStrategy(SearchStrategy):
    def suggest_next(self, history):
        # 你的自定义搜索逻辑
        return next_params

optimizer = MinimalOptimizer(
    evaluate=evaluate,
    search_space=search_space,
    search_strategy=MyStrategy()
)
```

## 🧪 测试

```bash
# 运行测试
pytest tests/

# 带覆盖率
pytest --cov=lingminopt tests/
```

## 📖 文档

- [API 文档](docs/API.md)
- [教程](docs/TUTORIAL.md)
- [高级用法](docs/ADVANCED.md)
- [设计文档](docs/DESIGN.md)

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 灵感来自 [Karpathy 的 autoresearch](https://github.com/karpathy/autoresearch)
- 基于 灵研 (LingResearch) - 极简自主研究的哲学
- 社区反馈和贡献

## 📞 联系方式

- GitHub: https://github.com/yourusername/lingminopt
- Issues: https://github.com/yourusername/lingminopt/issues

---

**由 Guangda 用 ❤️ 制作**
