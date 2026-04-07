# LingMinOpt MCP 封装评估

**日期**: 2026-04-07
**版本**: v0.2.0
**评估目标**: 评估将 LingMinOpt 所有功能封装为 MCP (Model Context Protocol) 服务的必要性和可行性

---

## 一、MCP 概述

MCP (Model Context Protocol) 是 Anthropic 提出的标准化协议，允许 AI 模型通过统一的 JSON-RPC 接口调用外部工具。封装为 MCP 服务后，任何支持 MCP 的 AI 客户端（如 Claude Desktop、Cursor、Crush 等）可以直接调用 LingMinOpt 的优化能力，无需编写 Python 代码。

**MCP 核心概念**:
- **Tool**: 可被 AI 调用的函数，有明确的输入/输出 schema
- **Resource**: 可被 AI 读取的数据源
- **Prompt**: 预定义的提示模板

---

## 二、功能清单与分类

### A. 核心 API（Python SDK 级别）

| # | 功能 | 类/方法 | 输入 | 输出 | 类型 |
|---|------|---------|------|------|------|
| 1 | 创建搜索空间 | `SearchSpace()` | 无 | SearchSpace 实例 | 状态构建 |
| 2 | 添加离散参数 | `SearchSpace.add_discrete()` | name, choices | None | 状态构建 |
| 3 | 添加连续参数 | `SearchSpace.add_continuous()` | name, min, max | None | 状态构建 |
| 4 | 从字典创建空间 | `SearchSpace.from_dict()` | dict | SearchSpace | 状态构建 |
| 5 | 随机采样 | `SearchSpace.sample()` | 无 | dict | 探索 |
| 6 | 创建配置 | `ExperimentConfig()` | 各参数 | ExperimentConfig | 状态构建 |
| 7 | 创建优化器 | `MinimalOptimizer()` | evaluate, space, config, strategy, seed | MinimalOptimizer | 状态构建 |
| 8 | 运行优化 | `MinimalOptimizer.run()` | 无 | OptimizationResult | **核心执行** |
| 9 | 查询状态 | `MinimalOptimizer.get_status()` | 无 | dict | 查询 |
| 10 | 创建实验配置 | `ExperimentConfig()` | max_experiments, time_budget, direction... | ExperimentConfig | 状态构建 |
| 11 | 比较分数 | `ExperimentConfig.is_better()` | new_score, old_score | bool | 判断 |

### B. 数据模型（序列化/反序列化）

| # | 功能 | 类/方法 | 输入 | 输出 | 类型 |
|---|------|---------|------|------|------|
| 12 | 实验序列化 | `Experiment.to_dict()` | 无 | dict | 序列化 |
| 13 | 实验反序列化 | `Experiment.from_dict()` | dict | Experiment | 序列化 |
| 14 | 结果序列化 | `OptimizationResult.to_dict()` | 无 | dict | 序列化 |
| 15 | 结果反序列化 | `OptimizationResult.from_dict()` | dict | OptimizationResult | 序列化 |
| 16 | 结果转JSON | `OptimizationResult.to_json()` | indent | str | 序列化 |
| 17 | 保存结果 | `OptimizationResult.save()` | filepath | None | 持久化 |
| 18 | 加载结果 | `OptimizationResult.load()` | filepath | OptimizationResult | 持久化 |

### C. 搜索策略

| # | 功能 | 类 | 描述 | 类型 |
|---|------|-----|------|------|
| 19 | 随机搜索 | `RandomSearch` | 均匀随机采样 | 策略 |
| 20 | 网格搜索 | `GridSearch` | 穷举所有组合 | 策略 |
| 21 | 贝叶斯搜索 | `BayesianSearch` | 利用/探索平衡 | 策略 |
| 22 | 模拟退火 | `SimulatedAnnealing` | 温度扰动 | 策略 |
| 23 | 策略工厂 | `create_strategy()` | 按名称创建 | 工厂 |

### D. 评估器

| # | 功能 | 类 | 描述 | 类型 |
|---|------|-----|------|------|
| 24 | 评估器基类 | `EvaluatorBase` | 抽象基类 | 扩展点 |
| 25 | 函数评估器 | `FunctionEvaluator` | 包装 callable | 适配器 |
| 26 | 定时评估器 | `TimedEvaluator` | 带超时的包装器 | 适配器 |

### E. CLI 命令

| # | 功能 | 命令 | 输入 | 输出 | 类型 |
|---|------|------|------|------|------|
| 27 | 初始化项目 | `lingminopt init` | project_name, template | 文件 | 项目管理 |
| 28 | 运行优化 | `lingminopt run` | config, max_experiments | 结果文件 | **核心执行** |
| 29 | 生成报告 | `lingminopt report` | results_file | 终端输出 | 查询 |

### F. 辅助功能

| # | 功能 | 函数 | 描述 | 类型 |
|---|------|------|------|------|
| 30 | 项目名验证 | `validate_project_name()` | 防路径遍历 | 安全 |
| 31 | 配置文件验证 | `validate_config_file()` | 验证JSON配置 | 安全 |
| 32 | 日志配置 | `setup_logging()` | 配置日志级别 | 工具 |

---

## 三、MCP 封装必要性评估

### 评估标准

| 等级 | 含义 |
|------|------|
| ⭐⭐⭐ **必要** | MCP 封装后价值显著提升，用户强需求 |
| ⭐⭐ **有价值** | MCP 封装有用，但非关键路径 |
| ⭐ **可选** | 锦上添花，优先级低 |
| ❌ **不建议** | 不适合 MCP 封装 |

### 逐项评估

#### ⭐⭐⭐ 必要封装（高价值，用户直接受益）

| # | 功能 | Tool 名称 | 理由 |
|---|------|-----------|------|
| 8 | 运行优化 | `optimize` | **核心价值**。AI 直接说"帮我优化这个函数"即可执行。用户无需写 Python 代码，AI 自动构建搜索空间和评估函数 |
| 28 | CLI 运行优化 | `run_optimization` | 已有项目配置的场景，AI 直接触发运行 |
| 29 | 生成报告 | `generate_report` | AI 读取结果并生成自然语言分析，比终端输出更有价值 |
| 17 | 保存结果 | `save_results` | 持久化优化结果，跨会话使用 |
| 18 | 加载结果 | `load_results` | AI 读取历史结果进行对比分析 |

#### ⭐⭐ 有价值封装（增强体验）

| # | 功能 | Tool 名称 | 理由 |
|---|------|-----------|------|
| 1-4 | 构建搜索空间 | `create_search_space` | AI 帮用户定义参数空间，交互式构建 |
| 5 | 随机采样 | `sample_parameters` | 预览参数空间，调试用 |
| 6,10 | 创建配置 | `create_experiment_config` | AI 引导用户配置优化参数 |
| 9 | 查询状态 | `get_optimization_status` | 长时间优化任务的进度查询 |
| 11 | 比较分数 | `compare_scores` | AI 判断优化是否有效 |
| 27 | 初始化项目 | `init_project` | 快速创建优化项目脚手架 |
| 14-16 | 结果序列化 | `export_results` | 导出多种格式 |

#### ⭐ 可选封装（低优先级）

| # | 功能 | 理由 |
|---|------|------|
| 12-13 | Experiment 序列化 | 内部使用，用户不直接交互 |
| 19-23 | 搜索策略类 | 通过 `optimize` 的 `strategy` 参数间接使用，无需单独暴露 |
| 24-26 | 评估器类 | Python SDK 级别，MCP 场景下评估函数由 AI 或用户直接提供 |
| 30-32 | 辅助函数 | 内部使用，MCP 层自动处理 |

#### ❌ 不建议封装

| 功能 | 理由 |
|------|------|
| `FunctionEvaluator` 类实例化 | MCP 场景下，evaluate 函数应作为参数传入 `optimize` tool，不需要单独实例化 |
| `TimedEvaluator` 包装 | 超时逻辑应内置在 MCP server 中，不需要用户感知 |
| `ParameterConfig` 内部类 | 实现细节，不应暴露 |
| `SearchStrategy` 子类直接构造 | 通过工厂函数间接使用即可 |

---

## 四、MCP 封装可行性评估

### 4.1 技术可行性

| 维度 | 评估 | 说明 |
|------|------|------|
| **协议兼容** | ✅ 完全可行 | MCP 是 JSON-RPC 协议，Python 有 `mcp` 官方 SDK |
| **类型映射** | ✅ 可行 | LingMinOpt 的输入输出都是基本类型（dict, float, int, str），可直接映射为 JSON Schema |
| **状态管理** | ⚠️ 需要设计 | MinimalOptimizer 是有状态的，MCP 是无状态调用，需要会话管理机制 |
| **回调函数** | ⚠️ 主要挑战 | `evaluate` 是 Python callable，MCP 无法直接传递函数。需要替代方案 |
| **长时间运行** | ⚠️ 需要设计 | 优化可能运行很长时间，需要异步/进度报告机制 |
| **文件系统** | ✅ 可行 | 读写 JSON 文件，MCP server 本地运行，无权限问题 |

### 4.2 核心挑战与解决方案

#### 挑战 1: 评估函数传递

**问题**: `MinimalOptimizer` 需要一个 `Callable[[Dict[str, Any]], float]`，MCP 协议只能传递 JSON 数据。

**解决方案**:

| 方案 | 描述 | 适用场景 |
|------|------|----------|
| **A. 内置评估器** | 预定义常见评估函数（数学函数、ML 指标） | 简单场景 |
| **B. 代码注入** | AI 生成评估函数代码，MCP server 动态执行 | 高级场景（需安全沙箱） |
| **C. 外部回调** | MCP server 调用外部 HTTP API 获取分数 | 分布式场景 |
| **D. CLI 模式** | MCP 封装 `lingminopt run`，评估函数在 `variable.py` 中 | 已有项目场景 |

**推荐**: 优先实现 D（CLI 模式），其次 A + B。

#### 挑战 2: 有状态会话

**问题**: 优化过程涉及 SearchSpace → ExperimentConfig → MinimalOptimizer → Result 的多步构建。

**解决方案**:

```python
# 方案: 会话存储
sessions = {}  # session_id -> {search_space, config, optimizer, result}

@mcp.tool()
def create_search_space(session_id: str, params: dict) -> str:
    """创建搜索空间，返回 session_id"""

@mcp.tool()
def run_optimization(session_id: str, strategy: str) -> dict:
    """运行优化，返回结果"""
```

#### 挑战 3: 长时间运行

**问题**: `optimizer.run()` 可能阻塞数分钟到数小时。

**解决方案**:

```python
# 方案: 异步执行 + 状态查询
@mcp.tool()
async def start_optimization(session_id: str) -> str:
    """启动优化，返回 task_id"""

@mcp.tool()
def get_optimization_status(task_id: str) -> dict:
    """查询优化进度"""

@mcp.tool()
def get_optimization_result(task_id: str) -> dict:
    """获取优化结果（完成后）"""
```

### 4.3 推荐的 MCP Tool 设计

基于以上分析，推荐以下 **8 个 MCP Tools**:

```python
# 1. 快速优化（一站式，最常用）
@mcp.tool()
def optimize(
    objective: str,          # 目标函数的 Python 代码（字符串）
    parameters: dict,        # {"discrete": {"x": [1,2,3]}, "continuous": {"y": [0, 10]}}
    max_experiments: int = 50,
    strategy: str = "random",
    direction: str = "minimize",
    seed: int = None
) -> dict:
    """
    一站式优化：定义参数空间和目标函数，立即执行优化。
    返回: {best_score, best_params, total_experiments, total_time}
    """

# 2. 初始化项目
@mcp.tool()
def init_project(
    project_name: str,
    template: str = "minimal"  # minimal, ml-optimization, database-optimization, game-optimization
) -> str:
    """创建优化项目脚手架"""

# 3. 运行已有项目
@mcp.tool()
def run_project(
    project_path: str,
    config_file: str = "config.json",
    max_experiments: int = None
) -> dict:
    """运行已有项目的优化"""

# 4. 生成报告
@mcp.tool()
def generate_report(
    results_file: str,
    format: str = "text"  # text, markdown, json
) -> str:
    """从结果文件生成可读报告"""

# 5. 采样参数空间
@mcp.tool()
def sample_parameters(
    parameters: dict,
    count: int = 5,
    seed: int = None
) -> list:
    """预览参数空间的随机采样点"""

# 6. 比较优化结果
@mcp.tool()
def compare_results(
    results_file_1: str,
    results_file_2: str
) -> dict:
    """比较两次优化的结果"""

# 7. 加载历史结果
@mcp.tool()
def load_results(filepath: str) -> dict:
    """加载保存的优化结果"""

# 8. 保存结果
@mcp.tool()
def save_results(result_data: dict, filepath: str) -> str:
    """保存优化结果到文件"""
```

### 4.4 工作量估算

| 模块 | 预估工时 | 依赖 |
|------|----------|------|
| MCP Server 框架搭建 | 4h | `mcp` Python SDK |
| 8 个 Tool 实现 | 8h | 现有 API |
| 会话管理（有状态支持） | 4h | 无 |
| 代码注入沙箱（安全执行） | 8h | `restrictedpython` 或子进程隔离 |
| 异步执行支持 | 4h | `asyncio` |
| Schema 定义与测试 | 4h | JSON Schema |
| 文档与示例 | 4h | 无 |
| **合计** | **~36h** | |

### 4.5 依赖与风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| `mcp` SDK 变更 | 中 | 锁定版本，关注更新 |
| 代码注入安全 | 高 | 沙箱执行，限制文件/网络访问 |
| 长时间运行阻塞 | 中 | 异步设计，超时控制 |
| AI 生成的评估函数有误 | 中 | 错误处理，友好提示 |
| 搜索空间过大导致超时 | 低 | 设置默认上限 |

---

## 五、综合评估结论

### 必要性评分: ⭐⭐⭐ (高)

1. **AI 原生优化**: MCP 封装后，AI 可以直接帮用户优化超参数，无需用户写代码
2. **工作流集成**: 可嵌入 Claude Desktop、Cursor 等 AI 工具的日常工作流
3. **降低门槛**: 5 行代码 → 1 句自然语言描述
4. **差异化**: 目前没有成熟的 Python 优化框架提供 MCP 服务

### 可行性评分: ⭐⭐⭐ (高)

1. **技术成熟**: MCP Python SDK 已稳定，类型映射无障碍
2. **架构适配**: LingMinOpt 的 API 设计简洁，封装成本低
3. **主要挑战可控**: 评估函数传递和状态管理都有成熟解决方案

### 建议路线

```
Phase 1 (MVP, ~16h):        optimize + init_project + run_project + generate_report
Phase 2 (增强, ~12h):       sample_parameters + compare_results + load/save + 会话管理
Phase 3 (高级, ~8h):        异步执行 + 沙箱 + 自定义评估器支持
```

**Phase 1 即可发布**，覆盖 80% 的使用场景。
