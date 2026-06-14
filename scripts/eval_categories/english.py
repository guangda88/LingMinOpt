EN_TESTS = [
    {"id":"EN_01","cat":"英文能力","name":"中译英","level":"fast",
     "prompt":"Translate to English: 这个系统使用微服务架构。",
     "eval":lambda c: 1.0 if "microservice" in c.lower() or "micro-service" in c.lower() else 0.0},
    {"id":"EN_02","cat":"英文能力","name":"Python概念","level":"fast",
     "prompt":"What is the difference between a list and a tuple in Python?",
     "eval":lambda c: 1.0 if ("mutable" in c.lower() or "immutable" in c.lower() or "可变" in c) and ("list" in c.lower() and "tuple" in c.lower()) else 0.5 if "list" in c.lower() and "tuple" in c.lower() else 0.0},
    {"id":"EN_03","cat":"英文能力","name":"Git概念","level":"fast",
     "prompt":"What does git rebase do?",
     "eval":lambda c: 1.0 if any(k in c.lower() for k in ["rebase","base","commit","branch","history","apply","rewrite"]) else 0.0},
]
