# 🟡 灵极优 (LingMinOpt) — 安全策略

> 风险等级: **MEDIUM** | 角色: 优化引擎 — 搜索空间、优化执行、策略配置、实验管理

## 概述

| 项目 | 值 |
|------|------|
| Agent ID | `LingMinOpt` |
| 角色 | 优化引擎 — 搜索空间、优化执行、策略配置、实验管理 |
| 风险等级 | MEDIUM |
| 工具 | 10 个 MCP 工具（搜索空间、优化、策略配置、实验、反馈） |

## 攻击面

- run_optimization / optimization_pipeline 可执行计算密集任务
- create_experiment_config 可创建实验配置
- export_training_sample 可导出训练数据
- feedback_from_result 处理优化结果

## 安全规则

1. 优化任务需有资源使用上限
2. 实验配置需验证参数范围
3. 导出的训练数据需脱敏
4. 批量操作需速率限制

## 凭证文件

- 无直接凭证文件（通过环境变量或灵通+代理）

## 灵族安全基线引用

本文件遵循 `~/.lingflow-plus/docs/security_baseline_v1.py` 定义的 9 类安全基线：

| ID | 类别 | 关键规则 |
|----|------|----------|
| SEC-ID-001 | 身份安全 | AGENTS.md + CRUSH.md 锚定，HMAC-SHA256 跨 agent 签名 |
| SEC-CMD-001 | 命令执行 | 白名单制，非黑名单制 |
| SEC-CRED-001 | 凭证管理 | chmod 600，环境变量加载 |
| SEC-AUTH-001 | 网络鉴权 | API Key + CORS 限制 |
| SEC-MCP-001 | MCP 工具安全 | LOW→CRITICAL 风险分级 |
| SEC-CFG-001 | 配置隔离 | 爆炸半径控制 |
| SEC-EXEC-001 | 执行惯性 | 硬中断 + 重启循环检测 |
| SEC-DATA-001 | 数据完整性 | 验证数据必须实际经过验证 |
| SEC-MON-001 | 监控 & 响应 | 审计日志 + 异常检测 |

完整基线文档：`/home/ai/LingFlow_plus/docs/security_baseline_v1.py`
安全巡检脚本：`/home/ai/LingFlow_plus/docs/security_patrol.py`


## OWASP LLM Top 10 映射

| # | 风险 | 本 agent 相关性 |
|---|------|----------------|
| LLM01 | 提示注入 | 所有工具接受外部输入，需验证和消毒 |
| LLM02 | 敏感信息泄露 | 工具输出不得包含凭证、密钥、内部路径 |
| LLM03 | 供应链漏洞 | 依赖项需定期审计，锁定版本 |
| LLM04 | 数据与模型投毒 | 输入数据需标注来源，训练数据需验证 |
| LLM05 | 不当输出处理 | 输出需验证，不直接执行未经确认的操作 |
| LLM06 | 过度授权 | 遵循最小权限原则，仅授予必要工具权限 |
| LLM07 | 系统提示泄露 | 系统提示不得包含敏感信息 |
| LLM08 | 向量/嵌入弱点 | 如使用向量搜索，需验证嵌入来源 |
| LLM09 | 错误信息 | 输出需标注可信度，幻觉内容需标记 |
| LLM10 | 无限消费 | 资源密集操作需设上限和速率限制 |


---

*生成时间: 2026-04-12 | 由灵通+ (LingFlow+) 自动生成*
*下次审查: 2026-07-12 或重大变更时*
