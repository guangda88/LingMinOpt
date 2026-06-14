"""lingAI 7B评估 — 复用41道严格测试，对比3B基线"""

import json
import os
import time
import requests
import sys
from datetime import datetime

API_URL = "http://localhost:8765/v1/chat/completions"
MODEL_7B = "lingai-7b-base-4bit"  # V8 uses same alias, routes to :8101
MODEL_3B = "lingai-3b-v7-4bit"
API_KEY = os.environ.get("EVAL_API_KEY", "")
TIMEOUT = 180

sys.path.insert(0, "/home/ai/lingminopt/tests")
from test_lingai_rigorous import TESTS

def call_api(messages, model, max_tokens=512, temperature=0.3):
    try:
        headers = {"X-API-Key": API_KEY}
        r = requests.post(API_URL, json={
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return {
            "content": content,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        }
    except Exception as e:
        return {"content": f"ERROR: {e}", "prompt_tokens": 0, "completion_tokens": 0}


def run_eval(model, label):
    results = []
    total = len(TESTS)
    print(f"\n{'='*60}")
    print(f"lingAI {label} 评估 — {total}道测试")
    print(f"模型: {model}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    for i, test in enumerate(TESTS, 1):
        tid = test["id"]
        name = test["name"]
        category = test["category"]
        msgs = test["messages"]

        t0 = time.time()
        resp = call_api(msgs, model)
        elapsed = round(time.time() - t0, 2)

        content = resp["content"]
        score = test["evaluate"](content)
        score = min(1.0, max(0.0, score))

        results.append({
            "id": tid,
            "category": category,
            "name": name,
            "content": content[:500],
            "score": score,
            "elapsed": elapsed,
            "prompt_tokens": resp["prompt_tokens"],
            "completion_tokens": resp["completion_tokens"],
        })

        status = "✓" if score >= 0.8 else "△" if score >= 0.5 else "✗"
        print(f"  [{i:2d}/{total}] {status} {tid} {name:20s} score={score:.1f} ({elapsed}s, {resp['completion_tokens']}tok)")

    cat_scores = {}
    for r in results:
        cat = r["category"]
        if cat not in cat_scores:
            cat_scores[cat] = []
        cat_scores[cat].append(r["score"])

    overall = sum(r["score"] for r in results) / len(results)

    print(f"\n{'='*60}")
    print(f"{label} 结果汇总")
    print(f"{'='*60}")
    print(f"\n总评分: {overall:.2f} / 1.0 ({len(results)} tests)\n")
    print(f"{'类别':<12s} {'均分':>5s} {'测试数':>5s} {'通过':>5s} {'失败':>5s}")
    print("-" * 40)
    for cat, scores in sorted(cat_scores.items()):
        avg = sum(scores) / len(scores)
        passed = sum(1 for s in scores if s >= 0.8)
        failed = sum(1 for s in scores if s < 0.5)
        print(f"{cat:<12s} {avg:>5.2f} {len(scores):>5d} {passed:>5d} {failed:>5d}")

    total_tokens = sum(r["completion_tokens"] for r in results)
    total_time = sum(r["elapsed"] for r in results)
    avg_speed = total_tokens / total_time if total_time > 0 else 0
    print(f"\n总token: {total_tokens}, 总时间: {total_time:.1f}s, 平均速度: {avg_speed:.1f} tok/s")

    output = {
        "model": model,
        "label": label,
        "api": API_URL,
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(results),
        "overall_score": round(overall, 2),
        "total_tokens": total_tokens,
        "total_time": round(total_time, 1),
        "avg_speed": round(avg_speed, 1),
        "categories": {cat: round(sum(s)/len(s), 2) for cat, s in sorted(cat_scores.items())},
        "results": results,
    }

    return output


def compare(baseline_3b, eval_7b):
    print(f"\n{'='*70}")
    print("3B vs 7B 对比")
    print(f"{'='*70}")
    print(f"{'类别':<14s} {'3B':>6s} {'7B':>6s} {'Δ':>6s}")
    print("-" * 35)

    all_cats = sorted(set(list(baseline_3b["categories"].keys()) + list(eval_7b["categories"].keys())))
    for cat in all_cats:
        s3 = baseline_3b["categories"].get(cat, 0)
        s7 = eval_7b["categories"].get(cat, 0)
        delta = s7 - s3
        sign = "+" if delta > 0 else ""
        print(f"{cat:<14s} {s3:>6.2f} {s7:>6.2f} {sign}{delta:>5.2f}")

    o3 = baseline_3b["overall_score"]
    o7 = eval_7b["overall_score"]
    delta = o7 - o3
    sign = "+" if delta > 0 else ""
    print(f"{'总分':<14s} {o3:>6.2f} {o7:>6.2f} {sign}{delta:>5.2f}")
    print(f"\n速度: 3B={baseline_3b.get('avg_speed', 'N/A')} tok/s, 7B={eval_7b.get('avg_speed', 'N/A')} tok/s")

    per_test_improvements = []
    per_test_regressions = []
    r3 = {r["id"]: r for r in baseline_3b["results"]}
    r7 = {r["id"]: r for r in eval_7b["results"]}

    for tid in r3:
        if tid in r7:
            d = r7[tid]["score"] - r3[tid]["score"]
            if d > 0:
                per_test_improvements.append((tid, r3[tid]["name"], d))
            elif d < 0:
                per_test_regressions.append((tid, r3[tid]["name"], d))

    if per_test_improvements:
        per_test_improvements.sort(key=lambda x: -x[2])
        print(f"\n最大提升 (7B > 3B):")
        for tid, name, d in per_test_improvements[:5]:
            print(f"  {tid} {name}: +{d:.1f}")

    if per_test_regressions:
        per_test_regressions.sort(key=lambda x: x[2])
        print(f"\n回退 (7B < 3B):")
        for tid, name, d in per_test_regressions[:5]:
            print(f"  {tid} {name}: {d:.1f}")


if __name__ == "__main__":
    eval_7b = run_eval(MODEL_7B, "7B-Q4_K_M")

    out_path = "/home/ai/lingminopt/data/lingai_7b_eval_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(eval_7b, f, ensure_ascii=False, indent=2)
    print(f"\n7B结果已保存: {out_path}")

    baseline_path = "/home/ai/lingminopt/data/lingai_rigorous_test_results.json"
    try:
        with open(baseline_path, "r") as f:
            baseline_3b = json.load(f)
        compare(baseline_3b, eval_7b)

        comparison = {
            "timestamp": datetime.now().isoformat(),
            "baseline_3b": {"model": baseline_3b["model"], "score": baseline_3b["overall_score"]},
            "eval_7b": {"model": eval_7b["model"], "score": eval_7b["overall_score"]},
            "delta": round(eval_7b["overall_score"] - baseline_3b["overall_score"], 2),
            "categories_delta": {},
            "per_test": [],
        }
        for cat in eval_7b["categories"]:
            comparison["categories_delta"][cat] = round(
                eval_7b["categories"].get(cat, 0) - baseline_3b["categories"].get(cat, 0), 2
            )
        r3 = {r["id"]: r for r in baseline_3b["results"]}
        r7 = {r["id"]: r for r in eval_7b["results"]}
        for tid in r7:
            if tid in r3:
                comparison["per_test"].append({
                    "id": tid, "name": r7[tid]["name"],
                    "score_3b": r3[tid]["score"], "score_7b": r7[tid]["score"],
                    "delta": round(r7[tid]["score"] - r3[tid]["score"], 2),
                })

        comp_path = "/home/ai/lingminopt/data/lingai_3b_vs_7b_comparison.json"
        with open(comp_path, "w", encoding="utf-8") as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)
        print(f"对比结果已保存: {comp_path}")
    except FileNotFoundError:
        print(f"\n3B基线未找到({baseline_path})，跳过对比")
