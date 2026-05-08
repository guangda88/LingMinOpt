"""
示例：机器学习超参数优化

使用 LingMinOpt 优化机器学习模型的超参数。

目标：最小化验证集的损失
"""

import sys
sys.path.insert(0, '/home/ai/LingMinOpt')

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss
import numpy as np
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 固定配置（不可修改）
# ============================================================================
# 生成数据
X, y = make_classification(
    n_samples=1000,
    n_features=20,
    n_informative=10,
    n_redundant=5,
    n_clusters_per_class=2,
    random_state=42
)

# 划分训练/验证集
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger.info("数据集信息:")
logger.info("  特征数: %d", X.shape[1])
logger.info("  类别数: %d", len(np.unique(y)))
logger.info("  训练样本: %d", X_train.shape[0])
logger.info("  验证样本: %d", X_val.shape[0])


# ============================================================================
# 评估函数（不可修改）
# ============================================================================
def evaluate_model(model, X_val, y_val):
    """
    评估模型并返回验证损失

    Args:
        model: 训练好的模型
        X_val: 验证集特征
        y_val: 验证集标签

    Returns:
        float: 验证集的对数损失
    """
    # 预测概率
    y_pred_proba = model.predict_proba(X_val)

    # 计算对数损失
    loss = log_loss(y_val, y_pred_proba)

    return loss


# ============================================================================
# 可变参数和实验逻辑
# ============================================================================
# 定义搜索空间
search_space = SearchSpace()

# 随机森林参数
search_space.add_discrete("n_estimators", [50, 100, 200, 300])
search_space.add_discrete("max_depth", [3, 5, 7, 10, None])
search_space.add_discrete("min_samples_split", [2, 5, 10])
search_space.add_discrete("min_samples_leaf", [1, 2, 4])
search_space.add_continuous("max_features", 0.1, 1.0)  # 特征比例
search_space.add_continuous("min_weight_fraction_leaf", 0.0, 0.5)
search_space.add_discrete("bootstrap", [True, False])


def run_experiment(params):
    """
    运行实验：训练随机森林并评估

    Args:
        params: 超参数字典

    Returns:
        float: 验证集损失（越低越好）
    """
    # 提取参数
    n_estimators = params["n_estimators"]
    max_depth = params["max_depth"]
    min_samples_split = params["min_samples_split"]
    min_samples_leaf = params["min_samples_leaf"]
    max_features = params["max_features"]
    min_weight_fraction_leaf = params["min_weight_fraction_leaf"]
    bootstrap = params["bootstrap"]

    # 创建模型
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_features=max_features,
        min_weight_fraction_leaf=min_weight_fraction_leaf,
        bootstrap=bootstrap,
        random_state=42,
        n_jobs=-1  # 并行训练
    )

    # 训练模型
    model.fit(X_train, y_train)

    # 评估模型
    val_loss = evaluate_model(model, X_val, y_val)

    return val_loss


# ============================================================================
# 主程序
# ============================================================================
def main():
    """主函数"""
    logger.info("")
    logger.info("=" * 70)
    logger.info("机器学习超参数优化示例")
    logger.info("=" * 70)
    logger.info("")

    # 配置优化器
    config = ExperimentConfig(
        max_experiments=30,
        improvement_threshold=0.001,
        time_budget=10.0,  # 每个实验最多 10 秒
        direction="minimize",
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
    logger.info("开始优化...")
    logger.info("搜索空间: %d 个参数", len(search_space))
    logger.info("最大实验次数: %d", config.max_experiments)
    logger.info("")

    result = optimizer.run()

    # 打印结果
    logger.info("")
    logger.info("=" * 70)
    logger.info("优化结果")
    logger.info("=" * 70)
    logger.info("")
    logger.info("最佳验证损失: %.6f", result.best_score)
    logger.info("最佳超参数:")
    for key, value in result.best_params.items():
        logger.info("  %s: %s", key, value)
    logger.info("")
    logger.info("总实验次数: %d", result.total_experiments)
    logger.info("总时间: %.2f 秒", result.total_time)
    logger.info("改进: %.6f", result.improvement)
    logger.info("")

    # 使用最佳参数训练最终模型
    logger.info("=" * 70)
    logger.info("训练最终模型")
    logger.info("=" * 70)
    logger.info("")

    final_model = RandomForestClassifier(
        n_estimators=result.best_params["n_estimators"],
        max_depth=result.best_params["max_depth"],
        min_samples_split=result.best_params["min_samples_split"],
        min_samples_leaf=result.best_params["min_samples_leaf"],
        max_features=result.best_params["max_features"],
        min_weight_fraction_leaf=result.best_params["min_weight_fraction_leaf"],
        bootstrap=result.best_params["bootstrap"],
        random_state=42,
        n_jobs=-1
    )

    # 使用全部训练数据
    X_full = np.vstack([X_train, X_val])
    y_full = np.hstack([y_train, y_val])

    final_model.fit(X_full, y_full)

    logger.info("最终模型已训练完成！")
    logger.info("训练样本: %d", X_full.shape[0])
    logger.info("")

    # 保存结果
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"ml_optimization_results_{timestamp}.json"

    with open(result_file, 'w') as f:
        json.dump({
            "best_params": result.best_params,
            "best_val_loss": result.best_score,
            "improvement": result.improvement,
            "total_experiments": result.total_experiments,
            "total_time": result.total_time
        }, f, indent=2)

    logger.info("结果已保存到: %s", result_file)


if __name__ == "__main__":
    main()
