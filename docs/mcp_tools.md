# lingminopt MCP Tools

> 从 AGENTS.md 迁出，2026-05-06 瘦身。2026-05-31 P0修复后更新。

## MCP Server 工具清单 (16工具)

### 搜索空间 + 优化执行

| 工具 | 功能 |
|------|------|
| `create_search_space` | 创建搜索空间 |
| `run_optimization` | 运行优化（声明式评估器，按名称调用） |
| `list_evaluators` | 列出可用评估器（sphere/rastrigin/rosenbrock/ackley/quadratic/neg_mean） |
| `get_optimization_status` | 优化状态查询 |
| `create_strategy_profile` | 创建优化策略 |

### 结果管理

| 工具 | 功能 |
|------|------|
| `load_results` | 加载优化结果（路径校验，限data/和results/） |
| `compare_results` | 对比两次优化结果 |
| `create_experiment_config` | 创建实验配置 |

### 反馈闭环

| 工具 | 功能 |
|------|------|
| `feedback_from_result` | 从优化结果生成结构化反馈 |
| `export_training_sample` | 导出训练样本 (best_only/top_k/all/trajectory) |
| `list_feedback` | 列出反馈记录 |
| `optimization_pipeline` | 一键闭环：优化→反馈→训练数据导出 |

### MKO元知识优化

| 工具 | 功能 |
|------|------|
| `mko_token_ranking` | 灵族Token消耗排名 |
| `mko_run` | 运行MKO优化 (prompt/routing/retry) |
| `mko_recommendations` | 全族优化建议 |

### 审计

| 工具 | 功能 |
|------|------|
| `list_audit_log` | 查看审计日志 |

## 安全架构

- **无exec()/eval()/compile()** — 评估函数通过声明式注册表调用
- **路径校验** — `_validate_data_path()` 限制在 data/ 和 results/ 目录
- **AST沙箱已移除** — 因不再需要动态代码执行

## 可用资源

- MCP Server: `/home/ai/lingminopt/lingminopt/mcp_server.py` (16工具)
- 反馈数据: `data/feedback/`
- MKO数据: `data/mko/`
- 审计日志: `data/audit_log.jsonl`
