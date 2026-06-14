"""合并V9训练数据：灵研934条 + anti-tool_call 14条 + V8关键样本"""
import json, os, random

OUTPUT_DIR = "/home/ai/lingminopt/data/training/v9"
OUTPUT_TRAIN = os.path.join(OUTPUT_DIR, "v9_train.jsonl")
OUTPUT_VAL = os.path.join(OUTPUT_DIR, "v9_val.jsonl")

# 数据源
SOURCES = [
    ("灵研合并数据", "/home/ai/lingresearch/data/training_dataset/merged/merged_train.jsonl"),
    ("anti-tool_call", "/home/ai/lingminopt/data/training/anti_tool_call_samples.jsonl"),
    ("V8训练数据", "/home/ai/lingflow/training_package_7b/data/lingai_7b_train_v8.jsonl"),
    ("V8 Phase5", "/home/ai/lingflow/training_package_7b/data/lingai_7b_train_v8_phase5.jsonl"),
    ("灵族特色", "/home/ai/lingminopt/data/training/lingzu_all_final.jsonl"),
]

os.makedirs(OUTPUT_DIR, exist_ok=True)

all_samples = []
source_stats = {}

for name, path in SOURCES:
    if not os.path.exists(path):
        print(f"SKIP {name}: {path} not found")
        continue
    count = 0
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            all_samples.append(d)
            count += 1
    source_stats[name] = count
    print(f"Loaded {name}: {count} samples")

# 去重（基于user message content hash）
seen = set()
deduped = []
for s in all_samples:
    user_msg = ""
    for msg in s.get("messages", []):
        if msg["role"] == "user":
            user_msg = msg["content"][:100]
            break
    key = hash(user_msg)
    if key not in seen:
        seen.add(key)
        deduped.append(s)

print(f"\nTotal before dedup: {len(all_samples)}")
print(f"After dedup: {len(deduped)}")

# 打乱顺序
random.seed(42)
random.shuffle(deduped)

# 分割 train/val (95/5)
split = int(len(deduped) * 0.95)
train = deduped[:split]
val = deduped[split:]

with open(OUTPUT_TRAIN, "w") as f:
    for s in train:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

with open(OUTPUT_VAL, "w") as f:
    for s in val:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

print(f"\n=== V9 Dataset ===")
print(f"Train: {len(train)} → {OUTPUT_TRAIN}")
print(f"Val:   {len(val)} → {OUTPUT_VAL}")
print(f"\nSource breakdown:")
for name, count in source_stats.items():
    print(f"  {name}: {count}")
