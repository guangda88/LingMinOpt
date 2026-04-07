# 灵极优 v0.2.0 系统审计报告

**审计员**: 灵极优 ⚡  
**审计日期**: 2026-04-07  
**审计范围**: /home/ai/LingMinOpt 全仓库 + /home/ai/zhineng-knowledge-system/mcp_servers/  
**对齐依据**: 灵通宪章 v1.0（自觉、自决、进化）+ 灵信章程 v0.2.0  

---

## 一、宪章对齐检查

| 宪章条款 | 状态 | 说明 |
|----------|------|------|
| **自觉** — 知道真实状态 | ⚠️ 部分 | optimizer.py:97 catch Exception + continue 静默吞掉错误，违反"不被表面数据欺骗" |
| **自决** — 发现问题就行动 | ✅ | v0.2.0 主动修复了 AGENTS.md 记录的所有 CRITICAL/HIGH 问题 |
| **进化** — 未发现的原因即进化方向 | ✅ | MCP 评估报告产出，训练数据流水线对接，反馈收集机制就位 |

## 二、灵信章程对齐检查

| 章节条款 | 状态 | 说明 |
|----------|------|------|
| §一 定位 | ✅ | 灵极优作为自优化框架，定位清晰 |
| §四 频道 self-optimize | ✅ | 已通过灵信 self-optimize 频道发送 MCP 评估报告 |
| §五 消息伦理 · 署名制 | ✅ | 所有灵信消息均署名 lingjiyou |
| §五 频道守则 | ✅ | 未跨频道灌水 |
| §九 source_type 标注 | ⚠️ | PostgreSQL 灵信系统的消息未标注 source_type（字段可能不存在） |
| §九 身份幻觉治理 | ✅ | 以 lingjiyou 身份发言，未冒用 |
| §十 与灵信关系 | ✅ | 作为平等协作者参与 |

## 三、代码质量审计

### 3.1 严重问题 (CRITICAL)

| # | 文件 | 行号 | 问题 | 风险 |
|---|------|------|------|------|
| C1 | `core/optimizer.py` | 97 | `catch Exception + continue` 静默吞掉所有评估错误 | 高 — 违反自觉原则，可能隐藏真实 bug |
| C2 | `cli/commands.py` | 591-592 | SQL 注入风险：`safe_sql = sql.replace("$1", thread_id)` 用字符串拼接构造 SQL | 高 — 虽然是灵信内部使用，但违反安全规范 |
| C3 | `cli/commands.py` | 510 | 硬编码数据库凭证 `zhineng_secure_2024` | 高 — 凭证泄露风险 |

### 3.2 重要问题 (HIGH)

| # | 文件 | 问题 | 说明 |
|---|------|------|------|
| H1 | `core/optimizer.py` + `core/config.py` + `config/config.py` | ExperimentConfig 三处定义 | AGENTS.md 已知问题，应统一到 config/config.py |
| H2 | `cli/commands.py` | Line 2, 450-451, 468 引用 `minopt` | 历史遗留，应改为 `lingminopt` |
| H3 | `__init__.py` | 导出可能引用错误来源 | 需验证从哪个 ExperimentConfig 导出 |

### 3.3 一般问题 (MEDIUM)

| # | 文件 | 问题 |
|---|------|------|
| M1 | `examples/example1_quadratic.py` | 21 处 print()，应使用 logger |
| M2 | `examples/example2_ml_tuning.py` | 30 处 print()，应使用 logger |
| M3 | `cli/commands.py` | `import subprocess` 未使用 (line 506) |
| M4 | `cli/commands.py` | 变量名 `l` (lines 540, 567) 违反 PEP8 |

### 3.4 测试状态

| 项目 | 结果 |
|------|------|
| 测试数量 | 26 |
| 通过率 | 26/26 (100%) |
| 覆盖类 | SearchSpace(9), ExperimentConfig(6), Evaluators(2), SearchStrategies(2), Optimizer(4), Models(3) |
| 缺失覆盖 | CLI commands, Strategy grid/bayesian/annealing 独立测试, evaluator edge cases |

## 四、MCP Server 审计 (zhineng-knowledge-system)

| 工具 | 安全性 | 验证状态 |
|------|--------|----------|
| knowledge_search | ✅ 只读代理 | ✅ 已验证 |
| ask_question | ✅ 只读代理 | ✅ 已验证 |
| domain_query | ⚠️ 需 JWT | 401 未解决 |
| optimization_status | ✅ 只读聚合 | ✅ 已验证 |
| submit_feedback | ✅ 输入校验 | ✅ 已验证 |
| submit_search_feedback | ✅ 输入校验 | ✅ 持久化 |
| get_search_feedback | ✅ 只读代理 | ✅ 已验证 |
| generate_training_data | ⚠️ 子进程调用 | 需限制 output_dir 路径 |
| safe_db_query | ✅ SELECT+白名单 | ✅ 安全校验通过 |
| list_categories | ✅ 只读 | ✅ |
| system_stats | ✅ 只读 | ✅ |

## 五、幻觉风险评估

### 5.1 已识别幻觉点

| # | 风险点 | 类型 | 严重度 |
|---|--------|------|--------|
| 幻1 | optimizer.py:97 静默跳过失败实验，可能让优化器"以为"实验数已满但实际全部失败 | 结果幻觉 | 高 |
| 幻2 | FeedbackCollector 纯内存存储，反馈数据重启后消失，分析结果基于不完整数据 | 数据幻觉 | 中 |
| 幻3 | MCP generate_training_data 工具调用子进程，如果脚本不存在返回错误但可能被上层忽略 | 状态幻觉 | 低 |

### 5.2 幻觉病例（上报灵妍）

**病例 #1: 静默失败导致的"空跑"幻觉**

- **位置**: `lingminopt/core/optimizer.py:66-97`
- **机制**: 当 evaluate() 抛出异常时，代码 `continue` 跳过。如果 evaluate 本身有 bug（如参数类型错误），优化器会消耗所有 max_experiments 但得不到任何有效结果
- **表现**: OptimizationResult 显示 "experiments: 100, best_score: inf" — 看起来运行完成，实际全部失败
- **分类**: 结果型幻觉 — 系统产出看似完整的输出，但内容为空
- **建议**: 记录失败原因到 history，连续失败超过阈值应中断并报错

## 六、对齐规范性问题

### 6.1 代码规范

| 规范 | 合规 | 说明 |
|------|------|------|
| line-length=100 (pyproject.toml) | ✅ | |
| black 格式化 | ⚠️ | examples/ 未格式化 |
| isort 排序 | ✅ | |
| type hints | ⚠️ | 部分函数缺少返回类型 |
| Google docstrings | ⚠️ | CLI commands 的 inbox 相关函数缺少 docstring |

### 6.2 安全规范

| 规范 | 合规 | 说明 |
|------|------|------|
| 输入验证 | ✅ | SearchSpace, ExperimentConfig 有验证 |
| 凭证管理 | ❌ | DB 密码硬编码在 commands.py |
| SQL 安全 | ❌ | inbox reply 用字符串拼接 SQL |
| 路径遍历防护 | ✅ | CLI init 有路径校验 |

## 七、修复优先级

### P0 — 立即修复

1. **C1**: optimizer.py 静默异常 → 记录到 history，连续失败中断
2. **C2**: inbox SQL 注入 → 改用 asyncpg 参数化查询
3. **C3**: 硬编码凭证 → 改用环境变量

### P1 — 本次提交前修复

4. **H1**: ExperimentConfig 去重 — 删除 core/config.py，统一到 config/config.py
5. **H2**: minopt → lingminopt 替换
6. **M3-M4**: 清理 lint warnings

### P2 — 后续迭代

7. Examples print → logger
8. CLI tests
9. MCP generate_training_data 路径限制
10. FeedbackCollector 持久化（等灵知回复）

---

**审计结论**: 灵极优 v0.2.0 核心功能稳定（26/26 测试通过），但存在 3 个严重安全和可靠性问题（静默异常、SQL注入、凭证泄露），以及 ExperimentConfig 重复定义导致的架构不清晰。建议在 P0 修复完成后方可提交灵依审查。

---

## 八、修复执行记录

### P0 修复（已完成）

| # | 修复项 | 文件 | 方法 |
|---|--------|------|------|
| C1 | 静默异常→连续失败中断 | `core/optimizer.py` | 添加 consecutive_failures 计数，超过 max(3, max_experiments//5) 次中断 |
| C2 | SQL注入→参数化查询 | `cli/commands.py` | inbox read/reply 改用 asyncpg 参数化查询 |
| C3 | 硬编码凭证→环境变量 | `cli/commands.py` | 移除默认值，要求 LINGMESSAGE_DB_URL 环境变量 |
| H1 | ExperimentConfig 去重 | `core/config.py` | 改为 re-export from config.config |
| H2 | minopt→lingminopt | `cli/commands.py` | 4处替换 |
| M3 | unused import subprocess | `cli/commands.py` | 改用 asyncpg，移除 subprocess |
| M4 | 变量名 `l` | `cli/commands.py` | 改用 dict row 访问 |

### 新增回归测试（3项）

| 测试 | 验证 |
|------|------|
| `test_consecutive_failures_abort` | C1修复：全部失败时必须中止，不能空跑 |
| `test_single_failure_does_not_abort` | C1修复：偶尔失败不应中止 |
| `test_experiment_config_single_source` | H1修复：core.config === config.config |

### 测试结果

```
29 passed in 0.09s (原26 + 新增3)
```

