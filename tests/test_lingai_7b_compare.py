"""
lingAI 7B vs 3B 对比评估脚本 — 灵极优(lingminopt)
复用 test_lingai_rigorous.py 的41道测试，对比3B基座 vs 7B基座。
用法: python tests/test_lingai_7b_compare.py [--model-7b MODEL_NAME]
"""

import json
import time
import sys
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from test_lingai_rigorous import TESTS, call_api, API_URL, API_KEY, TIMEOUT

MODEL_3B = "lingai-3b-v7-4bit"
MODEL_7B = "lingai-7b-q4km"
RESULTS_DIR = "/home/ai/lingminopt/data"


def run_suite(model_name):
    results = []
    total = len(TESTS)
    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"共 {total} 道测试 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    for i, test in enumerate(TESTS, 1):
        tid = test["id"]
        msgs = test["messages"]

        t0 = time.time()
        headers = {"X-API-Key": API_KEY}
        import requests
        try:
            r = requests.post(API_URL, json={
                "model": model_name,
                "messages": msgs,
                "max_tokens": 512,
                "temperature": 0.3,
            }, headers=headers, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
        except Exception as e:
            content = f"ERROR: {e}"
            prompt_tokens = 0
            completion_tokens = 0

        elapsed = round(time.time() - t0, 2)
        score = test["evaluate"](content)
        score = min(1.0, max(0.0, score))

        results.append({
            "id": tid,
            "category": test["category"],
            "name": test["name"],
            "score": score,
            "elapsed": elapsed,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        })

        status = "✓" if score >= 0.8 else "△" if score >= 0.5 else "✗"
        print(f"  [{i:2d}/{total}] {status} {tid} {test['name']:20s} score={score:.1f} ({elapsed}s)")

    return results


def compare(r3, r7):
    print(f"\n{'='*70}")
    print("3B vs 7B 对比报告")
    print(f"{'='*70}\n")

    by_id_3 = {r["id"]: r for r in r3}
    by_id_7 = {r["id"]: r for r in r7}
    all_ids = [r["id"] for r in r3]

    cats = {}
    for tid in all_ids:
        r3i = by_id_3.get(tid)
        r7i = by_id_7.get(tid)
        if not r3i or not r7i:
            continue
        cat = r3i["category"]
        if cat not in cats:
            cats[cat] = {"3b": [], "7b": []}
        cats[cat]["3b"].append(r3i["score"])
        cats[cat]["7b"].append(r7i["score"])

    print(f"{'类别':<14s} {'3B均分':>7s} {'7B均分':>7s} {'Δ':>7s} {'测试数':>5s}")
    print("-" * 50)
    for cat, scores in sorted(cats.items()):
        avg3 = sum(scores["3b"]) / len(scores["3b"])
        avg7 = sum(scores["7b"]) / len(scores["7b"])
        delta = avg7 - avg3
        sign = "+" if delta > 0 else ""
        print(f"{cat:<14s} {avg3:>7.2f} {avg7:>7.2f} {sign}{delta:>6.2f} {len(scores['3b']):>5d}")

    overall3 = sum(r["score"] for r in r3) / len(r3)
    overall7 = sum(r["score"] for r in r7) / len(r7)
    delta = overall7 - overall3
    sign = "+" if delta > 0 else ""
    print("-" * 50)
    print(f"{'总分':<14s} {overall3:>7.2f} {overall7:>7.2f} {sign}{delta:>6.2f} {len(r3):>5d}")

    improved = sum(1 for tid in all_ids if by_id_7[tid]["score"] > by_id_3[tid]["score"])
    regressed = sum(1 for tid in all_ids if by_id_7[tid]["score"] < by_id_3[tid]["score"])
    unchanged = len(all_ids) - improved - regressed
    print(f"\n逐题对比: 提升 {improved} | 持平 {unchanged} | 退化 {regressed}")

    print(f"\n{'ID':<18s} {'类别':<10s} {'3B':>4s} {'7B':>4s} {'Δ':>5s} {'变化':>6s}")
    print("-" * 55)
    for tid in all_ids:
        s3 = by_id_3[tid]["score"]
        s7 = by_id_7[tid]["score"]
        d = s7 - s3
        arrow = "↑" if d > 0 else "↓" if d < 0 else "→"
        print(f"{tid:<18s} {by_id_3[tid]['category']:<10s} {s3:>4.1f} {s7:>4.1f} {d:>+5.1f} {arrow:>6s}")

    avg_time3 = sum(r["elapsed"] for r in r3) / len(r3)
    avg_time7 = sum(r["elapsed"] for r in r7) / len(r7)
    print(f"\n平均响应时间: 3B={avg_time3:.1f}s, 7B={avg_time7:.1f}s (×{avg_time7/avg_time3:.1f})")

    total_tok3 = sum(r["prompt_tokens"] + r["completion_tokens"] for r in r3)
    total_tok7 = sum(r["prompt_tokens"] + r["completion_tokens"] for r in r7)
    print(f"总Token消耗: 3B={total_tok3:,}, 7B={total_tok7:,}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "model_3b": MODEL_3B,
        "model_7b": MODEL_7B,
        "overall_3b": round(overall3, 3),
        "overall_7b": round(overall7, 3),
        "delta": round(delta, 3),
        "improved": improved,
        "regressed": regressed,
        "unchanged": unchanged,
        "categories": {
            cat: {
                "3b": round(sum(s["3b"]) / len(s["3b"]), 3),
                "7b": round(sum(s["7b"]) / len(s["7b"]), 3),
                "delta": round(sum(s["7b"]) / len(s["7b"]) - sum(s["3b"]) / len(s["3b"]), 3),
            }
            for cat, s in sorted(cats.items())
        },
        "per_test": [
            {
                "id": tid,
                "category": by_id_3[tid]["category"],
                "score_3b": by_id_3[tid]["score"],
                "score_7b": by_id_7[tid]["score"],
                "delta": round(by_id_7[tid]["score"] - by_id_3[tid]["score"], 2),
                "time_3b": by_id_3[tid]["elapsed"],
                "time_7b": by_id_7[tid]["elapsed"],
            }
            for tid in all_ids
        ],
        "performance": {
            "avg_time_3b": round(avg_time3, 2),
            "avg_time_7b": round(avg_time7, 2),
            "total_tokens_3b": total_tok3,
            "total_tokens_7b": total_tok7,
        },
    }

    out_path = f"{RESULTS_DIR}/lingai_7b_vs_3b_comparison.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n对比报告已保存: {out_path}")
    return report


def main():
    model_7b = MODEL_7B
    if len(sys.argv) > 2 and sys.argv[1] == "--model-7b":
        model_7b = sys.argv[2]

    print(f"灵极优 7B vs 3B 对比评估")
    print(f"3B模型: {MODEL_3B}")
    print(f"7B模型: {model_7b}")
    print(f"测试数: {len(TESTS)}")

    print("\n=== Phase 1: 测试 3B 基座 ===")
    r3 = run_suite(MODEL_3B)

    print("\n=== Phase 2: 测试 7B 基座 ===")
    r7 = run_suite(model_7b)

    print("\n=== Phase 3: 生成对比报告 ===")
    compare(r3, r7)


if __name__ == "__main__":
    main()
