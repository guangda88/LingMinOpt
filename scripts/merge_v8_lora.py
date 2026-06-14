"""合并V8 LoRA到Qwen2.5-Coder-7B-Instruct基座 → 导出fp16 safetensors"""
import os, sys, time

MODEL_DIR = "/home/ai/models/Qwen2.5-Coder-7B-Instruct"
LORA_DIR = "/home/ai/lingflow/training_package_7b/v8_lora"
OUTPUT_DIR = "/home/ai/models/lingai-7b-v8-merged"

print("=== V8 LoRA Merge ===")
t0 = time.time()

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

print(f"[1/3] Loading base model: {MODEL_DIR}")
base = AutoModelForCausalLM.from_pretrained(
    MODEL_DIR, torch_dtype="auto", device_map="cpu", low_cpu_mem_usage=True
)
tok = AutoTokenizer.from_pretrained(MODEL_DIR)
print(f"  loaded in {time.time()-t0:.0f}s")

print(f"[2/3] Applying LoRA: {LORA_DIR}")
model = PeftModel.from_pretrained(base, LORA_DIR)
print(f"  LoRA applied, merging...")
model = model.merge_and_unload()
print(f"  merge done in {time.time()-t0:.0f}s")

print(f"[3/3] Saving merged model: {OUTPUT_DIR}")
os.makedirs(OUTPUT_DIR, exist_ok=True)
model.save_pretrained(OUTPUT_DIR, safe_serialization=True, max_shard_size="5GB")
tok.save_pretrained(OUTPUT_DIR)
print(f"  saved in {time.time()-t0:.0f}s")
print("=== Done ===")
