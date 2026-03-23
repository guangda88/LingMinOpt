"""
简化版灵研示例 - 演示如何使用 LingMinOpt 进行自主研究

完整版 LingResearch 项目请访问：
https://github.com/guangda88/LingResearch

此示例展示了 LingMinOpt 框架的核心用法：
- 定义搜索空间
- 定义评估函数
- 自动化优化流程
"""

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
import numpy as np


def main():
    """简化版灵研示例"""

    # 1. 定义搜索空间
    search_space = SearchSpace()
    search_space.add_discrete("model_type", ["mlp", "lstm", "gru"])
    search_space.add_discrete("hidden_size", [64, 128, 256, 512])
    search_space.add_continuous("learning_rate", 1e-4, 1e-2)
    search_space.add_continuous("dropout", 0.0, 0.5)
    search_space.add_discrete("optimizer", ["adam", "adamw", "sgd"])

    # 2. 定义评估函数（模拟训练和评估）
    def evaluate(params):
        """
        模拟训练和评估过程

        在真实场景中，这里会：
        1. 根据参数构建模型
        2. 训练几个 epoch
        3. 在验证集上评估
        4. 返回验证损失（BPC）
        """
        # 模拟训练时间
        import time
        time.sleep(0.1)  # 模拟 100ms 训练

        # 模拟：参数越好，BPC 越低
        model_type_score = {"mlp": 1.5, "lstm": 1.3, "gru": 1.2}[params["model_type"]]
        hidden_score = params["hidden_size"] / 256.0
        lr_score = -np.log10(params["learning_rate"]) * 0.1
        dropout_score = params["dropout"] * 0.5
        opt_score = {"adam": 0.9, "adamw": 1.0, "sgd": 0.8}[params["optimizer"]]

        # 模拟 BPC（bits per character）
        bpc = model_type_score + hidden_score + lr_score + dropout_score + opt_score

        # 添加一些随机性
        bpc += np.random.randn() * 0.02

        return bpc

    # 3. 配置优化器
    config = ExperimentConfig(
        max_experiments=50,
        improvement_threshold=0.01,
        time_budget=300,  # 5 分钟
        early_stopping_patience=10,
        direction="minimize",
        random_seed=42
    )

    # 4. 创建并运行优化器
    print("=" * 70)
    print("灵研简化示例 - 使用 LingMinOpt 框架")
    print("=" * 70)
    print()
    print("完整版 LingResearch 项目：")
    print("  https://github.com/guangda88/LingResearch")
    print()

    optimizer = MinimalOptimizer(
        evaluate=evaluate,
        search_space=search_space,
        config=config,
        search_strategy="random"
    )

    # 5. 运行优化
    result = optimizer.run()

    # 6. 打印结果
    print()
    print("=" * 70)
    print("优化结果")
    print("=" * 70)
    print(f"最佳 BPC: {result.best_score:.4f}")
    print(f"最佳参数:")
    for key, value in result.best_params.items():
        print(f"  {key}: {value}")
    print()
    print(f"总实验次数: {result.total_experiments}")
    print(f"总时间: {result.total_time:.2f} 秒")
    print(f"总改进: {result.improvement:.4f} BPC")
    print()


if __name__ == "__main__":
    main()
