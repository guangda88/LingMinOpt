"""将PEFT LoRA (safetensors) 转换为 GGUF LoRA格式 — 修复版"""
import os, sys
import numpy as np
from safetensors import safe_open
import gguf

LORA_PATH = "/home/ai/lingflow/training_package_7b/v8_lora/adapter_model.safetensors"
OUTPUT_PATH = "/home/ai/models/v8-lora.gguf"
RANK = 8
ALPHA = 16
NUM_LAYERS = 28

MODULE_MAP = {
    "self_attn.q_proj": "attn_q",
    "self_attn.k_proj": "attn_k",
    "self_attn.v_proj": "attn_v",
    "self_attn.o_proj": "attn_output",
    "mlp.gate_proj": "ffn_gate",
    "mlp.down_proj": "ffn_down",
    "mlp.up_proj": "ffn_up",
}

print("=== PEFT LoRA → GGUF LoRA (fixed) ===")

tensors = {}
with safe_open(LORA_PATH, framework="pt") as f:
    for key in f.keys():
        tensors[key] = f.get_tensor(key).numpy().astype(np.float32)

print(f"Loaded {len(tensors)} tensors")

writer = gguf.GGUFWriter(OUTPUT_PATH, "llama-lora", use_temp_file=False)

# 关键：设置ADAPTER类型（官方脚本用法）
writer.add_type(gguf.GGUFType.ADAPTER)
writer.add_string(gguf.Keys.Adapter.TYPE, "lora")
writer.add_float32(gguf.Keys.Adapter.LORA_ALPHA, float(ALPHA))

count = 0
for layer_idx in range(NUM_LAYERS):
    for peft_module, gguf_module in MODULE_MAP.items():
        a_key = f"base_model.model.model.layers.{layer_idx}.{peft_module}.lora_A.weight"
        b_key = f"base_model.model.model.layers.{layer_idx}.{peft_module}.lora_B.weight"

        if a_key not in tensors or b_key not in tensors:
            continue

        lora_a = tensors[a_key]  # [r, in_features]
        lora_b = tensors[b_key]  # [out_features, r]

        a_name = f"blk.{layer_idx}.{gguf_module}.weight.lora_a"
        b_name = f"blk.{layer_idx}.{gguf_module}.weight.lora_b"

        writer.add_tensor(a_name, lora_a, raw_dtype=gguf.GGMLQuantizationType.F32)
        writer.add_tensor(b_name, lora_b, raw_dtype=gguf.GGMLQuantizationType.F32)
        count += 2

print(f"Written {count} tensors")

writer.write_header_to_file()
writer.write_kv_data_to_file()
writer.write_tensors_to_file()
writer.close()

print(f"GGUF LoRA saved: {OUTPUT_PATH}")
print("=== Done ===")
