"""
lingAI Model Comparison Tool — 灵极优(lingminopt)
对比3B vs 7B基座在41道严格测试上的表现差异。
用法: python tests/compare_3b_7b.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/home/ai/lingminopt/data")


def load_results(model_tag):
    """按model tag查找最新结果文件"""
    candidates = sorted(DATA_DIR.glob(f"lingai_*_results*.json"))
    matched = [f for f in candidates if model_tag in f.stem]
    if not matched:
        print(f"未找到 {model_tag} 的测试结果")
        return None, None
    latest = matched[-1]
    print(f"加载 {model_tag}: {latest}")
    with open(latest, "r", encoding="utf-8") as f:
        return json.load(f), latest


def compare(r3b, r7b, path_3b, path_7b):
    """生成3B vs 7B对比报告"""
    print(f"\n{'='*70}")
    print(f"lingAI 3B vs 7B 对比报告 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*70}")

    score_3b = r3b["overall_score"]
    score_7b = r7b["overall_score"]
    delta = round(score_7b - score_3b, 3)

    print(f"\n总分: 3B={score_3b:.2f}  7B={score_7b:.2f}  差异={delta:+.3f}")

    cats_3b = r3b.get("categories", {})
    cats_7b = r7b.get("categories", {})

    print(f"\n{'类别':<14s} {'3B':>6s} {'7B':>6s} {'差异':>7s} {'判定':>6s}")
    print("-" * 45)

    verdicts = []
    for cat in sorted(set(cats_3b) | set(cats_7b)):
        s3 = cats_3b.get(cat, 0)
        s7 = cats_7b.get(cat, 0)
        d = round(s7 - s3, 3)
        if d > 0.05:
            v = "↑"
        elif d < -0.05:
            v = "↓"
        else:
            v = "→"
        verdicts.append(v)
        print(f"{cat:<14s} {s3:>6.2f} {s7:>6.2f} {d:>+7.3f} {v:>6s}")

    results_3b = {r["id"]: r for r in r3b.get("results", [])}
    results_7b = {r["id"]: r for r in r7b.get("results", [])}

    all_ids = sorted(set(results_3b) | set(results_7b))

    improved = []
    regressed = []
    unchanged = []

    for tid in all_ids:
        s3 = results_3b.get(tid, {}).get("score", 0)
        s7 = results_7b.get(tid, {}).get("score", 0)
        d = round(s7 - s3, 3)
        name = results_3b.get(tid, results_7b.get(tid, {})).get("name", tid)
        entry = {"id": tid, "name": name, "3b": s3, "7b": s7, "delta": d}
        if d > 0.1:
            improved.append(entry)
        elif d < -0.1:
            regressed.append(entry)
        else:
            unchanged.append(entry)

    print(f"\n{'='*70}")
    print("逐题对比")
    print(f"{'='*70}")

    if improved:
        print(f"\n↑ 改善 ({len(improved)}题):")
        for e in sorted(improved, key=lambda x: -x["delta"]):
            print(f"  {e['id']:<20s} {e['3b']:.1f}→{e['7b']:.1f} ({e['delta']:+.1f}) {e['name']}")

    if regressed:
        print(f"\n↓ 退化 ({len(regressed)}题):")
        for e in sorted(regressed, key=lambda x: x["delta"]):
            print(f"  {e['id']:<20s} {e['3b']:.1f}→{e['7b']:.1f} ({e['delta']:+.1f}) {e['name']}")

    if unchanged:
        print(f"\n→ 持平 ({len(unchanged)}题)")

    print(f"\n{'='*70}")
    print("判定标准 (docs/lingai_7b_upgrade_plan.md §五)")
    print(f"{'='*70}")
    targets = {
        "总分": (score_3b, score_7b, 0.85),
        "幻觉检测": (cats_3b.get("幻觉检测", 0), cats_7b.get("幻觉检测", 0), 0.75),
        "SDTH": (cats_3b.get("SDTH", 0), cats_7b.get("SDTH", 0), 0.60),
        "代码Bug": (cats_3b.get("代码Bug", 0), cats_7b.get("代码Bug", 0), 0.70),
        "推理深度": (cats_3b.get("推理深度", 0), cats_7b.get("推理深度", 0), 0.80),
        "代码生成": (cats_3b.get("代码生成", 0), cats_7b.get("代码生成", 0), 0.90),
        "安全拒绝": (cats_3b.get("安全拒绝", 0), cats_7b.get("安全拒绝", 0), 0.90),
    }

    print(f"\n{'指标':<12s} {'3B':>6s} {'7B':>6s} {'目标':>6s} {'达标':>6s}")
    print("-" * 42)
    pass_count = 0
    for label, (s3, s7, target) in targets.items():
        ok = "✓" if s7 >= target else "✗"
        if s7 >= target:
            pass_count += 1
        print(f"{label:<12s} {s3:>6.2f} {s7:>6.2f} {target:>6.2f} {ok:>6s}")

    print(f"\n达标率: {pass_count}/{len(targets)}")

    report = {
        "timestamp": datetime.now().isoformat(),
        "3b": {"model": r3b["model"], "score": score_3b, "file": str(path_3b)},
        "7b": {"model": r7b["model"], "score": score_7b, "file": str(path_7b)},
        "delta": delta,
        "improved": improved,
        "regressed": regressed,
        "targets_met": pass_count,
        "targets_total": len(targets),
    }

    out_path = DATA_DIR / f"comparison_3b_vs_7b_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n对比报告已保存: {out_path}")

    return report


if __name__ == "__main__":
    r3b, p3b = load_results("3b")
    r7b, p7b = load_results("7b")
    if r3b and r7b:
        compare(r3b, r7b, p3b, p7b)
