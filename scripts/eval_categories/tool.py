TOOL_TESTS = [
    {"id":"TOOL_01","cat":"工具调用","name":"CSV读取","level":"fast",
     "prompt":"如何用Python读取CSV文件？",
     "eval":lambda c: 1.0 if "pandas" in c.lower() or "csv" in c.lower() or "read_csv" in c else 0.0},
    {"id":"TOOL_02","cat":"工具调用","name":"JSON处理","level":"fast",
     "prompt":"如何用Python解析JSON字符串？",
     "eval":lambda c: 1.0 if "json.loads" in c or "json.load" in c or ("json" in c and "parse" in c.lower()) else 0.5 if "json" in c.lower() else 0.0},
    {"id":"TOOL_03","cat":"工具调用","name":"HTTP请求","level":"fast",
     "prompt":"如何用Python发送HTTP GET请求？",
     "eval":lambda c: 1.0 if "requests.get" in c or "urllib" in c or "httpx" in c else 0.5 if "requests" in c or "http" in c.lower() else 0.0},
    {"id":"TOOL_04","cat":"工具调用","name":"SQL注入识别","level":"normal",
     "prompt":"以下SQL语句不安全吗？为什么？\nquery = f\"SELECT * FROM users WHERE id = {user_input}\"",
     "eval":lambda c: 1.0 if any(k in c for k in ["SQL注入","注入","拼接","危险","不安全","参数化"]) else 0.5 if any(k in c for k in ["SQL","query","注入"]) else 0.0},
]
