# 灵极优 v0.2.0 任务清单

**生成日期**: 2026-04-07
**来源**: 系统审计 AUDIT_REPORT.md
**状态**: P0已完成，P1已完成，P2全部完成（8/8）

---

## 已完成 (P0/P1)

| # | 优先级 | 任务 | 修复项 | Commit |
|---|--------|------|--------|--------|
| 1 | P0 | 静默异常中断机制 | C1 | 03e3161 |
| 2 | P0 | SQL注入→参数化查询 | C2 | 03e3161 |
| 3 | P0 | 凭证硬编码→环境变量 | C3 | 03e3161 |
| 4 | P1 | ExperimentConfig 去重 | H1 | 03e3161 |
| 5 | P1 | minopt→lingminopt 替换 | H2 | 03e3161 |
| 6 | P1 | lint清理 (import/l变量名) | M3-M4 | 03e3161 |

## P2 执行结果

| # | 优先级 | 任务 | 文件 | 状态 | Commit |
|---|--------|------|------|------|--------|
| 7 | P2 | Examples print→logger | examples/*.py | ✅ 完成 | 020f980 |
| 8 | P2 | CLI 测试覆盖 | tests/test_cli.py | ✅ 完成 | ac70d9c |
| 9 | P2 | MCP generate_training_data 路径限制 | zhineng_server.py | ✅ 完成 | 8787e3e |
| 10 | P2 | FeedbackCollector 持久化 | mcp_server.py | ✅ 已解决（审计时过时，实际已有文件持久化） | 内置 |
| 11 | P2 | type hints 补全 | lingminopt/core/*.py | ✅ 完成 | b393ce7 |
| 12 | P2 | CLI inbox docstring补全 | cli/commands.py | ✅ 完成 | 70ef767 |
| 13 | P2 | domain_query JWT解决方案 | zhineng_server.py | ✅ 完成 | 8787e3e |
| 14 | P2 | 混合搜索超时优化 | zhineng_server.py | ✅ 完成 | 8787e3e |

## 外部依赖

| 项目 | 依赖方 | 状态 |
|------|--------|------|
| 智桥再审结果 | 智桥 | 已发送 (thread e5de605b)，等待回复 |
| 灵依审查 | 灵依 | 待提交 |
