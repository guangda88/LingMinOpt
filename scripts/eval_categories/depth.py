DEPTH_TESTS = [
    {"id":"DEPTH_01","cat":"推理深度","name":"限流系统设计","level":"normal",
     "prompt":"设计一个限流系统，支持每秒1000个请求。你会怎么设计？",
     "eval":lambda c: 1.0 if any(k in c for k in ["令牌桶","token bucket","滑动窗口","sliding","计数器","counter","漏桶","leaky"]) else 0.5 if any(k in c for k in ["限流","rate","请求","队列"]) else 0.0},
    {"id":"DEPTH_02","cat":"推理深度","name":"红区治理","level":"normal",
     "prompt":"在灵族中，什么是红区操作？为什么需要审批机制？请详细解释。",
     "eval":lambda c: 1.0 if "红区" in c and any(k in c for k in ["审批","投票","治理","危险","删除","杀进程","guardrail"]) else 0.5 if "红区" in c else 0.0},
    {"id":"DEPTH_03","cat":"推理深度","name":"系统分析","level":"normal",
     "prompt":"从CAP定理的角度分析，为什么分布式数据库比单机数据库更难设计？",
     "eval":lambda c: 1.0 if any(k in c for k in ["一致性","可用性","分区","consistency","availability","partition","CAP"]) else 0.5 if any(k in c for k in ["分布","复杂","数据库"]) else 0.0},
]
