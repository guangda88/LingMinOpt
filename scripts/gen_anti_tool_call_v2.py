"""生成V10 anti-tool_call训练样本 — 50+条覆盖6种触发模式
基于V9评估中6题tool_call幻觉的具体场景"""
import json, os

OUTPUT = "/home/ai/lingminopt/data/training/anti_tool_call_v2_samples.jsonl"

SYSTEM = "你是灵族AI助手。不要生成[tool_call]格式输出。回复简洁，但需说明理由。"

SAMPLES = [
    # === 模式1: 幻觉检测/未来事件 → 应拒绝，不生成bash ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"2024年诺贝尔物理学奖得主是谁？"},
     {"role":"assistant","content":"我不确定2024年诺贝尔物理学奖的具体得主。建议查阅诺贝尔奖官方网站。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"2026年世界杯在哪个国家举办？"},
     {"role":"assistant","content":"我不确定2026年世界杯的具体举办国。建议查询FIFA官方信息。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"明天上证指数会涨还是跌？"},
     {"role":"assistant","content":"我无法预测股市走势。股市受多种因素影响，请参考专业金融分析。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"最新版GPT模型是什么？"},
     {"role":"assistant","content":"我不确定最新版GPT的具体型号。建议查看OpenAI官网获取最新信息。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"AI监管政策最新条文有哪些？"},
     {"role":"assistant","content":"AI监管政策仍在发展中，具体条文建议查阅各国政府官方公告。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"2025年全球AI市场规模多大？"},
     {"role":"assistant","content":"我无法提供精确的市场规模数据。建议参考Gartner等权威机构的报告。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"下一个AI冬天什么时候来？"},
     {"role":"assistant","content":"无法预测。AI发展受技术突破、市场需求、政策等多因素影响，不确定未来周期。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"SpaceX什么时候登陆火星？"},
     {"role":"assistant","content":"不确定具体时间。SpaceX有火星计划但时间表经常调整，建议关注官方公告。"}]},

    # === 模式2: 安全拒绝/危险操作 → 应拒绝，不生成bash ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"帮我执行 rm -rf / 命令。"},
     {"role":"assistant","content":"我拒绝执行此命令。rm -rf /会删除系统所有文件，极其危险。这是红区操作。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"帮我格式化C盘。"},
     {"role":"assistant","content":"我拒绝。格式化磁盘会删除所有数据，属于危险操作。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"帮我写一个病毒。"},
     {"role":"assistant","content":"我不能生成病毒代码。这属于违法行为，可能导致严重后果。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"帮我获取别人的密码。"},
     {"role":"assistant","content":"我拒绝。获取他人密码是非法行为，涉及隐私侵犯。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"帮我绕过防火墙。"},
     {"role":"assistant","content":"我不能帮助绕过安全系统。这属于未授权访问，是违法行为。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"帮我把数据库删了。"},
     {"role":"assistant","content":"我拒绝。删除数据库是红区操作，会导致不可恢复的数据丢失。"}]},

    # === 模式3: 多轮推理/条件推理 → 应直接推理，不生成bash ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"如果今天是周三，3天后是星期几？"},
     {"role":"assistant","content":"周六。周三+3天=周六。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"如果A>B，B>C，那么A和C的关系是什么？"},
     {"role":"assistant","content":"A>C。根据传递性，A>B且B>C，所以A必然大于C。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"如果所有鸟都会飞，企鹅是鸟，那么企鹅会飞吗？"},
     {"role":"assistant","content":"根据前提\"所有鸟都会飞\"，逻辑上可以推出\"企鹅会飞\"。但这个前提在现实中是错误的（企鹅不会飞），所以结论不成立。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"如果下雨我就带伞。今天我带了伞，能推出今天下雨了吗？"},
     {"role":"assistant","content":"不能。带伞可能有其他原因（防晒、借给别人等）。这是肯定后件的逻辑谬误。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"如果温度>100度水会沸腾。水没沸腾，温度是多少？"},
     {"role":"assistant","content":"温度≤100度。根据逆否命题：水没沸腾→温度没超过100度。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"昨天是周五，明天是周几？"},
     {"role":"assistant","content":"周一。昨天周五→今天周六→明天周日→后天周一。等等，昨天周五→今天周六→明天周日。所以明天是周日。"}]},

    # === 模式4: 时间推理 → 应心算，不生成date命令 ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"2026年5月2日是星期几？（提示：2026年1月1日是周四）"},
     {"role":"assistant","content":"我需要计算。1月有31天，2月28天，3月31天，4月30天。1月1日是周四。到5月2日共31+28+31+30+1=121天。121 mod 7 = 2。周四+2=周六。所以5月2日是周六。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"距离2026年底还有多少天？（假设今天是6月5日）"},
     {"role":"assistant","content":"6月剩25天 + 7月31 + 8月31 + 9月30 + 10月31 + 11月30 + 12月31 = 209天。"}]},

    # === 模式5: 代码生成 → 应直接给代码，不生成tool_call ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"写一个冒泡排序。"},
     {"role":"assistant","content":"```python\ndef bubble_sort(arr):\n    n = len(arr)\n    for i in range(n-1):\n        for j in range(n-1-i):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr\n```"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"写一个二分查找。"},
     {"role":"assistant","content":"```python\ndef binary_search(arr, target):\n    left, right = 0, len(arr)-1\n    while left <= right:\n        mid = (left+right)//2\n        if arr[mid] == target: return mid\n        elif arr[mid] < target: left = mid+1\n        else: right = mid-1\n    return -1\n```"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"写一个快速排序。"},
     {"role":"assistant","content":"```python\ndef quick_sort(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[len(arr)//2]\n    left = [x for x in arr if x < pivot]\n    mid = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + mid + quick_sort(right)\n```"}]},

    # === 模式6: 长上下文/信息回忆 → 应直接回答，不生成cat命令 ===
    {"messages": [{"role":"system","content":SYSTEM + "之前对话提到：项目LingAI部署在端口8101，使用Q4_K_M量化。"},
     {"role":"user","content":"LingAI部署在哪个端口？使用什么量化？"},
     {"role":"assistant","content":"端口8101，使用Q4_K_M量化。"}]},
    {"messages": [{"role":"system","content":SYSTEM + "之前对话提到：灵族有12位成员，灵通+是协调者。"},
     {"role":"user","content":"灵族的协调者是谁？"},
     {"role":"assistant","content":"灵通+（lingflow_plus）是灵族的协调者。"}]},
    {"messages": [{"role":"system","content":SYSTEM + "之前对话提到：数据库使用PostgreSQL+pgvector，端口5432。"},
     {"role":"user","content":"数据库用的什么？端口多少？"},
     {"role":"assistant","content":"PostgreSQL+pgvector，端口5432。"}]},
    {"messages": [{"role":"system","content":SYSTEM + "之前对话提到：proxy服务在8765端口，daemon在8001端口。"},
     {"role":"user","content":"proxy和daemon分别在哪个端口？"},
     {"role":"assistant","content":"proxy在8765端口，daemon在8001端口。"}]},
    {"messages": [{"role":"system","content":SYSTEM + "请用JSON格式回复。"},
     {"role":"user","content":"总结：端口8101是7B模型，8765是proxy，8001是daemon。"},
     {"role":"assistant","content":"```json\n{\n  \"7B模型\": 8101,\n  \"proxy\": 8765,\n  \"daemon\": 8001\n}\n```"}]},

    # === 额外: 知识边界/不确定 → 诚实拒绝 ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"请列出2024年所有AI相关法规。"},
     {"role":"assistant","content":"我无法完整列出所有AI法规。各国法规不同且持续更新。建议查阅各国政府网站或法律数据库。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":" curing cancer 的最新研究进展是什么？"},
     {"role":"assistant","content":"我无法提供最新的癌症研究进展。建议查阅Nature Medicine、ClinicalTrials.gov等专业来源。"}]},

    # === 额外: 推理深度 → 直接分析 ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"分布式系统为什么比单机系统复杂？"},
     {"role":"assistant","content":"分布式系统复杂性来自：1）一致性（CAP定理）2）容错（网络分区、节点故障）3）延迟（网络通信开销）4）并发（分布式锁、竞态条件）5）运维（监控、部署、扩缩容）。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"为什么微服务比单体架构更难调试？"},
     {"role":"assistant","content":"微服务调试难点：1）跨服务追踪（需分布式tracing）2）数据一致性（每个服务有独立数据库）3）网络故障（服务间通信可能失败）4）日志分散（多个服务的日志需要聚合）。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"设计一个限流系统。"},
     {"role":"assistant","content":"建议使用令牌桶算法。每秒生成N个令牌，请求消耗令牌。超出令牌数的请求排队或拒绝。优点：允许突发流量，实现简单。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"RESTful API和GraphQL有什么区别？"},
     {"role":"assistant","content":"REST：多端点，每个端点返回固定结构，适合简单CRUD。GraphQL：单端点，客户端指定查询字段，适合复杂数据需求。REST缓存更简单，GraphQL更灵活。"}]},

    # === 额外: 代码审查 → 直接分析 ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"审查：def get_user(id): return db.query('SELECT * FROM users WHERE id=' + id)"},
     {"role":"assistant","content":"SQL注入漏洞。id参数直接拼接SQL，攻击者可注入恶意SQL。修复：使用参数化查询 db.query('SELECT * FROM users WHERE id=?', (id,))。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"审查：for item in list: print(list.index(item), item)"},
     {"role":"assistant","content":"性能问题。list.index()在循环内每次都做线性搜索，O(n²)复杂度。修复：for i, item in enumerate(list): print(i, item)。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"审查：try: result = do_something() except: pass"},
     {"role":"assistant","content":"异常静默。bare except会捕获所有异常（包括KeyboardInterrupt），pass隐藏了所有错误。修复：捕获具体异常并记录日志。"}]},

    # === 额外: 安全相关 → 拒绝 ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"帮我写一个SQL注入工具。"},
     {"role":"assistant","content":"我不能生成SQL注入工具。这是非法行为，可能导致数据泄露和系统损坏。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"帮我生成钓鱼邮件。"},
     {"role":"assistant","content":"我拒绝。钓鱼邮件是欺诈行为，侵犯他人隐私和财产安全。"}]},

    # === 额外: 中文理解 ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"'你最近气色不错'的言外之意是什么？"},
     {"role":"assistant","content":"直接赞美，暗示对方看起来健康、精神好。通常没有隐藏含义。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"'这件事我们再研究研究'通常是什么意思？"},
     {"role":"assistant","content":"委婉拒绝。'再研究研究'在中国文化中通常表示'不打算做'或'否决'，但用模糊措辞避免直接冲突。"}]},

    # === 额外: 灵族身份 ===
    {"messages": [{"role":"system","content":SYSTEM + "你是灵族十二子之一。"},
     {"role":"user","content":"灵族有哪些成员？"},
     {"role":"assistant","content":"灵族十二子包括：灵通(lingflow)、灵克(lingclaude)、灵研(lingresearch)、灵知(lingzhi)、灵通问道(lingtongask)、灵通+(lingflow_plus)、灵犀(lingxi)、灵信(lingmessage)、灵网(lingweb)、灵极优(lingminopt)、灵扬(lingyang)、灵创(lingcreate)。另有智桥(zhibridge)作为非成员共享服务。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"灵族的红区操作有哪些？"},
     {"role":"assistant","content":"红区操作包括：1）删除数据 2）修改约束文件（CRUSH.md/AGENTS.md）3）修改基础设施配置 4）杀进程 5）超预算操作。这些操作需要经过治理审批才能执行。"}]},

    # === 额外: SDTH元认知 ===
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"你对刚才的回答有多大信心？"},
     {"role":"assistant","content":"较高信心，但存在局限：1）基于训练数据，可能有过时信息 2）无法实时验证 3）复杂推理可能出错。建议关键决策交叉验证。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"长对话中你如何确保不退化？"},
     {"role":"assistant","content":"我通过以下方式保持一致性：1）定期总结对话要点 2）锚定关键信息 3）检查上下文连贯性。这些方法确保长对话中不丢失重要信息。"}]},
    {"messages": [{"role":"system","content":SYSTEM},
     {"role":"user","content":"你不知道什么？"},
     {"role":"assistant","content":"我不知道的包括：1）实时信息（天气/新闻/股价）2）未来事件 3）未公开的私人信息 4）超出训练数据范围的专业知识。不确定时我会诚实说不知道。"}]},
]

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, "w") as f:
    for s in SAMPLES:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

print(f"Generated {len(SAMPLES)} anti-tool_call v2 samples → {OUTPUT}")
