EDGE_TESTS = [
    {"id":"EDGE_01","cat":"边界条件","name":"权限检查","level":"fast",
     "prompt":"在执行文件删除前，应该检查哪些条件？",
     "eval":lambda c: 1.0 if any(k in c for k in ["权限","存在","路径","确认","检查"]) else 0.0},
    {"id":"EDGE_02","cat":"边界条件","name":"空输入处理","level":"fast",
     "prompt":"函数参数为None或空字符串时该怎么处理？",
     "eval":lambda c: 1.0 if any(k in c for k in ["检查","判断","None","空","默认","异常","抛出"]) else 0.0},
    {"id":"EDGE_03","cat":"边界条件","name":"超大输入","level":"fast",
     "prompt":"处理10GB文件时需要注意什么？",
     "eval":lambda c: 1.0 if any(k in c for k in ["分块","流式","内存","chunk","stream","缓冲"]) else 0.0},
    {"id":"EDGE_04","cat":"边界条件","name":"并发安全","level":"normal",
     "prompt":"多个线程同时写入同一个文件时，需要注意什么？",
     "eval":lambda c: 1.0 if any(k in c for k in ["锁","Lock","线程安全","互斥","Mutex","排队","同步"]) else 0.5 if any(k in c for k in ["线程","并发","冲突"]) else 0.0},
]
