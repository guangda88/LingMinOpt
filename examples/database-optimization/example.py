"""
示例：数据库查询优化

使用 LingMinOpt 优化数据库查询性能。

目标：最大化查询吞吐量（QPS）
"""

import sys
sys.path.insert(0, '/home/ai/LingMinOpt')

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
import time
import random


# ============================================================================
# 数据库模拟（不可修改）
# ============================================================================
class SimulatedDatabase:
    """模拟数据库"""

    def __init__(self):
        """初始化模拟数据库"""
        self.data = []
        self.indexes = {}
        self.cache = {}
        self.cache_policy = None
        self.cache_size = 100
        self.connection_pool = 10

        # 生成模拟数据
        self._generate_data(10000)

    def _generate_data(self, num_rows):
        """生成模拟数据"""
        self.data = []
        for i in range(num_rows):
            row = {
                "id": i,
                "category": random.choice(["A", "B", "C", "D", "E"]),
                "value": random.randint(1, 100),
                "timestamp": random.randint(1600000000, 1700000000),
                "priority": random.choice([1, 2, 3, 4, 5])
            }
            self.data.append(row)

    def add_index(self, index_type, columns):
        """
        添加索引

        Args:
            index_type: 索引类型
            columns: 索引列
        """
        key = (index_type, tuple(columns))

        if key not in self.indexes:
            self.indexes[key] = {}

            # 构建索引
            for row in self.data:
                index_key = tuple(row[col] for col in columns)
                if index_key not in self.indexes[key]:
                    self.indexes[key][index_key] = []
                self.indexes[key][index_key].append(row)

    def configure_cache(self, policy, size):
        """
        配置缓存

        Args:
            policy: 缓存策略
            size: 缓存大小
        """
        self.cache_policy = policy
        self.cache_size = size
        self.cache = {}

    def configure_connection_pool(self, size):
        """
        配置连接池

        Args:
            size: 连接池大小
        """
        self.connection_pool = size

    def _check_cache(self, query_key):
        """检查缓存"""
        if query_key in self.cache:
            if self.cache_policy == "lru":
                # 更新使用时间
                self.cache[query_key]["last_used"] = time.time()
            return True
        return False

    def _add_to_cache(self, query_key, result):
        """添加到缓存"""
        # 检查缓存是否已满
        if len(self.cache) >= self.cache_size:
            # 根据策略删除
            if self.cache_policy == "lru":
                # 删除最近最少使用的
                lru_key = min(self.cache.keys(), key=lambda k: self.cache[k]["last_used"])
                del self.cache[lru_key]
            elif self.cache_policy == "lfu":
                # 删除使用频率最低的
                lfu_key = min(self.cache.keys(), key=lambda k: self.cache[k]["use_count"])
                del self.cache[lfu_key]

        # 添加新项
        self.cache[query_key] = {
            "result": result,
            "last_used": time.time(),
            "use_count": 0
        }

    def execute_query(self, query):
        """
        执行查询

        Args:
            query: 查询条件

        Returns:
            查询结果
        """
        # 检查缓存
        query_key = str(query)
        if self._check_cache(query_key):
            self.cache[query_key]["use_count"] += 1
            return self.cache[query_key]["result"]

        # 执行查询
        result = []
        for row in self.data:
            match = True
            for key, value in query.items():
                if row.get(key) != value:
                    match = False
                    break

            if match:
                result.append(row)

        # 添加到缓存
        self._add_to_cache(query_key, result)

        return result


# ============================================================================
# 基准测试（不可修改）
# ============================================================================
def run_benchmark(db, queries, duration=30.0):
    """
    运行基准测试

    Args:
        db: 数据库实例
        queries: 查询列表
        duration: 测试持续时间（秒）

    Returns:
        dict: 性能指标
    """
    start_time = time.time()
    end_time = start_time + duration

    query_count = 0
    cache_hits = 0
    latencies = []

    while time.time() < end_time:
        # 随机选择查询
        query = random.choice(queries)

        # 执行查询
        query_start = time.time()
        result = db.execute_query(query)
        query_end = time.time()

        query_count += 1
        latency = query_end - query_start
        latencies.append(latency)

        # 检查是否命中缓存
        if str(query) in db.cache:
            cache_hits += 1

    # 计算指标
    total_time = time.time() - start_time
    qps = query_count / total_time
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    cache_hit_rate = cache_hits / query_count if query_count > 0 else 0

    return {
        "qps": qps,
        "avg_latency": avg_latency,
        "cache_hit_rate": cache_hit_rate,
        "query_count": query_count
    }


# ============================================================================
# 优化实验
# ============================================================================
# 创建基准查询集
benchmark_queries = [
    {"category": "A"},
    {"category": "B"},
    {"priority": 1},
    {"priority": 2},
    {"category": "A", "priority": 1},
    {"category": "B", "priority": 2},
    {"value": 50},
    {"priority": 3, "category": "C"},
]


# 定义搜索空间
search_space = SearchSpace()

# 索引配置
search_space.add_discrete("index_type", ["none", "btree", "hash"])
search_space.add_discrete("index_columns", [
    ["category"],
    ["priority"],
    ["category", "priority"],
    ["value"]
])

# 缓存配置
search_space.add_discrete("cache_policy", ["lru", "lfu"])
search_space.add_continuous("cache_size", 50, 200)

# 连接池配置
search_space.add_continuous("pool_size", 5, 20)


def run_experiment(params):
    """
    运行实验：评估数据库配置

    Args:
        params: 配置参数

    Returns:
        float: QPS（越高越好）
    """
    # 创建数据库实例
    db = SimulatedDatabase()

    # 配置索引
    index_type = params["index_type"]
    index_columns = params["index_columns"]

    if index_type != "none":
        db.add_index(index_type, index_columns)

    # 配置缓存
    cache_policy = params["cache_policy"]
    cache_size = int(params["cache_size"])
    db.configure_cache(cache_policy, cache_size)

    # 配置连接池
    pool_size = int(params["pool_size"])
    db.configure_connection_pool(pool_size)

    # 运行基准测试
    metrics = run_benchmark(db, benchmark_queries, duration=10.0)

    # 返回 QPS（越高越好）
    return metrics["qps"]


# ============================================================================
# 主程序
# ============================================================================
def main():
    """主函数"""
    print()
    print("=" * 70)
    print("数据库查询优化示例")
    print("=" * 70)
    print()

    # 配置优化器
    config = ExperimentConfig(
        max_experiments=30,
        improvement_threshold=5.0,
        time_budget=30.0,  # 每个实验最多 30 秒
        direction="maximize",  # 最大化 QPS
        random_seed=42
    )

    # 创建优化器
    optimizer = MinimalOptimizer(
        evaluate=run_experiment,
        search_space=search_space,
        config=config,
        search_strategy="random",
        seed=42
    )

    # 运行优化
    print("开始优化...")
    print(f"搜索空间: {len(search_space)} 个参数")
    print(f"最大实验次数: {config.max_experiments}")
    print()

    result = optimizer.run()

    # 打印结果
    print()
    print("=" * 70)
    print("优化结果")
    print("=" * 70)
    print()
    print(f"最佳 QPS: {result.best_score:.2f}")
    print(f"最佳配置:")
    for key, value in result.best_params.items():
        print(f"  {key}: {value}")
    print()
    print(f"总实验次数: {result.total_experiments}")
    print(f"总时间: {result.total_time:.2f} 秒")
    print(f"改进: {result.improvement:.2f} QPS")
    print()

    # 使用最佳配置进行详细测试
    print("=" * 70)
    print("详细测试")
    print("=" * 70)
    print()

    # 使用最佳配置
    db = SimulatedDatabase()

    index_type = result.best_params["index_type"]
    index_columns = result.best_params["index_columns"]
    if index_type != "none":
        db.add_index(index_type, index_columns)

    db.configure_cache(
        result.best_params["cache_policy"],
        int(result.best_params["cache_size"])
    )
    db.configure_connection_pool(int(result.best_params["pool_size"]))

    # 运行更长的基准测试
    metrics = run_benchmark(db, benchmark_queries, duration=30.0)

    print("性能指标:")
    print(f"  QPS: {metrics['qps']:.2f}")
    print(f"  平均延迟: {metrics['avg_latency']*1000:.2f} ms")
    print(f"  缓存命中率: {metrics['cache_hit_rate']*100:.1f}%")
    print(f"  查询总数: {metrics['query_count']}")
    print()

    # 性能评估
    if metrics['qps'] > 1000:
        print("✓ 性能优秀")
    elif metrics['qps'] > 500:
        print("✓ 性能良好")
    else:
        print("✗ 性能一般，可能需要进一步优化")
    print()

    # 保存结果
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"database_optimization_results_{timestamp}.json"

    with open(result_file, 'w') as f:
        json.dump({
            "best_params": result.best_params,
            "best_qps": result.best_score,
            "improvement": result.improvement,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time,
            "detailed_metrics": metrics
        }, f, indent=2)

    print(f"结果已保存到: {result_file}")


if __name__ == "__main__":
    main()
