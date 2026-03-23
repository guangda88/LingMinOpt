# LingFlow + LingMinOpt 集成方案

**目标**: 将 LingFlow 的代码优化过程迁移到 LingMinOpt 框架下

**日期**: 2026-03-23
**状态**: 📋 讨论阶段

---

## 📋 当前状况

### LingFlow 的代码优化机制

```
code-analysis → code-optimizer → code-refactor
      ↓              ↓               ↓
   分析代码质量    生成优化方案     执行重构
```

**问题**:
- ❌ 静态优化方案，没有自动化实验
- ❌ 无法尝试不同策略组合
- ❌ 没有自动化的效果评估
- ❌ 无法找到最优配置

---

## 🎯 集成目标

### 目标 1: 自动化代码优化

将代码优化建模为一个可实验的优化问题，自动寻找最优配置。

### 目标 2: 多策略优化

尝试不同的优化策略组合，找到最有效的方案。

### 目标 3: 数据驱动决策

基于实验数据（代码质量、测试结果）做决策，而非直觉。

---

## 💡 集成方案

### 方案 1: 代码配置优化 ⭐ 推荐

**核心思想**: 将代码优化参数化，让 LingMinOpt 搜索最优配置。

#### 搜索空间

```python
search_space = SearchSpace()
search_space.add_discrete("strategy", [
    "refactor_first",           # 先重构，再优化
    "optimize_first",           # 先优化，再重构
    "balanced"                 # 平衡策略
])
search_space.add_discrete("optimization_level", [
    "conservative",             # 保守：只优化明显问题
    "moderate",                # 中等：常见优化
    "aggressive"               # 激进：尽可能优化
])
search_space.add_discrete("refactor_order", [
    ["duplicates", "complexity", "dead_code"],
    ["complexity", "duplicates", "dead_code"],
    ["dead_code", "duplicates", "complexity"]
])
search_space.add_continuous("complexity_threshold", 5, 15)  # 圈复杂度阈值
search_space.add_continuous("duplication_threshold", 0.05, 0.3)  # 重复率阈值
```

#### 评估函数

```python
def evaluate_code_optimization(params):
    """
    评估代码优化配置的效果
    """
    strategy = params["strategy"]
    level = params["optimization_level"]
    order = params["refactor_order"]
    complexity_threshold = params["complexity_threshold"]
    duplication_threshold = params["duplication_threshold"]

    # 1. 运行 code-analysis
    analysis_result = run_code_analysis()

    # 2. 根据 params 生成优化方案
    optimization_plan = generate_optimization_plan(
        analysis_result,
        strategy=strategy,
        level=level,
        order=order,
        complexity_threshold=complexity_threshold,
        duplication_threshold=duplication_threshold
    )

    # 3. 执行优化
    refactored_code = execute_refactoring(optimization_plan)

    # 4. 运行测试
    test_result = run_tests()

    # 5. 重新分析
    new_analysis = run_code_analysis()

    # 6. 计算综合得分
    score = calculate_optimization_score(
        test_pass_rate=test_result["pass_rate"],
        complexity_improvement=analysis_result["complexity"] - new_analysis["complexity"],
        duplication_improvement=analysis_result["duplication"] - new_analysis["duplication"],
        code_changes=len(optimization_plan["changes"])
    )

    return score
```

#### 评分函数

```python
def calculate_optimization_score(test_pass_rate, complexity_improvement,
                               duplication_improvement, code_changes):
    """
    综合评分：
    - 测试通过率：权重 0.4（最重要）
    - 复杂度改进：权重 0.3
    - 重复率改进：权重 0.2
    - 代码变更量：权重 -0.1（惩罚过度修改）
    """
    return (
        test_pass_rate * 0.4 +
        complexity_improvement * 0.3 +
        duplication_improvement * 0.2 -
        code_changes * 0.1
    )
```

#### 优点
- ✅ 自动化实验
- ✅ 多目标优化（质量 + 稳定性）
- ✅ 可找到最优配置
- ✅ 可量化评估效果

#### 缺点
- ⚠️ 需要代码变更（创建新技能）
- ⚠️ 每次实验需要运行测试（时间成本）
- ⚠️ 需要代码回滚机制

---

### 方案 2: LingFlow 技能增强

**核心思想**: 创建新的 LingFlow 技能，内部使用 LingMinOpt。

#### 新技能: code-optimizer-auto

```
skills/code-optimizer-auto/
├── SKILL.md
├── implementation.py
└── optimizer_config.py
```

#### 实现逻辑

```python
from lingminopt import MinimalOptimizer, SearchSpace

def execute_skill(params):
    """
    自动化代码优化技能
    """
    # 1. 定义搜索空间
    search_space = create_optimization_search_space(params)

    # 2. 定义评估函数
    def evaluate(config):
        return evaluate_optimization_config(config, params)

    # 3. 创建优化器
    optimizer = MinimalOptimizer(
        evaluate=evaluate,
        search_space=search_space,
        config=ExperimentConfig(
            max_experiments=50,
            time_budget=600,  # 10 分钟
            direction="maximize"
        )
    )

    # 4. 运行优化
    result = optimizer.run()

    # 5. 应用最佳配置
    best_plan = apply_best_config(result.best_params)

    return {
        "best_config": result.best_params,
        "best_score": result.best_score,
        "optimization_plan": best_plan,
        "experiments": result.total_experiments
    }
```

#### 优点
- ✅ 不改变现有代码结构
- ✅ 与现有工作流无缝集成
- ✅ 可以独立开发
- ✅ 向后兼容

#### 缺点
- ⚠️ 需要新的技能实现
- ⚠️ 增加系统复杂度

---

### 方案 3: 独立优化工具

**核心思想**: 创建独立的工具，在 LingFlow 外部使用。

#### 工具结构

```
lingflow-optimizer/
├── prepare.py           # 固定配置（测试、分析工具）
├── variable.py          # 可变参数（搜索空间、评估）
├── run_optimizer.py     # 主运行脚本
└── utils/
    ├── analyzer.py       # 代码分析
    ├── refactored.py     # 代码重构
    └── tester.py        # 测试运行
```

#### 使用流程

```bash
cd lingflow-optimizer

# 1. 准备环境
python prepare.py

# 2. 定义优化参数
# 编辑 variable.py

# 3. 运行优化
python run_optimizer.py

# 4. 应用最佳配置
# 查看结果并手动或自动应用
```

#### 优点
- ✅ 完全独立，不影响 LingFlow
- ✅ 类似 LingResearch 的工作流
- ✅ 易于测试和迭代
- ✅ 可复用 LingMinOpt 框架

#### 缺点
- ⚠️ 需要手动集成到 LingFlow
- ⚠️ 需要额外的工具链

---

## 📊 方案对比

| 特性 | 方案1: 参数优化 | 方案2: 技能增强 | 方案3: 独立工具 |
|------|----------------|----------------|----------------|
| 集成度 | 高（需要修改现有技能） | 中（新技能） | 低（独立工具） |
| 开发难度 | 中 | 高 | 低 |
| 易用性 | 中 | 高（无缝集成） | 中（需要手动） |
| 自动化程度 | 高 | 高 | 高 |
| 可维护性 | 中 | 中 | 高 |
| 推荐度 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 推荐方案

### 阶段 1: 快速验证（方案3）

先使用独立工具验证想法：

```bash
# 创建 lingflow-optimizer 项目
cd /home/ai
mkdir lingflow-optimizer
cd lingflow-optimizer

# 使用 LingMinOpt 初始化模板
lingminopt init . --template minimal

# 实现代码优化逻辑
# - prepare.py: 配置 LingFlow 的测试和分析工具
# - variable.py: 定义搜索空间和评估函数
# - run_optimizer.py: 运行优化
```

**目标**: 验证 LingMinOpt 是否适合代码优化场景

**时间**: 1-2 天

---

### 阶段 2: 集成到 LingFlow（方案2）

如果验证成功，创建新技能集成到 LingFlow：

```bash
# 创建 code-optimizer-auto 技能
cd /home/ai/LingFlow/skills
mkdir code-optimizer-auto
cd code-optimizer-auto

# 实现
# - SKILL.md: 技能描述
# - implementation.py: 使用 LingMinOpt 的实现
```

**目标**: 将自动化优化集成到 LingFlow 工作流

**时间**: 2-3 天

---

### 阶段 3: 深度集成（方案1）

如果集成成功，考虑深度修改现有技能：

```bash
# 修改 code-optimizer 技能
cd /home/ai/LingFlow/skills/code-optimizer

# 添加配置参数
# - 添加参数化优化支持
# - 与 code-optimizer-auto 共享逻辑
```

**目标**: 完全替代手动优化流程

**时间**: 3-5 天

---

## 🔍 关键技术挑战

### 1. 代码回滚

每次实验后需要回滚代码，避免影响后续实验。

**解决方案**:
- 使用 git stash
- 使用临时分支
- 使用虚拟文件系统

### 2. 评估函数设计

需要平衡多个指标：
- 代码质量（复杂度、重复率）
- 功能正确性（测试通过率）
- 稳定性（代码变更量）

**解决方案**:
- 加权评分
- 多目标优化
- 帕累托前沿

### 3. 实验时间

代码优化 + 测试可能较慢（分钟级）。

**解决方案**:
- 减小测试集
- 使用缓存
- 限制实验次数
- 使用更快的搜索策略（random）

---

## 📋 实施步骤

### 第一步: 验证可行性（1-2天）

1. 创建 lingflow-optimizer 独立项目
2. 定义简单的搜索空间（1-2 个参数）
3. 实现基本的评估函数
4. 运行几次实验，验证流程

**成功标准**:
- 可以运行完整的实验循环
- 可以量化评估优化效果
- 可以回滚代码

---

### 第二步: 增强功能（2-3天）

1. 扩展搜索空间（更多参数）
2. 改进评估函数（多指标）
3. 添加代码回滚机制
4. 集成 LingFlow 的测试和分析工具

**成功标准**:
- 可以找到比手动优化更好的配置
- 所有实验可以自动回滚
- 测试通过率 > 95%

---

### 第三步: 集成到 LingFlow（2-3天）

1. 创建 code-optimizer-auto 技能
2. 将优化逻辑封装到技能中
3. 更新技能配置和文档
4. 集成到工作流中

**成功标准**:
- 可以通过 CLI 或 API 触发自动化优化
- 与其他技能无缝协作
- 生成清晰的优化报告

---

## 🚀 预期收益

### 直接收益

- ✅ **自动化**: 减少手动优化的工作量
- ✅ **数据驱动**: 基于实验数据做决策
- ✅ **最优配置**: 找到手动难以发现的优化方案
- ✅ **可复现**: 每次优化都有完整的实验记录

### 长期收益

- ✅ **持续改进**: 可以定期运行，持续改进代码
- ✅ **知识积累**: 实验数据可以用于训练更好的策略
- ✅ **通用化**: 方法可以应用到其他代码库

---

## 🤔 需要讨论的问题

1. **优先级**: 哪个方案最适合当前需求？
2. **时间预算**: 可以投入多少开发时间？
3. **风险承受度**: 是否愿意修改现有 LingFlow 代码？
4. **验证标准**: 如何定义优化是否成功？

---

## 📞 下一步

**建议**: 从方案3（独立工具）开始

1. 创建快速原型（1天）
2. 验证 LingMinOpt 对代码优化的适用性
3. 根据结果决定后续集成方式

**是否开始实施？**

---

**生成时间**: 2026-03-23
**生成者**: Crush
**状态**: 📋 待讨论
