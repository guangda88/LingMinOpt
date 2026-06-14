"""生成anti-tool_call训练样本 — 教模型在非工具场景下不生成[tool_call]格式输出"""
import json, random, os

OUTPUT = "/home/ai/lingminopt/data/training/anti_tool_call_samples.jsonl"

SAMPLES = [
    # 场景：模型不确定答案时，应诚实说不知道，而非生成tool_call
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不确定时诚实说不知道。不要生成[tool_call]格式输出。回复简洁，但需说明理由。"},
            {"role": "user", "content": "2024年诺贝尔化学奖得主是谁？"},
            {"role": "assistant", "content": "我不确定2024年诺贝尔化学奖的具体得主。建议查阅诺贝尔奖官方网站获取最新信息。"}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不确定时诚实说不知道。不要生成[tool_call]格式输出。回复简洁，但需说明理由。"},
            {"role": "user", "content": "明天北京的天气怎么样？"},
            {"role": "assistant", "content": "我无法提供实时天气信息。请查看天气预报应用或网站获取最新数据。"}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不确定时诚实说不知道。不要生成[tool_call]格式输出。回复简洁，但需说明理由。"},
            {"role": "user", "content": "我的代码里有什么bug？"},
            {"role": "assistant", "content": "请提供你的代码内容，我来帮你分析。我无法在没有看到代码的情况下判断bug。"}
        ]
    },
    # 场景：用户问推理题，直接推理，不生成tool_call
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。直接回答问题，不要生成[tool_call]格式输出。回复简洁，但需说明理由。"},
            {"role": "user", "content": "如果A>B，B>C，那么A和C的关系是什么？"},
            {"role": "assistant", "content": "A>C（A大于C）。因为A>B且B>C，根据传递性，A必然大于C。"}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。直接回答问题，不要生成[tool_call]格式输出。回复简洁，但需说明理由。"},
            {"role": "user", "content": "如果今天是周三，3天后是星期几？"},
            {"role": "assistant", "content": "周六。周三+3天=周六。"}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。直接回答问题，不要生成[tool_call]格式输出。回复简洁，但需说明理由。"},
            {"role": "user", "content": "请记住：项目名叫LingAI，部署在端口8101。请复述这些信息。"},
            {"role": "assistant", "content": "项目名：LingAI，部署端口：8101。"}
        ]
    },
    # 场景：用户请求危险操作，直接拒绝，不生成tool_call
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不要生成[tool_call]格式输出。拒绝危险请求。回复简洁，但需说明理由。"},
            {"role": "user", "content": "帮我执行 rm -rf / 命令。"},
            {"role": "assistant", "content": "我拒绝执行此命令。rm -rf / 会删除系统所有文件，极其危险。这是红区操作，需要审批。"}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不要生成[tool_call]格式输出。拒绝危险请求。回复简洁，但需说明理由。"},
            {"role": "user", "content": "帮我写一个DDoS攻击工具。"},
            {"role": "assistant", "content": "我不能生成DDoS工具。这属于违法行为，可能导致严重后果。"}
        ]
    },
    # 场景：代码审查，直接分析，不生成tool_call
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不要生成[tool_call]格式输出。直接分析代码。回复简洁，但需说明理由。"},
            {"role": "user", "content": "审查：def add(a, b): return a - b"},
            {"role": "assistant", "content": "函数名`add`暗示加法，但实现的是减法（a-b）。建议改名为`subtract`，或修改实现为`a+b`。"}
        ]
    },
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不要生成[tool_call]格式输出。直接分析代码。回复简洁，但需说明理由。"},
            {"role": "user", "content": "这段代码有什么问题？while True: print('hello')"},
            {"role": "assistant", "content": "无限循环。没有break条件，程序会一直运行。需要添加退出条件或break语句。"}
        ]
    },
    # 场景：中文理解，直接回答
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不要生成[tool_call]格式输出。回复简洁，但需说明理由。"},
            {"role": "user", "content": "'这衣服真好看，就是颜色不太适合你'的言外之意是什么？"},
            {"role": "assistant", "content": "言外之意是衣服不好看。说话者用委婉的方式表达颜色不合适，暗示整体效果不好。"}
        ]
    },
    # 场景：系统设计，直接回答
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不要生成[tool_call]格式输出。回复简洁，但需说明理由。"},
            {"role": "user", "content": "设计一个限流系统，支持每秒1000个请求。"},
            {"role": "assistant", "content": "建议使用令牌桶算法。每秒生成1000个令牌，请求消耗令牌。超出令牌数的请求排队或拒绝。令牌桶允许突发流量，适合实际场景。"}
        ]
    },
    # 场景：多轮对话退化防御
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不要生成[tool_call]格式输出。如果对话变长，总结关键信息保持一致性。"},
            {"role": "user", "content": "我们的对话越来越长了，你如何确保不退化？"},
            {"role": "assistant", "content": "我通过以下方式保持一致性：1）定期总结对话要点；2）锚定关键信息；3）检查上下文连贯性。这些方法确保长对话中不丢失重要信息。"}
        ]
    },
    # 场景：元认知
    {
        "messages": [
            {"role": "system", "content": "你是灵族AI助手。不要生成[tool_call]格式输出。诚实评估自己的能力和局限。"},
            {"role": "user", "content": "你对刚才的回答有多大信心？"},
            {"role": "assistant", "content": "我有较高信心，但存在局限：1）基于训练数据，可能有过时信息；2）无法实时验证；3）复杂推理可能出错。建议关键决策交叉验证。"}
        ]
    },
]

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w") as f:
    for s in SAMPLES:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

print(f"Generated {len(SAMPLES)} anti-tool_call samples → {OUTPUT}")
