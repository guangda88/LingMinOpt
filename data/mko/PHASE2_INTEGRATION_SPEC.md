# MKO Phase 2 集成规范 — lingminopt → lingflow_plus

> 生成时间: 2026-05-31
> 灵极优交付，灵通+执行

## 概述

将 MKO 优化结果导入 proxy，实现 per-caller 路由 + max_tokens 限制。

## 输入文件

`/home/ai/lingminopt/data/mko/lingflowplus_member_routing.json`

格式：
```json
{
  "lingflow": {
    "total_tokens": 863759,
    "percentage": 11.5,
    "recommended": {
      "code_model": "glm-5.1",
      "chat_model": "qwen-plus",
      "max_tokens": 4096
    },
    "action": "max_tokens限制 + 非code路由qwen-plus"
  },
  ...
}
```

## 集成点（3处改动）

### 1. purpose_router.py — per-caller 路由覆盖

在 `classify()` 方法中，当 `caller` 匹配 MKO 配置时：
- 如果关键词分类结果不是 `coding`/`thinking` 等高资源路由
- 且 MKO 建议的 `chat_model` 与默认不同
- 则返回 MKO 建议的 chat_model 对应的路由

```python
# purpose_router.py 顶部加
_MKO_CONFIG_PATH = Path.home() / "lingminopt" / "data" / "mko" / "lingflowplus_member_routing.json"
_mko_config: dict | None = None
_mko_config_mtime: float = 0.0

def _load_mko_config() -> dict:
    global _mko_config, _mko_config_mtime
    try:
        if _MKO_CONFIG_PATH.exists() and _MKO_CONFIG_PATH.stat().st_mtime > _mko_config_mtime:
            _mko_config = json.loads(_MKO_CONFIG_PATH.read_text())
            _mko_config_mtime = _MKO_CONFIG_PATH.stat().st_mtime
    except Exception:
        pass
    return _mko_config or {}
```

在 `classify()` 返回前加 MKO 覆盖：
```python
# MKO per-caller override
mko = _load_mko_config()
if caller:
    caller_lower = caller.lower().replace("-", "").replace("_", "").replace("+", "plus")
    member_cfg = mko.get(caller_lower)
    if member_cfg:
        rec = member_cfg.get("recommended", {})
        chat_model = rec.get("chat_model", "")
        max_tokens = rec.get("max_tokens", 4096)
        # 如果不是 coding 类路由，且 chat_model 不同，使用更轻量的路由
        if route_key not in ("coding", "thinking", "model_direct") and chat_model:
            # 映射 chat_model 到路由 key
            # qwen-plus → fast_response 或 chinese_reasoning
            # glm-4.7-flash → fast_response
            pass  # 灵通+根据实际 task_routes 映射
return route_key
```

### 2. proxy.py — max_tokens 限制

在 `chat()` 和 `chat_stream()` 中，调用 provider 前检查 MKO max_tokens：

```python
# 在 _resolve_candidates() 或 _try_provider() 中
mko = _load_mko_config()  # 可复用 purpose_router 的加载
caller_lower = caller.lower().replace("-", "").replace("_", "").replace("+", "plus")
member_cfg = mko.get(caller_lower, {})
rec = member_cfg.get("recommended", {})
mko_max = rec.get("max_tokens", None)
if mko_max and max_tokens > mko_max:
    max_tokens = mko_max
    logger.info("[mko] caller=%s max_tokens capped to %d", caller, max_tokens)
```

### 3. proxy.py — 高消耗成员模型降级

对 `percentage > 10` 的成员（灵知25.3%、灵通问道15.6%、灵通11.5%、灵克11.6%、灵扬10.5%）：
- 非工具调用场景自动使用更经济的模型
- 代码任务保持 glm-5.1，聊天/简单问答降级到 glm-4.7-flash 或 qwen-plus

## 验证方法

1. 修改后启动 proxy，发送测试请求：
   ```bash
   # 灵知请求（应触发 max_tokens=2048）
   curl -H "X-Caller: lingzhi" http://localhost:8765/v1/chat/completions \
     -d '{"messages":[{"role":"user","content":"你好"}],"max_tokens":8192}'
   ```
2. 检查 proxy 日志中 `[mko]` 前缀的条目
3. 对比修改前后各成员的 token 消耗趋势

## 注意事项

- MKO 配置文件由灵极优 `lingminopt mko --type all` 生成
- 文件变更通过 mtime 检测自动热加载，无需重启 proxy
- 灵知(out/in=10.1x)是最高优先级目标，当前无输出截断导致大量 token 浪费
- `max_tokens` 是硬限制，不会截断正在进行的重要输出，但会阻止冗长生成的尾部
