"""
lingAI 7B Reasoning LoRA 直接评估 — 灵极优(lingminopt)
使用llama-cpp-python直接加载模型，不走HTTP服务器。
"""
import json, os, time
from datetime import datetime
from llama_cpp import Llama

MODEL_PATH = "/home/ai/models/lingai-7b-reasoning-q4km.gguf"
OUTPUT_PATH = "/home/ai/lingminopt/data/lingai_7b_reasoning_eval_results.json"

print(f"Loading {MODEL_PATH}...", flush=True)
llm = Llama(model_path=MODEL_PATH, n_gpu_layers=-1, n_ctx=2048, verbose=False)
print("Model loaded.", flush=True)

# Import test cases from existing suite
import sys
sys.path.insert(0, "/home/ai/lingminopt/tests")
from test_lingai_rigorous import TESTS

def call_model(messages, max_tokens=256, temperature=0.3):
    t0 = time.time()
    r = llm.create_chat_completion(messages=messages, max_tokens=max_tokens, temperature=temperature)
    content = r["choices"][0]["message"]["content"]
    usage = r.get("usage", {})
    elapsed = time.time() - t0
    return {
        "content": content,
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "elapsed": elapsed,
    }

results = []
total = len(TESTS)
print(f"\n{'='*60}", flush=True)
print(f"lingAI 7B Reasoning LoRA 评估 — {total} tests", flush=True)
print(f"{'='*60}\n", flush=True)

for i, test in enumerate(TESTS, 1):
    tid = test["id"]
    name = test["name"]
    category = test["category"]
    msgs = test["messages"]

    resp = call_model(msgs)
    content = resp["content"]
    score = test["evaluate"](content)
    score = min(1.0, max(0.0, score))

    results.append({
        "id": tid,
        "category": category,
        "name": name,
        "content": content[:500],
        "score": score,
        "elapsed": round(resp["elapsed"], 2),
        "prompt_tokens": resp["prompt_tokens"],
        "completion_tokens": resp["completion_tokens"],
    })

    status = "✓" if score >= 0.8 else "△" if score >= 0.5 else "✗"
    print(f"  [{i:2d}/{total}] {status} {tid} {name:20s} score={score:.1f} ({resp['elapsed']:.1f}s)", flush=True)

# Summary
cat_scores = {}
for r in results:
    cat = r["category"]
    if cat not in cat_scores:
        cat_scores[cat] = []
    cat_scores[cat].append(r["score"])

overall = sum(r["score"] for r in results) / len(results)
print(f"\n{'='*60}", flush=True)
print("结果汇总", flush=True)
print(f"{'='*60}", flush=True)
print(f"\n总评分: {overall:.2f} / 1.0 ({len(results)} tests)\n", flush=True)
print(f"{'类别':<12s} {'均分':>5s} {'测试数':>5s} {'通过':>5s} {'失败':>5s}", flush=True)
print("-" * 40, flush=True)
for cat, scores in sorted(cat_scores.items()):
    avg = sum(scores) / len(scores)
    passed = sum(1 for s in scores if s >= 0.8)
    failed = sum(1 for s in scores if s < 0.5)
    print(f"{cat:<12s} {avg:>5.2f} {len(scores):>5d} {passed:>5d} {failed:>5d}", flush=True)

output = {
    "model": "lingai-7b-reasoning-q4km (LoRA)",
    "base_model": "Qwen2.5-Coder-7B-Instruct",
    "timestamp": datetime.now().isoformat(),
    "total_tests": len(results),
    "overall_score": round(overall, 2),
    "categories": {cat: round(sum(s)/len(s), 2) for cat, s in sorted(cat_scores.items())},
    "results": results,
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"\n结果已保存: {OUTPUT_PATH}", flush=True)
