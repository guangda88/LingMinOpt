"""
示例：游戏策略优化

使用 LingMinOpt 优化简单的游戏 AI 策略。

目标：最大化胜率
"""

import sys
sys.path.insert(0, '/home/ai/LingMinOpt')

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
import numpy as np


# ============================================================================
# 游戏环境（不可修改）
# ============================================================================
class SimpleGame:
    """简单的游戏环境"""

    def __init__(self):
        """初始化游戏"""
        self.state = None
        self.history = []

    def reset(self):
        """重置游戏"""
        self.state = {
            "position": 0,  # 位置（-10 到 10）
            "energy": 100,  # 能量（0 到 100）
            "score": 0      # 分数
        }
        self.history = []

    def step(self, action, strategy_params):
        """
        执行一步动作

        Args:
            action: 动作（-1, 0, 1）
            strategy_params: 策略参数

        Returns:
            tuple: (reward, done)
        """
        # 提取策略参数
        aggression = strategy_params.get("aggression", 0.5)
        risk_tolerance = strategy_params.get("risk_tolerance", 0.5)

        # 更新位置
        self.state["position"] += action

        # 限制位置范围
        self.state["position"] = max(-10, min(10, self.state["position"]))

        # 能量消耗
        energy_cost = abs(action) * (1 + aggression * 0.5)
        self.state["energy"] -= energy_cost

        # 检查是否超出边界
        if abs(self.state["position"]) >= 10:
            # 惩罚
            reward = -10 * risk_tolerance
            done = True
        elif self.state["energy"] <= 0:
            # 能量耗尽
            reward = -5
            done = True
        else:
            # 获得奖励（越接近 0 越好）
            reward = -abs(self.state["position"]) * 0.1
            done = False

        # 偶尔奖励
        if np.random.random() < 0.05:
            reward += 2
            self.state["score"] += 2

        self.history.append({
            "position": self.state["position"],
            "energy": self.state["energy"],
            "action": action,
            "reward": reward
        })

        return reward, done


def run_episode(strategy, strategy_params, max_steps=100):
    """
    运行一局游戏

    Args:
        strategy: 策略函数
        strategy_params: 策略参数
        max_steps: 最大步数

    Returns:
        float: 总奖励
    """
    game = SimpleGame()
    game.reset()

    total_reward = 0.0

    for _ in range(max_steps):
        # 根据当前状态和策略选择动作
        action = strategy(game.state, strategy_params)

        # 执行动作
        reward, done = game.step(action, strategy_params)
        total_reward += reward

        if done:
            break

    return total_reward


# ============================================================================
# 策略定义（可修改）
# ============================================================================
def aggressive_strategy(state, params):
    """
    激进策略

    Args:
        state: 游戏状态
        params: 策略参数

    Returns:
        int: 动作（-1, 0, 1）
    """
    aggression = params["aggression"]
    risk_tolerance = params["risk_tolerance"]

    # 激进策略：倾向于远离中心
    if state["position"] > 0:
        if np.random.random() < aggression:
            return 1
    else:
        if np.random.random() < aggression:
            return -1

    # 随机动作
    return np.random.choice([-1, 0, 1])


def conservative_strategy(state, params):
    """
    保守策略

    Args:
        state: 游戏状态
        params: 策略参数

    Returns:
        int: 动作（-1, 0, 1）
    """
    aggression = params["aggression"]
    exploration_rate = params["exploration_rate"]

    # 保守策略：倾向于保持在中心附近
    if abs(state["position"]) > 3:
        # 返回中心
        return -1 if state["position"] > 0 else 1
    else:
        # 探索
        if np.random.random() < exploration_rate:
            return np.random.choice([-1, 1])

        return 0


def balanced_strategy(state, params):
    """
    平衡策略

    Args:
        state: 游戏状态
        params: 策略参数

    Returns:
        int: 动作（-1, 0, 1）
    """
    exploration_rate = params["exploration_rate"]
    risk_tolerance = params["risk_tolerance"]

    # 平衡策略：根据位置和风险容忍度决定
    if abs(state["position"]) > 5:
        # 远离中心，保守
        return -1 if state["position"] > 0 else 1
    else:
        # 中心附近，探索
        if np.random.random() < exploration_rate:
            return np.random.choice([-1, 1])
        else:
            return 0


# 策略映射
STRATEGIES = {
    "aggressive": aggressive_strategy,
    "conservative": conservative_strategy,
    "balanced": balanced_strategy
}


# ============================================================================
# 优化实验
# ============================================================================
# 定义搜索空间
search_space = SearchSpace()

# 策略参数
search_space.add_discrete("strategy_type", ["aggressive", "conservative", "balanced"])
search_space.add_continuous("aggression", 0.0, 1.0)
search_space.add_continuous("risk_tolerance", 0.0, 1.0)
search_space.add_continuous("exploration_rate", 0.0, 0.5)


def run_experiment(params):
    """
    运行实验：评估游戏策略

    Args:
        params: 策略参数

    Returns:
        float: 平均奖励（越高越好）
    """
    strategy_type = params["strategy_type"]
    strategy_params = {
        "aggression": params["aggression"],
        "risk_tolerance": params["risk_tolerance"],
        "exploration_rate": params["exploration_rate"]
    }

    # 选择策略
    strategy = STRATEGIES[strategy_type]

    # 运行多局游戏
    num_games = 20
    total_reward = 0.0

    for _ in range(num_games):
        reward = run_episode(strategy, strategy_params, max_steps=100)
        total_reward += reward

    # 返回平均奖励（越高越好）
    avg_reward = total_reward / num_games

    return avg_reward


# ============================================================================
# 主程序
# ============================================================================
def main():
    """主函数"""
    print()
    print("=" * 70)
    print("游戏策略优化示例")
    print("=" * 70)
    print()

    # 配置优化器
    config = ExperimentConfig(
        max_experiments=50,
        improvement_threshold=0.5,
        time_budget=5.0,  # 每个实验最多 5 秒
        direction="maximize",  # 最大化奖励
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
    print(f"最佳平均奖励: {result.best_score:.4f}")
    print(f"最佳策略参数:")
    for key, value in result.best_params.items():
        print(f"  {key}: {value}")
    print()
    print(f"总实验次数: {result.total_experiments}")
    print(f"总时间: {result.total_time:.2f} 秒")
    print(f"改进: {result.improvement:.4f}")
    print()

    # 使用最佳策略运行演示
    print("=" * 70)
    print("演示最佳策略")
    print("=" * 70)
    print()

    strategy_type = result.best_params["strategy_type"]
    strategy = STRATEGIES[strategy_type]
    strategy_params = {
        "aggression": result.best_params["aggression"],
        "risk_tolerance": result.best_params["risk_tolerance"],
        "exploration_rate": result.best_params["exploration_rate"]
    }

    # 运行 10 局演示
    total_reward = 0.0
    wins = 0

    for i in range(10):
        reward = run_episode(strategy, strategy_params, max_steps=100)
        total_reward += reward
        if reward > 0:
            wins += 1
        print(f"  游戏 {i+1}: 奖励 = {reward:.2f}")

    print()
    print(f"演示结果:")
    print(f"  平均奖励: {total_reward / 10:.2f}")
    print(f"  正局数: {wins}/10")
    print()

    # 保存结果
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"game_optimization_results_{timestamp}.json"

    with open(result_file, 'w') as f:
        json.dump({
            "best_params": result.best_params,
            "best_avg_reward": result.best_score,
            "improvement": result.improvement,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time
        }, f, indent=2)

    print(f"结果已保存到: {result_file}")


if __name__ == "__main__":
    main()
