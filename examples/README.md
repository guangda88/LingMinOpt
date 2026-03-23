# LingMinOpt 应用场景示例

本目录包含 LingMinOpt 框架在各种场景下的应用示例。

## 示例列表

### 1. 灵研 (LingResearch) - 自主 AI 研究

**文件**: `lingresearch_demo.py`

**描述**: 简化的灵研（LingResearch）示例，演示如何使用 LingMinOpt 框架进行自主研究。

**特性**:
- 简化版灵研核心概念
- 搜索空间定义和评估函数演示
- 5 行代码开始优化
- 快速反馈循环（模拟）

**运行方式**:
```bash
python lingresearch_demo.py
```

**目标**: 最小化验证集的 BPC (bits per character)

**说明**: 这是 LingMinOpt 框架的一个简化演示。完整的 LingResearch 项目请查看：
- **完整项目**: https://github.com/guangda88/lingresearch
- **本地路径**: `/home/ai/LingResearch/`

完整项目包含：
- 真实的训练数据和模型
- 固定约束（prepare.py）和可变参数（train.py）分离
- 5 分钟训练循环
- AI 代理自主研究（program.md）

---

### 2. 机器学习超参数优化

**目录**: `ml-optimization/`

**描述**: 使用 LingMinOpt 优化机器学习模型的超参数。

**特性**:
- 随机森林超参数优化
- Scikit-learn 集成
- 对数损失评估

**运行方式**:
```bash
cd ml-optimization
python example.py
```

**目标**: 最小化验证集的对数损失

**搜索空间**:
- n_estimators: [50, 100, 200, 300]
- max_depth: [3, 5, 7, 10, None]
- learning_rate: [1e-5, 1e-2]
- 其他随机森林参数

---

### 3. 游戏策略优化

**目录**: `game-optimization/`

**描述**: 优化简单游戏的 AI 策略。

**特性**:
- 多种策略（激进、保守、平衡）
- 策略参数调优
- 胜率/奖励优化

**运行方式**:
```bash
cd game-optimization
python example.py
```

**目标**: 最大化游戏的平均奖励

**搜索空间**:
- strategy_type: [aggressive, conservative, balanced]
- aggression: [0.0, 1.0]
- risk_tolerance: [0.0, 1.0]
- exploration_rate: [0.0, 0.5]

---

### 4. 算法优化

**目录**: `algorithm-optimization/`

**描述**: 优化排序算法的参数和实现细节。

**特性**:
- 多种排序算法（快速排序、冒泡排序、混合排序）
- 算法参数调优
- 执行时间优化

**运行方式**:
```bash
cd algorithm-optimization
python example.py
```

**目标**: 最小化排序算法的平均执行时间

**搜索空间**:
- algorithm: [quick, bubble, hybrid]
- pivot_strategy: [last, random, median_of_three]
- threshold: [5, 50]
- 优化标志

---

### 5. 数据库查询优化

**目录**: `database-optimization/`

**描述**: 优化数据库查询性能。

**特性**:
- 模拟数据库环境
- 索引策略优化
- 缓存配置优化
- QPS 评估

**运行方式**:
```bash
cd database-optimization
python example.py
```

**目标**: 最大化查询吞吐量（QPS）

**搜索空间**:
- index_type: [none, btree, hash]
- index_columns: [category, priority, etc.]
- cache_policy: [lru, lfu]
- cache_size: [50, 200]
- pool_size: [5, 20]

---

### 6. 硬件/编译器优化

**目录**: `hardware-optimization/`

**描述**: 优化编译器标志以提升程序性能。

**特性**:
- GCC 编译器优化
- 多种编译标志组合
- 执行时间优化
- 需要安装 GCC

**运行方式**:
```bash
cd hardware-optimization
python example.py
```

**目标**: 最小化程序执行时间

**搜索空间**:
- opt_level: [-O0, -O1, -O2, -O3, -Os]
- march: [native, x86-64, None]
- loop优化标志
- 其他编译优化标志

**依赖**: GCC 编译器

---

## 如何使用这些示例

### 步骤 1: 安装 LingMinOpt

```bash
cd /home/ai/LingMinOpt
pip install -e .
```

### 步骤 2: 选择示例

根据你的需求选择合适的示例：

- **灵研**: 如果你想做自主 AI 研究
- **ML 优化**: 如果你在做机器学习超参数调优
- **游戏优化**: 如果你在做游戏 AI
- **算法优化**: 如果你想优化算法性能
- **数据库优化**: 如果你在做数据库调优
- **硬件优化**: 如果你想优化编译器标志

### 步骤 3: 运行示例

```bash
cd examples/[example-name]
python example.py
```

### 步骤 4: 查看结果

每个示例都会生成一个结果文件（JSON 格式），包含：
- 最佳参数
- 最佳性能
- 改进幅度
- 实验历史

### 步骤 5: 自定义

基于示例，创建你自己的优化场景：

1. 复制一个相似的示例
2. 修改搜索空间（`SearchSpace`）
3. 实现你的评估函数（`run_experiment`）
4. 运行优化

---

## 示例对比

| 示例 | 目标 | 搜索策略 | 实验时间 | 依赖 |
|------|------|----------|----------|------|
| 灵研 | 最小化 BPC | random | 5分钟/实验 | numpy |
| ML 优化 | 最小化损失 | random | 10秒/实验 | sklearn |
| 游戏 | 最大化奖励 | random | 5秒/实验 | numpy |
| 算法 | 最小化时间 | random | 30秒/实验 | 标准库 |
| 数据库 | 最大化 QPS | random | 30秒/实验 | 标准库 |
| 硬件 | 最小化时间 | random | 60秒/实验 | GCC |

---

## 通用模式

所有示例都遵循相同的模式：

```python
from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig

# 1. 定义搜索空间
search_space = SearchSpace()
search_space.add_continuous("param1", 0.0, 1.0)
search_space.add_discrete("param2", ["option1", "option2"])

# 2. 定义评估函数
def run_experiment(params):
    # 运行你的实验
    result = my_experiment(params)
    return result["score"]  # 返回数值

# 3. 配置优化器
config = ExperimentConfig(
    max_experiments=100,
    time_budget=300,
    direction="minimize"  # 或 "maximize"
)

# 4. 创建优化器
optimizer = MinimalOptimizer(
    evaluate=run_experiment,
    search_space=search_space,
    config=config
)

# 5. 运行优化
result = optimizer.run()

# 6. 查看结果
print(f"Best score: {result.best_score}")
print(f"Best params: {result.best_params}")
```

---

## 性能优化建议

### 1. 缩短实验时间

- 减小数据集大小
- 减少训练/评估的迭代次数
- 使用更快的硬件

### 2. 提高搜索效率

- 从小的搜索空间开始
- 使用更智能的搜索策略（`bayesian`）
- 基于先验知识限制搜索空间

### 3. 并行化

- 未来版本将支持并行实验
- 现在可以手动运行多个实验

---

## 贡献你的示例

如果你有其他应用场景的示例，欢迎贡献！

步骤：
1. 创建新的示例目录
2. 实现评估函数
3. 添加文档
4. 提交 Pull Request

---

## 获取帮助

- 查看主 README: `/home/ai/LingMinOpt/README.md`
- 查看文档: `/home/ai/LingMinOpt/docs/`
- 提交问题: GitHub Issues

---

**祝你优化愉快！** 🚀
