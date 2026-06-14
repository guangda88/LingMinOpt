#!/bin/bash
# V9 LoRA训练脚本 — 基于V8流程+anti-tool_call改进
# 基座: Qwen2.5-Coder-7B-Instruct
# 数据: 1110 train + 59 val (含anti-tool_call 14条)
# 参数: r=8, alpha=16, 1epoch, lr=3e-5

set -euo pipefail

echo "=== V9 LoRA Training ==="
echo "Start: $(date)"

# 配置
BASE_MODEL="${BASE_MODEL:-Qwen/Qwen2.5-Coder-7B-Instruct}"
TRAIN_DATA="/home/ai/lingminopt/data/training/v9/v9_train.jsonl"
VAL_DATA="/home/ai/lingminopt/data/training/v9/v9_val.jsonl"
OUTPUT_DIR="./v9_lora"
LOG_DIR="./logs"

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

# 训练参数（与V8一致，验证过的稳定参数）
ACCELERATE_CONFIG="--mixed_precision bf16 --num_processes 1"

# 检查数据
echo "[1/3] Checking data..."
python3 -c "
import json
for path, label in [('$TRAIN_DATA', 'train'), ('$VAL_DATA', 'val')]:
    with open(path) as f:
        lines = f.readlines()
    print(f'{label}: {len(lines)} samples')
    # 检查格式
    for line in lines[:3]:
        d = json.loads(line)
        assert 'messages' in d, f'Missing messages key'
        roles = [m['role'] for m in d['messages']]
        assert 'user' in roles and 'assistant' in roles, f'Missing user/assistant'
    print(f'  Format OK')
"

# LoRA训练
echo "[2/3] Starting LoRA training..."
python3 -m transformers.trainer \
    --model_name_or_path "$BASE_MODEL" \
    --train_file "$TRAIN_DATA" \
    --validation_file "$VAL_DATA" \
    --output_dir "$OUTPUT_DIR" \
    --num_train_epochs 1 \
    --per_device_train_batch_size 4 \
    --per_device_eval_batch_size 4 \
    --gradient_accumulation_steps 4 \
    --learning_rate 3e-5 \
    --warmup_ratio 0.03 \
    --lr_scheduler_type cosine \
    --logging_steps 10 \
    --save_strategy epoch \
    --eval_strategy epoch \
    --lora_r 8 \
    --lora_alpha 16 \
    --lora_dropout 0.05 \
    --lora_target_modules "q_proj,k_proj,v_proj,o_proj,gate_proj,down_proj,up_proj" \
    --bf16 \
    --gradient_checkpointing \
    --max_seq_length 1024 \
    2>&1 | tee "$LOG_DIR/v9_train.log"

echo "[3/3] Training complete: $OUTPUT_DIR"
echo "End: $(date)"
echo ""
echo "Next: 灵极优执行V9评估"
echo "  python3 /home/ai/lingminopt/scripts/eval_v8_lora.py --lora $OUTPUT_DIR"
