# 7B → 14B 基座评估三步计划

> **目标**：用 44 题统一测试集评估候选基座，选出最优模型，决定本地部署方案
> **预算**：云 GPU ¥500（评估阶段）+ ¥15,000（硬件，可选）

---

## 第一步：7B 模型对比（本题材周期 1-2 天，0 云成本）

**硬件**：ai01（GTX 1070 8GB, 31GB RAM）+ ai（6GB GPU）

**目的**：验证核心假设——Coder 基座的 tool_call 倾向是否导致评测低于非 Coder 版

### 测试模型

| 模型 | 存储 | 大小 | 来源 |
|------|------|:----:|------|
| Qwen2.5-Coder-7B-Instruct (现有) | ai01 | 4.4G | 已下载 |
| Qwen2.5-7B-Instruct (非 Coder) | ai01 | 4.4G | HuggingFace 下载 |
| Qwen2.5-7B-Instruct 中文优化版 | ai01 | 4.4G | HuggingFace 下载 |

### 执行步骤

```
1. 下载新模型到 ai01 /home/ai01/models/
2. 对每个模型跑 44 题统一测试（N_GPU_LAYERS=0, CPU 推理）
3. 收集结果到 data/eval_7b_comparison.json
4. 与现有 V8/V9/V10/V10 评估结果对比
```

### 决策标准

| 非 Coder 版得分 | 结论 |
|:--------------:|------|
| > 0.85 | Coder 基座确实是问题根源，Step 2 直接上 14B |
| 0.80 - 0.85 | 差异不大，Coder 非核心因素 |
| < 0.80 | 7B 级别能力上限就在这，必须上 14B |

---

## 第二步：14B 云 GPU 评估（1-2 天，¥30-50 云成本）

**硬件**：恒源云 RTX 3090/4090 24G（¥3-5/h）

**目的**：确认 14B 相比 7B 基座的提升是否显著

### 测试模型

| 模型 | 量化 | 显存 | 评估耗时 |
|------|:----:|:----:|:--------:|
| Qwen2.5-14B-Instruct | Q4_K_M | ~10G | ~15 min |
| Qwen2.5-14B-Instruct | Q3_K_M | ~8G | ~15 min |

### 执行步骤

```
1. 启动恒源云实例（RTX 3090/4090, 预装 CUDA）
2. 安装环境: pip install llama-cpp-python huggingface_hub
3. 运行同一份 44 题评估脚本 scripts/eval_cloud.py
4. 结果保存到本地 data/eval_14b_comparison.json
```

### 决策标准

| 14B 得分 | 结论 |
|:--------:|------|
| > 0.90 | 大幅提升，进入 Step 3 本地部署规划 |
| 0.85 - 0.90 | 有提升但边际效应递减，可选 |
| < 0.85 | 14B 不值，7B 已够用 |

---

## 第三步：本地部署决策（如 Step 2 确认 14B 显著优于 7B）

### 硬件方案

| 方案 | 成本 | 可跑模型 | 可做训练 |
|:----:|:----:|:---------|:---------|
| **2×RTX 3090 24G** | ~¥15,000 | 14B FP16 / 32B Q4 推理 | 14B QLoRA ✅ |
| 云 GPU 按需 | ¥3-5/h | 同左 | 适合短期评估 |
| 本地 + 云混合 | ¥15k+按需 | 本地日常推理，云训练 | 最佳性价比 |

### 部署架构

```
ai01 (8G) ─── llama.cpp server (7B, 日常推理)
    │
    ├── PCIe 直连 ─── RTX 3090 #1 (14B 主推理)
    └── PCIe 直连 ─── RTX 3090 #2 (备用/训练)
```

### 实施排期

| 阶段 | 内容 | 时间 |
|:----:|------|:----:|
| 准备工作 | 云实例 + 模型下载 + 脚本 | 1 天 |
| Step 1 | 7B 对比，出结果 | 1 天 |
| Step 2 | 14B 云评估，出结果 | 1-2 天 |
| 决策点 | 是否值得买 2×3090 | — |
| Step 3 | 采购 + 装机 + 部署 | 1-2 周 |

---

## 评估脚本

已就绪：`scripts/eval_cloud.py`

```bash
# 7B 模型
MODEL_NAME=qwen2.5-7b-instruct \
MODEL_PATH=/path/to/model.gguf \
N_GPU_LAYERS=99 \
python3 scripts/eval_cloud.py

# 14B 模型（云 GPU）
MODEL_NAME=qwen2.5-14b-instruct \
MODEL_URL=Qwen/Qwen2.5-14B-Instruct-GGUF \
GGUF_FILE=qwen2.5-14b-instruct-q4_k_m.gguf \
N_GPU_LAYERS=99 \
python3 scripts/eval_cloud.py
```

44 题测试集已验证与 V8/V9/V10 评估一致，确保所有分数直接可比。
