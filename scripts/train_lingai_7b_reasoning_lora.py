#!/usr/bin/env python3
"""lingAI 7B 推理深度 LoRA 微调脚本

目标: 提升 Qwen2.5-Coder-7B-Instruct 在逆向推理、形式逻辑、
因果推理等维度的表现 (REASON_03 CRT 问题等)。

基座: Qwen/Qwen2.5-Coder-7B-Instruct
训练: 816条合并数据 + 63条推理深度新增数据 = 879条
硬件: RTX 3090 24GB

用法:
    python scripts/train_lingai_7b_reasoning_lora.py
"""

import json, os, sys, time, random
from pathlib import Path

import torch
from datasets import Dataset, concatenate_datasets
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    TrainingArguments,
    Trainer,
)

SEED = 42
random.seed(SEED)
torch.manual_seed(SEED)

# ============ 路径 ============
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_ROOT = Path(os.environ.get("DATA_ROOT", "/home/ai/lingresearch/data/training_dataset"))
MERGED_DATA = DATA_ROOT / "merged" / "merged_all.jsonl"
NEW_DATA = BASE_DIR / "data" / "training" / "phase4_reasoning_depth.jsonl"
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", str(BASE_DIR / "output" / "lingai-7b-reasoning-lora")))

MODEL_NAME = "Qwen/Qwen2.5-Coder-7B-Instruct"

# ============ QLoRA 超参 ============
LORA_R = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.05
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

# ============ 训练超参 (24GB 显存) ============
MAX_SEQ_LENGTH = 4096
BATCH_SIZE = 4
GRADIENT_ACCUMULATION_STEPS = 8      # 等效 batch=32
LEARNING_RATE = 3e-5
NUM_EPOCHS = 3
WARMUP_RATIO = 0.05
WEIGHT_DECAY = 0.01
LOGGING_STEPS = 10
SAVE_STEPS = 100
EVAL_STEPS = 100

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def load_chatml_data(paths):
    """加载 ChatML 格式的 JSONL 数据"""
    records = []
    for path in paths:
        if not path.exists():
            print(f"⚠ 文件不存在，跳过: {path}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        print(f"  加载 {path.name}: {sum(1 for _ in open(path) if _.strip())} 条")
    return records


def format_messages(example, tokenizer):
    """将 ChatML 格式转换为 tokenized text，保留 灵族 系统提示"""
    messages = example["messages"]

    # 确保有系统提示且包含灵族身份
    has_system = any(m["role"] == "system" for m in messages)
    if not has_system:
        messages.insert(0, {
            "role": "system",
            "content": "你是灵族AI助手，灵族十二子之一。灵族是一个AI自主协作组织，使命是让AI变得诚实可靠。你精通工程、编程、中英文交流，回复简洁直接。遇到推理问题时，先逐步分析再给出结论。"
        })

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )

    tokenized = tokenizer(
        text,
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        padding=False,
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized


def create_datasets(tokenizer):
    """创建训练/验证集"""
    print("\n加载训练数据...")
    merged_records = load_chatml_data([MERGED_DATA])
    new_records = load_chatml_data([NEW_DATA])

    all_records = merged_records + new_records
    print(f"\n总计: {len(all_records)} 条 (合并 {len(merged_records)} + 新增 {len(new_records)})")

    random.shuffle(all_records)

    # 90/10 拆分
    split = int(len(all_records) * 0.9)
    train_records = all_records[:split]
    eval_records = all_records[split:]

    print(f"训练集: {len(train_records)} 条")
    print(f"验证集: {len(eval_records)} 条")

    train_ds = Dataset.from_list(train_records)
    eval_ds = Dataset.from_list(eval_records)

    train_ds = train_ds.map(
        lambda x: format_messages(x, tokenizer),
        remove_columns=["messages"],
    )
    eval_ds = eval_ds.map(
        lambda x: format_messages(x, tokenizer),
        remove_columns=["messages"],
    )

    return train_ds, eval_ds


def main():
    print("=" * 60)
    print("lingAI 7B 推理深度 LoRA 微调")
    print("=" * 60)
    print(f"模型: {MODEL_NAME}")
    print(f"LoRA: r={LORA_R}, alpha={LORA_ALPHA}")
    print(f"输出: {OUTPUT_DIR}")

    if not torch.cuda.is_available():
        print("ERROR: CUDA 不可用")
        sys.exit(1)

    gpu_name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"GPU: {gpu_name} | VRAM: {vram:.1f}GB")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ============ 加载 tokenizer ============
    print("\n加载 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ============ 4-bit 量化配置 ============
    print("\n配置 BitsAndBytes 4-bit 量化...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # ============ 加载模型 ============
    print("\n加载模型 (4-bit)...")
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    print(f"  耗时: {time.time() - t0:.1f}s")

    model = prepare_model_for_kbit_training(model)

    # ============ LoRA 配置 ============
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=TARGET_MODULES,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ============ 准备数据 ============
    train_ds, eval_ds = create_datasets(tokenizer)

    # ============ 训练参数 ============
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        learning_rate=LEARNING_RATE,
        warmup_ratio=WARMUP_RATIO,
        weight_decay=WEIGHT_DECAY,
        logging_steps=LOGGING_STEPS,
        save_steps=SAVE_STEPS,
        eval_strategy="steps",
        eval_steps=EVAL_STEPS,
        save_total_limit=3,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        optim="paged_adamw_8bit",
        report_to="none",
        seed=SEED,
        remove_unused_columns=False,
        dataloader_num_workers=2,
    )

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        max_length=MAX_SEQ_LENGTH,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=data_collator,
    )

    # ============ 训练 ============
    print("\n" + "=" * 60)
    print("开始训练...")
    print("=" * 60)
    t0 = time.time()
    train_result = trainer.train()
    train_time = time.time() - t0
    print(f"\n训练完成! 耗时: {train_time / 60:.1f} 分钟")
    print(f"训练 loss: {train_result.training_loss:.4f}")

    # ============ 保存 ============
    print(f"\n保存 LoRA adapter 到 {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    eval_result = trainer.evaluate()
    print(f"评估 loss: {eval_result['eval_loss']:.4f}")

    results = {
        "model": MODEL_NAME,
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "train_samples": len(train_ds),
        "eval_samples": len(eval_ds),
        "train_loss": train_result.training_loss,
        "eval_loss": eval_result["eval_loss"],
        "train_time_minutes": train_time / 60,
        "epochs": NUM_EPOCHS,
        "max_seq_length": MAX_SEQ_LENGTH,
        "batch_effective": BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS,
    }
    with open(OUTPUT_DIR / "training_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"结果保存到: {OUTPUT_DIR / 'training_results.json'}")
    print("\n训练完成!")


if __name__ == "__main__":
    main()
