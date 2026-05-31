# 元知识优化报告

**生成时间**: 2026-05-29 20:42:08

## 综合结果

- **综合得分**: 0.8301
- **总实验次数**: 60
- **总耗时**: 0.00 秒

## 提示词优化

- **model**: glm-5.1
- **temperature**: 0.5986
- **max_tokens**: 4096
- **system_prompt_template**: standard

- **最优得分**: 0.5791
- **实验次数**: 16
- **耗时**: 0.00 秒

## 路由优化

- **code_model**: llama-3.3-70b
- **debug_model**: qwen-plus
- **chat_model**: qwen-plus
- **routing_strategy**: cost_based

- **最优得分**: 1.0000
- **实验次数**: 16
- **耗时**: 0.00 秒

## 重试优化

- **primary_retry_limit**: 3
- **backoff_base**: 2.9606
- **backoff_max**: 46.0178
- **degraded_call_threshold**: 10
- **degraded_time_threshold**: 73.6327
- **degradation_strategy**: hybrid
- **fallback_model**: minimax-m2.7

- **最优得分**: 0.9113
- **实验次数**: 28
- **耗时**: 0.00 秒

## 优化建议

1. **应用配置**: 将上述最优参数应用到 lingclaude 配置文件
2. **监控效果**: 观察 Token 使用量、响应时间、成功率的变化
3. **定期优化**: 每周或每月重新运行优化以适应业务变化
4. **A/B 测试**: 在生产环境中进行 A/B 测试验证效果

---

*由 lingminopt (灵极优) 自动生成*