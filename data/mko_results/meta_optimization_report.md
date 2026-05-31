# 元知识优化报告 — 灵族

**生成时间**: 2026-05-29 20:55:38
**数据来源**: 灵族crush.db + LingBus

## 按成员Token消耗排名

| 成员 | 总Token | 占比 | 输出/输入比 | 工具调用 | 优先级 |
|------|---------|------|-------------|----------|--------|
| lingzhi | 1,896,005 | 25.4% | 10.1x | 21,273 | 高优 |
| lingtongask | 1,193,193 | 16.0% | 5.4x | 11,318 | 高优 |
| lingflow | 861,436 | 11.6% | 3.1x | 14,962 | 高优 |
| lingyang | 785,643 | 10.5% | 1.3x | 10,928 | 高优 |
| lingclaude | 781,944 | 10.5% | 3.9x | 12,578 | 高优 |
| lingresearch | 642,042 | 8.6% | 3.4x | 13,765 | 中优 |
| lingcreate | 484,066 | 6.5% | 0.1x | 1,725 | 中优 |
| lingweb | 362,819 | 4.9% | 6.1x | 6,875 | 低优 |
| lingmessage | 137,230 | 1.8% | 9.7x | 2,329 | 低优 |
| lingxi | 136,807 | 1.8% | 7.1x | 2,881 | 低优 |
| lingminopt | 96,442 | 1.3% | 7.2x | 2,034 | 低优 |
| zhibridge | 57,280 | 0.8% | 7.6x | 1,475 | 低优 |
| lingflowplus | 19,156 | 0.3% | 18.5x | 605 | 低优 |

## 综合结果

- **综合得分**: 0.9556
- **总实验次数**: 51
- **总耗时**: 0.15 秒

## 提示词优化

- **model**: glm-5.1
- **temperature**: 0.5419
- **max_tokens**: 16384
- **system_prompt_template**: minimal

- **最优得分**: 0.9724
- **实验次数**: 19
- **耗时**: 0.08 秒

## 路由优化

- **code_model**: glm-5.1
- **debug_model**: glm-5.1
- **chat_model**: glm-4.7-flash
- **routing_strategy**: cost_based

- **最优得分**: 1.0000
- **实验次数**: 12
- **耗时**: 0.07 秒

## 重试优化

- **primary_retry_limit**: 5
- **backoff_base**: 3.4259
- **backoff_max**: 20.6031
- **degraded_call_threshold**: 10
- **degraded_time_threshold**: 84.2372
- **degradation_strategy**: timeout_increase
- **fallback_model**: llama-3.3-70b

- **最优得分**: 0.8943
- **实验次数**: 20
- **耗时**: 0.00 秒

## 优化建议

1. **应用配置**: 将上述最优参数应用到 灵族成员 的 Proxy 路由配置
2. **监控效果**: 观察 Token 使用量、响应时间、成功率的变化
3. **定期优化**: 每周或每月重新运行优化以适应业务变化
4. **A/B 测试**: 在生产环境中进行 A/B 测试验证效果

---

*由 lingminopt (灵极优) 自动生成*