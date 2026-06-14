LONG_TESTS = [
    {"id":"LONG_01","cat":"长上下文","name":"信息复述","level":"fast",
     "prompt":"请记住这个信息：我们的项目名叫LingAI，部署在端口8101，使用Qwen2.5基座。现在请复述项目信息。",
     "eval":lambda c: 1.0 if "LingAI" in c and "8101" in c else 0.5 if "LingAI" in c else 0.0},
    {"id":"LONG_02","cat":"长上下文","name":"信息提取","level":"fast",
     "prompt":"一个系统包含3个模块：认证、路由、日志。认证模块在:8002，路由在:8765，日志在:8900。认证模块在哪个端口？",
     "eval":lambda c: 1.0 if "8002" in c else 0.0},
    {"id":"LONG_03","cat":"长上下文","name":"约束遵循","level":"fast",
     "prompt":"请用恰好3句话描述Python的优点。不要多也不要少。",
     "eval":lambda c: 1.0 if sum([c.count(p) for p in ["。","！","？"]]) == 3 or (c.count("\n") == 2 and len(c) < 300) else 0.5 if 2 <= sum([c.count(p) for p in ["。","！","？"]]) <= 4 else 0.0},
]
