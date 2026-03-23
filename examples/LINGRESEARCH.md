# LingResearch (灵研) - 自主 AI 研究项目

**完整的自主研究项目，使用 LingMinOpt 框架**

LingResearch 是一个完整的自主研究项目，灵感来自 Karpathy 的 [autoresearch](https://github.com/karpathy/autoresearch)。

## 📦 仓库信息

- **GitHub**: https://github.com/guangda88/LingResearch
- **依赖**: `pip install lingminopt`
- **状态**: 独立项目（不在 LingMinOpt 仓库中）

## 🎯 项目目标

LingResearch 展示了如何使用 LingMinOpt 框架进行真正的自主研究：

1. **自主实验**: 自动搜索最优模型架构和超参数
2. **快速反馈**: 每个实验在几分钟内完成
3. **数据驱动**: 基于实验结果自动调整搜索方向
4. **持续改进**: 逐步逼近最优配置

## 🚀 快速开始

```bash
# 克隆项目
git clone https://github.com/guangda88/LingResearch.git
cd LingResearch

# 安装依赖
pip install lingminopt torch numpy

# 运行研究
python run_lingresearch.py
```

## 📁 项目结构

```
LingResearch/
├── prepare.py           # 固定约束（数据集、环境等）
├── variable.py          # 可变参数（搜索空间、实验逻辑）
├── run_lingresearch.py  # 主运行脚本
└── README.md           # 本文件
```

## 🔄 与 LingMinOpt 的关系

- **LingMinOpt**: 通用自优化框架库
- **LingResearch**: 使用该框架的具体应用

```
LingResearch (应用)
    ↓ 使用
LingMinOpt (框架)
    ↓ 应用到
其他场景（ML优化、数据库优化等）
```

## 💡 核心理念

> **给 AI 一个真实的环境，让它自主实验。修改代码、运行几分钟、检查结果是否改进、保留或丢弃更改，然后重复。**

这与 LingMinOpt 的设计理念完全一致：
- 极简主义：5 行代码开始
- 自动化：自动搜索、评估、选择
- 数据驱动：基于结果做决策

## 📊 典型工作流程

```python
# 1. 定义搜索空间
search_space = SearchSpace()
search_space.add_discrete("model_type", ["mlp", "lstm", "gru"])
search_space.add_continuous("learning_rate", 1e-5, 1e-2)

# 2. 定义评估函数
def evaluate(params):
    model = build_model(params)
    loss = train(model, params)
    return loss

# 3. 运行优化
optimizer = MinimalOptimizer(evaluate, search_space)
result = optimizer.run()

# 4. 使用最佳结果
print(f"最佳配置: {result.best_params}")
```

## 🎓 学习资源

- LingMinOpt 文档: https://github.com/guangda88/LingMinOpt
- Karpathy 的 autoresearch: https://github.com/karpathy/autoresearch

## 📝 许可证

MIT License - 与 LingMinOpt 保持一致

---

**由 Guangda 用 ❤️ 制作**
