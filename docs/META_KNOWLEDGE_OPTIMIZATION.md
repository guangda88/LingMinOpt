# 元知识优化 (MKO) — 实施记录

> **项目**: Meta Knowledge Optimizer (MKO)
> **负责方**: 灵极优 (lingminopt)
> **版本**: v2.0.0 (Phase 1 已交付)
> **日期**: 2026-05-29

---

## 一、Phase 1 交付成果

### 1.1 数据发现

灵族13成员总token消耗 **7.46M tokens**（2026-05-29快照）：

| 排名 | 成员 | Token | 占比 | 输出/输入比 | 问题类型 |
|------|------|-------|------|-------------|----------|
| 1 | 灵知 | 1,896,005 | 25.4% | 10.1x | 输出膨胀 |
| 2 | 灵通问道 | 1,197,238 | 16.0% | 5.4x | 输出膨胀 |
| 3 | 灵通 | 862,737 | 11.6% | 3.1x | 高输出 |
| 4 | 灵扬 | 785,643 | 10.5% | 1.3x | 均衡 |
| 5 | 灵克 | 781,944 | 10.5% | 3.9x | 高输出 |
| 6 | 灵研 | 642,262 | 8.6% | 3.4x | 中输出 |
| 7-13 | 其余6成员 | 1,297,054 | 17.4% | — | 低优先 |

**核心发现**：灵知输出/输入比10.1x，即每接收1个token就输出10个token——典型的输出膨胀。

### 1.2 优化建议

| 成员 | 建议路由 | max_tokens | 预估节省 |
|------|----------|------------|----------|
| 灵知 | code→glm-4.7-flash, chat→qwen-plus | 2048 | 61.5% |
| 灵通问道 | code→glm-4.7, chat→qwen-plus | 4096 | 44.0% |
| 灵通 | code→glm-5.1, chat→qwen-plus | 8192 | 23.5% |
| 灵克 | code→glm-5.1, chat→qwen-plus | 8192 | 23.5% |
| 灵扬 | code→glm-4.7-flash, chat→qwen-plus | 4096 | 53.0% |

**总计预估节省**: 2.5M tokens (33.5%)

### 1.3 优化器运行结果

基于LingBus 500条真实数据，30 trials × 3维度：

- **Prompt优化**: model=glm-5.1, temperature=0.54, max_tokens=16384, template=minimal → score 0.9724
- **Routing优化**: code=glm-5.1, debug=glm-5.1, chat=glm-4.7-flash, strategy=cost_based → score 1.0000
- **Retry优化**: retries=5, backoff=3.4, strategy=timeout_increase, fallback=qwen-max → score 0.8943

---

## 二、已实现的代码模块

| 文件 | 功能 | 状态 |
|------|------|------|
| `meta_optimizer/search_spaces.py` | 搜索空间定义（8个灵族真实模型） | ✅ |
| `meta_optimizer/evaluators.py` | 评估函数（token成本+质量+成功率） | ✅ |
| `meta_optimizer/lingbus_collector.py` | 数据收集（13个crush.db + LingBus） | ✅ |
| `meta_optimizer/optimizer.py` | 优化器封装 | ✅ |
| `meta_optimizer/report_generator.py` | 报告生成（MD/JSON/配置） | ✅ |
| `meta_optimizer/data_collector.py` | 原始lingclaude数据收集器 | ✅ |
| `meta_optimizer/feature_extractor.py` | 特征提取 | ✅ |
| `cli/meta_optimize.py` | CLI: `lingminopt mko` + `lingminopt meta-optimize` | ✅ |
| `mcp_server.py` | MCP: `mko_token_ranking` / `mko_run` / `mko_recommendations` | ✅ |

### CLI用法

```bash
lingminopt mko                    # 全部优化
lingminopt mko --type ranking     # 仅token排名
lingminopt mko --type prompt      # 仅提示词优化
lingminopt mko --type routing     # 仅路由优化
lingminopt mko --trials 50        # 更多尝试次数
```

### MCP工具

| 工具名 | 描述 |
|--------|------|
| `mko_token_ranking` | 灵族Token消耗排名+建议 |
| `mko_run` | 运行单维度MKO优化 |
| `mko_recommendations` | 综合三维度优化建议 |

---

## 三、搜索空间

### 3.1 Prompt优化

| 参数 | 候选值 |
|------|--------|
| model | glm-5.1, glm-5-turbo, glm-4.7, glm-4.7-flash, qwen-max, qwen-plus, minimax-m2.7, llama-3.3-70b |
| temperature | [0.0, 1.0] |
| max_tokens | 2048, 4096, 8192, 16384, 32768 |
| system_prompt_template | minimal, standard, detailed |

### 3.2 Routing优化

| 参数 | 候选值 |
|------|--------|
| code_model | glm-5.1, glm-4.7, qwen-max, llama-3.3-70b |
| debug_model | glm-5.1, glm-4.7-flash, qwen-plus |
| chat_model | glm-4.7-flash, qwen-plus, minimax-m2.7 |
| routing_strategy | intent_based, capability_based, cost_based, hybrid |

### 3.3 Retry优化

| 参数 | 范围 |
|------|------|
| primary_retry_limit | [1, 5] |
| backoff_base | [1.0, 10.0] |
| backoff_max | [10.0, 60.0] |
| degraded_call_threshold | [5, 20] |
| degraded_time_threshold | [30.0, 120.0] |
| degradation_strategy | model_downgrade, timeout_increase, hybrid |
| fallback_model | qwen-max, minimax-m2.7, llama-3.3-70b |

---

## 四、评估器设计

### PromptEvaluator

```
score = 0.4 × token_efficiency + 0.4 × quality + 0.2 × success_rate
```

- `token_efficiency`: 基于模型token乘数和模板乘数
- `quality`: 模型质量基线 × 温度因子
- `success_rate`: 历史成功率

模型token成本乘数（相对glm-5.1）：

| 模型 | 乘数 | 质量基线 |
|------|------|----------|
| glm-5.1 | 1.0 | 0.92 |
| glm-5-turbo | 0.75 | 0.85 |
| glm-4.7 | 0.85 | 0.88 |
| glm-4.7-flash | 0.6 | 0.78 |
| qwen-max | 0.8 | 0.87 |
| qwen-plus | 0.55 | 0.75 |
| minimax-m2.7 | 0.7 | 0.80 |
| llama-3.3-70b | 0.65 | 0.76 |

### RoutingEvaluator

```
score = 0.4 × latency_efficiency + 0.3 × cost_efficiency + 0.3 × success_rate
```

### RetryEvaluator

```
score = 0.5 × time_efficiency + 0.5 × final_success_rate
```

---

## 五、数据来源

### LingBusCollector

从两个数据源收集：

1. **crush.db**（13个成员）: `SELECT role, parts, created_at, model, provider FROM messages`
2. **LingBus**（消息总线）: `SELECT rowid, sender, recipient, subject, body, timestamp, channel FROM messages`

输出：`MemberSessionStats`（总量统计）+ `SessionRecord`（单条记录）

---

## 六、Phase 2 计划（需灵通+配合）

1. **路由配置导入**: `data/mko/routing_recommendations.json` → 灵通+ `proxy_app.py`
2. **max_tokens硬限制**: 为灵知(2048)、灵通问道(4096)设置输出上限
3. **A/B测试**: 对比优化前后的实际token消耗
4. **定期自动优化**: 接入灵通+daemon，每周运行一次MKO

---

*灵极优 (lingminopt) — 2026-05-29*
