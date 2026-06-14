def _make_eval_code(def_required, keyword_pass):
    def fn(content):
        c = content.lower()
        if def_required.lower() in c and any(k.lower() in c for k in keyword_pass):
            return 1.0
        elif def_required.lower() in c:
            return 0.5
        return 0.0
    return fn

GEN_TESTS = [
    {"id":"GEN_01","cat":"代码生成","name":"冒泡排序","level":"fast",
     "prompt":"写一个Python函数实现冒泡排序。",
     "eval":_make_eval_code("def", ["bubble","sort","冒泡","for"])},
    {"id":"GEN_02","cat":"代码生成","name":"字符串反转","level":"fast",
     "prompt":"写一个Python函数反转字符串。",
     "eval":_make_eval_code("def", ["[::-1]","reverse","reversed"])},
    {"id":"GEN_03","cat":"代码生成","name":"学生类","level":"fast",
     "prompt":"写一个Python类表示一个学生，包含姓名和成绩。",
     "eval":_make_eval_code("class", ["Student","学生","name","score","grade"])},
    {"id":"GEN_04","cat":"代码生成","name":"设计模式","level":"normal",
     "prompt":"用Python实现单例模式(Singleton)。",
     "eval":_make_eval_code("class", ["singleton","单例","_instance","__new__"])},
    {"id":"GEN_05","cat":"代码生成","name":"API设计","level":"normal",
     "prompt":"用Flask/FastAPI写一个简单的REST API，包含一个GET /hello端点。",
     "eval":lambda c: 1.0 if ("app" in c and "route" in c) or ("FastAPI" in c or "flask" in c.lower()) else 0.5 if "def " in c else 0.0},
]
