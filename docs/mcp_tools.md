# LingMinOpt MCP Tools & P0 Progress

> 从 AGENTS.md 迁出，2026-05-06 瘦身。

## 灵信线程 #328 — MCP封装进度

### P0 进度 (6/7 完成, 1 评估后跳过)

| # | P0 项 | 状态 | MCP工具名 |
|---|-------|------|-----------|
| 1 | 知识检索 (search+ask) | ✅ | `knowledge_search`, `ask_question` |
| 2 | 训练数据生成 | ✅ | `generate_training_data` |
| 3 | 自优化引擎 | ✅ | `optimization_status`, `analyze_optimization`, `execute_optimization`, `optimization_dashboard`, `trigger_audit`, `audit_history`, `error_analysis`, `log_error`, `submit_feedback` |
| 4 | 文件读写沙箱 | ⏭️ | Crush 已覆盖 |
| 5 | 数据库查询 | ✅ | `safe_db_query` (白名单表) |
| 6 | 领域路由查询 | ✅ | `domain_query` |
| 7 | 命令执行白名单 | ⏭️ | Crush 已覆盖 |

### 反馈闭环 ✅

LingMinOpt MCP Server (`lingminopt/mcp_server.py`) 工具:

| 工具 | 功能 |
|------|------|
| `feedback_from_result` | 从优化结果生成结构化反馈，持久化到 `data/feedback/` |
| `export_training_sample` | 将优化历史导出为训练数据 (best_only/top_k/all/trajectory) |
| `list_feedback` | 列出已保存的反馈记录 |
| `optimization_pipeline` | 一键闭环：优化→反馈→训练数据导出 |
| `compare_results` | 对比两次优化结果 |

闭环流程: `run_optimization` → `feedback_from_result` → `export_training_sample` → `generate_training_data`

### 可用资源

- MCP Server (灵知): `/home/ai/zhineng-knowledge-system/mcp_servers/zhineng_server.py` (37工具)
- MCP Server (灵极优): `/home/ai/LingMinOpt/lingminopt/mcp_server.py` (11工具)
- 训练数据: `/home/ai/zhineng-knowledge-system/data/training/` (16K条)
- 反馈数据: `data/feedback/` (LingMinOpt本地)
- MCP报告: `/home/ai/zhineng-knowledge-system/docs/reports/MCP_ENCAPSULATION_ASSESSMENT.md`
- 灵信线程: #328
