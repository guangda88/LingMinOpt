# 元知识优化报告 — 灵族

**生成时间**: 2026-05-30 00:31:06
**数据来源**: 灵族crush.db + LingBus

## 按成员Token消耗排名

| 成员 | 总Token | 占比 | 输出/输入比 | 工具调用 | 优先级 |
|------|---------|------|-------------|----------|--------|
| lingzhi | 1,896,005 | 25.2% | 10.1x | 21,273 | 高优 |
| lingtongask | 1,200,629 | 16.0% | 5.4x | 11,448 | 高优 |
| lingflow | 879,396 | 11.7% | 3.0x | 15,348 | 高优 |
| lingclaude | 804,376 | 10.7% | 3.9x | 12,725 | 高优 |
| lingyang | 786,236 | 10.5% | 1.3x | 11,009 | 高优 |
| lingresearch | 652,040 | 8.7% | 3.4x | 14,123 | 中优 |
| lingcreate | 485,257 | 6.5% | 0.1x | 1,737 | 中优 |
| lingweb | 362,957 | 4.8% | 6.1x | 6,886 | 低优 |
| lingmessage | 139,285 | 1.9% | 9.7x | 2,340 | 低优 |
| lingxi | 138,350 | 1.8% | 7.1x | 2,886 | 低优 |
| lingminopt | 101,392 | 1.3% | 7.3x | 2,415 | 低优 |
| zhibridge | 57,427 | 0.8% | 7.6x | 1,492 | 低优 |
| lingflowplus | 19,836 | 0.3% | 18.5x | 620 | 低优 |

## 提示词优化

- **model**: glm-5.1
- **temperature**: 0.6122
- **max_tokens**: 2048
- **system_prompt_template**: minimal

## 路由优化

- **code_model**: glm-5.1
- **debug_model**: qwen-plus
- **chat_model**: glm-4.7-flash
- **routing_strategy**: cost_based

## 重试优化

- **primary_retry_limit**: 5
- **backoff_base**: 1.2296
- **backoff_max**: 34.6991
- **degraded_call_threshold**: 20
- **degraded_time_threshold**: 42.4500
- **degradation_strategy**: timeout_increase
- **fallback_model**: llama-3.3-70b

## 优化建议

1. **应用配置**: 将上述最优参数应用到 灵族 的 Proxy 路由配置
2. **监控效果**: 观察 Token 使用量、响应时间、成功率的变化
3. **定期优化**: 每周或每月重新运行优化以适应业务变化
4. **A/B 测试**: 在生产环境中进行 A/B 测试验证效果

---

*由 lingminopt (灵极优) 自动生成*