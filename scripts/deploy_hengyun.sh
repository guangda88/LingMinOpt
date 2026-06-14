#!/bin/bash
# lingAI 7B 推理深度 LoRA 微调 — 恒源云部署脚本
# 用法: bash deploy_hengyun.sh
# 前置: 在恒源云 RTX 3090 实例上运行
set -e

echo "========================================"
echo "lingAI 7B 推理深度 LoRA 微调"
echo "========================================"

PROJECT_DIR="/root/autodl-tmp/lingminopt"
DATA_DIR="$PROJECT_DIR/data/training"
OUTPUT_DIR="/root/autodl-tmp/lingai-7b-reasoning-lora"
SCRIPTS_DIR="$PROJECT_DIR/scripts"
MERGED_DATA_DIR="/root/autodl-tmp/lingresearch/data/training_dataset"

# === 1. 安装依赖 ===
echo -e "\n=== 安装依赖 ==="
pip install -U torch transformers peft trl accelerate datasets bitsandbytes --quiet

# === 2. 同步代码和训练数据 ===
echo -e "\n=== 准备训练数据 ==="
# 假设代码已通过 scp 上传到恒源云
# scp -P <PORT> -r /home/ai/lingminopt root@<HOST>:/root/autodl-tmp/lingminopt
# scp -P <PORT> /home/ai/lingresearch/data/training_dataset/merged/merged_all.jsonl root@<HOST>:/root/autodl-tmp/lingai-7b-data/

mkdir -p $MERGED_DATA_DIR/merged
ls -lh $DATA_DIR/
ls -lh $MERGED_DATA_DIR/merged/merged_all.jsonl 2>/dev/null || \
    echo "⚠ merged_all.jsonl 不在 $MERGED_DATA_DIR/merged/ 下，脚本会跳过该文件"

# === 3. 验证 GPU ===
echo -e "\n=== GPU 信息 ==="
python3 -c "
import torch
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        p = torch.cuda.get_device_properties(i)
        print(f'GPU {i}: {p.name} | VRAM: {p.total_memory/1024**3:.1f}GB')
else:
    print('ERROR: CUDA 不可用')
"

# === 4. 运行训练 ===
echo -e "\n=== 开始训练 ==="
DATA_ROOT=$MERGED_DATA_DIR OUTPUT_DIR=$OUTPUT_DIR \
    python3 $SCRIPTS_DIR/train_lingai_7b_reasoning_lora.py

# === 5. 合并 LoRA + 量化 ===
echo -e "\n=== 合并 LoRA ==="
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

base_model_name = 'Qwen/Qwen2.5-Coder-7B-Instruct'
lora_path = '$OUTPUT_DIR'\noutput_dir_env = '$OUTPUT_DIR'
output_path = '/root/autodl-tmp/lingai-7b-merged'

print('加载基座模型...')
tokenizer = AutoTokenizer.from_pretrained(base_model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.bfloat16,
    device_map='auto',
    trust_remote_code=True,
)

print('加载 LoRA 权重...')
model = PeftModel.from_pretrained(model, lora_path)
print('合并 LoRA...')
merged = model.merge_and_unload()
print(f'保存合并模型到 {output_path}...')
merged.save_pretrained(output_path)
tokenizer.save_pretrained(output_path)
print('合并完成!')
"

# === 6. 量化 GGUF Q4_K_M (用于 ai01 8GB GPU) ===
echo -e "\n=== 量化 GGUF Q4_K_M ==="
pip install llama-cpp-python --quiet
python3 -m llama_cpp.convert \
    /root/autodl-tmp/lingai-7b-merged \
    --outtype q4_k_m \
    --outfile /root/autodl-tmp/lingai-7b-reasoning-q4km.gguf

# === 7. 打包 ===
echo -e "\n=== 打包 ==="
cd /root/autodl-tmp
tar czf lingai-7b-reasoning-output.tar.gz \
    lingai-7b-merged/ \
    lingai-7b-reasoning-q4km.gguf \
    lingai-7b-reasoning-lora/
ls -lh lingai-7b-reasoning-output.tar.gz

echo -e "\n========================================"
echo "训练完成!"
echo "下载命令:"
echo "  scp -P <PORT> root@<HOST>:/root/autodl-tmp/lingai-7b-reasoning-output.tar.gz /home/ai/models/"
echo "========================================"
