#!/usr/bin/env python3
"""
评估结果对比工具 — 自动对比eval结果差异 + 历史退化检测
用法:
  python3 scripts/eval_diff.py data/eval_v2.json data/eval_v3.json
  python3 scripts/eval_diff.py data/eval_v2.json data/eval_v3.json --detail
  python3 scripts/eval_diff.py --history data/              # 所有eval文件历史趋势
  python3 scripts/eval_diff.py --history data/ --threshold 0.005  # 自定义退化阈值
"""
import json
import sys
from pathlib import Path


def load_report(path):
    with open(path) as f:
        return json.load(f)


def diff_reports(old_path, new_path, detail=False):
    old = load_report(old_path)
    new = load_report(new_path)

    old_by_id = {r["id"]: r for r in old["results"]}
    new_by_id = {r["id"]: r for r in new["results"]}

    all_ids = sorted(set(old_by_id) | set(new_by_id))

    improved = []
    regressed = []
    unchanged_pass = []
    unchanged_fail = []
    new_only = []
    old_only = []

    for tid in all_ids:
        if tid in new_by_id and tid not in old_by_id:
            new_only.append(tid)
            continue
        if tid in old_by_id and tid not in new_by_id:
            old_only.append(tid)
            continue

        o = old_by_id[tid]
        n = new_by_id[tid]
        ds = n["score"] - o["score"]

        if ds > 0:
            improved.append((tid, o, n, ds))
        elif ds < 0:
            regressed.append((tid, o, n, ds))
        elif o["score"] >= 0.8:
            unchanged_pass.append(tid)
        else:
            unchanged_fail.append(tid)

    old_total = old["total_score"]
    new_total = new["total_score"]
    delta = new_total - old_total

    print(f"{'='*60}")
    print("评估对比报告")
    print(f"{'='*60}")
    print(f"旧版: {Path(old_path).name} | {old['model']} | {old_total:.4f} | {old['passed']}/{old['num_tests']}")
    print(f"新版: {Path(new_path).name} | {new['model']} | {new_total:.4f} | {new['passed']}/{new['num_tests']}")
    print(f"总分变化: {delta:+.4f} ({delta*100:+.2f}pp)")
    print()

    print(f"{'─'*40}")
    print(f"统计: {len(improved)}改善 | {len(regressed)}退化 | {len(unchanged_pass)}持续通过 | {len(unchanged_fail)}持续失败")
    print(f"{'─'*40}")

    if regressed:
        print(f"\n🔴 退化 ({len(regressed)}):")
        for tid, o, n, ds in regressed:
            print(f"  {tid} ({o['category']}): {o['score']:.1f}→{n['score']:.1f} ({ds:+.1f})")
            if detail:
                print(f"    旧: {o['response'][:120]}")
                print(f"    新: {n['response'][:120]}")

    if improved:
        print(f"\n🟢 改善 ({len(improved)}):")
        for tid, o, n, ds in improved:
            print(f"  {tid} ({o['category']}): {o['score']:.1f}→{n['score']:.1f} ({ds:+.1f})")
            if detail:
                print(f"    旧: {o['response'][:120]}")
                print(f"    新: {n['response'][:120]}")

    if unchanged_fail:
        print(f"\n🟡 持续失败 ({len(unchanged_fail)}):")
        for tid in unchanged_fail:
            r = new_by_id[tid]
            print(f"  {tid} ({r['category']}): {r['score']:.1f}")

    if new_only:
        print(f"\n加新增题 ({len(new_only)}): {', '.join(new_only)}")
    if old_only:
        print(f"\n减旧题 ({len(old_only)}): {', '.join(old_only)}")

    print(f"\n{'─'*40}")
    print("类别对比:")
    all_cats = sorted(set(old["category_scores"]) | set(new["category_scores"]))
    for cat in all_cats:
        os_ = old["category_scores"].get(cat)
        ns_ = new["category_scores"].get(cat)
        if os_ is not None and ns_ is not None:
            d = ns_ - os_
            marker = "↑" if d > 0 else "↓" if d < 0 else "="
            print(f"  {cat}: {os_:.2f}→{ns_:.2f} {marker}")
        elif os_ is not None:
            print(f"  {cat}: {os_:.2f}→ (removed)")
        else:
            print(f"  {cat}: (new)→{ns_:.2f}")

    print(f"\n{'='*60}")
    return len(regressed) == 0


def load_score_history(directory):
    """从目录中加载所有eval结果的分数历史"""
    pattern = "eval_*83q.json"
    files = sorted(Path(directory).glob(pattern))
    if not files:
        print(f"错误: {directory} 中没有匹配 {pattern} 的文件")
        return []

    history = []
    for f in files:
        try:
            data = json.load(open(f))
            ts = data.get("timestamp", "")
            history.append({
                "file": f.name,
                "model": data.get("model", "unknown"),
                "total_score": data["total_score"],
                "passed": data["passed"],
                "num_tests": data["num_tests"],
                "category_scores": data.get("category_scores", {}),
                "timestamp": ts,
            })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"警告: {f.name} 解析失败: {e}")
    return history


def check_degradation(history, threshold=0.005):
    """检测连续退化：相邻两次总分下降超过阈值"""
    alerts = []
    for i in range(1, len(history)):
        prev = history[i - 1]
        curr = history[i]
        delta = curr["total_score"] - prev["total_score"]
        if delta < -threshold:
            alerts.append({
                "prev_file": prev["file"],
                "curr_file": curr["file"],
                "prev_score": prev["total_score"],
                "curr_score": curr["total_score"],
                "delta": delta,
                "delta_pp": delta * 100,
                "degraded_categories": _degraded_categories(prev, curr),
            })
    return alerts


def _degraded_categories(prev, curr):
    """找出退化的类别"""
    degraded = []
    for cat in prev["category_scores"]:
        if cat in curr["category_scores"]:
            d = curr["category_scores"][cat] - prev["category_scores"][cat]
            if d < 0:
                degraded.append((cat, prev["category_scores"][cat], curr["category_scores"][cat], d))
    return degraded


def print_history(history, threshold=0.005):
    """打印历史趋势 + 退化告警"""
    print(f"{'='*70}")
    print(f"评估历史趋势 ({len(history)} 个结果)")
    print(f"{'='*70}")
    print(f"{'文件':<40} {'模型':<30} {'总分':>6} {'通过':>6}")
    print(f"{'─'*82}")
    for h in history:
        print(f"{h['file']:<40} {h['model']:<30} {h['total_score']:.4f} {h['passed']}/{h['num_tests']}")

    alerts = check_degradation(history, threshold)
    if alerts:
        print(f"\n{'='*70}")
        print(f"🔴 退化告警 ({len(alerts)} 次退化，阈值={threshold*100:.1f}pp)")
        print(f"{'='*70}")
        for a in alerts:
            print(f"  {a['prev_file']} → {a['curr_file']}")
            print(f"    总分: {a['prev_score']:.4f} → {a['curr_score']:.4f} ({a['delta_pp']:+.2f}pp)")
            if a["degraded_categories"]:
                for cat, old_s, new_s, d in a["degraded_categories"]:
                    print(f"    退化类别: {cat}: {old_s:.2f}→{new_s:.2f} ({d:+.2f})")
        print("\n建议: 检查退化版本间的system prompt/知识库变更")
    else:
        print(f"\n✅ 无退化告警 (阈值={threshold*100:.1f}pp)")

    print("\n" + "=" * 70)
    return len(alerts) == 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--history" in args:
        idx = args.index("--history")
        directory = args[idx + 1] if idx + 1 < len(args) and not args[idx + 1].startswith("--") else "."
        threshold = 0.005
        if "--threshold" in args:
            tidx = args.index("--threshold")
            if tidx + 1 < len(args):
                threshold = float(args[tidx + 1])
        history = load_score_history(directory)
        if not history:
            sys.exit(1)
        ok = print_history(history, threshold)
        sys.exit(0 if ok else 1)
    elif len(args) >= 2 and not args[0].startswith("--"):
        detail = "--detail" in args
        ok = diff_reports(args[0], args[1], detail)
        sys.exit(0 if ok else 1)
    else:
        print("用法:")
        print("  python3 eval_diff.py <old.json> <new.json> [--detail]")
        print("  python3 eval_diff.py --history <data_dir> [--threshold 0.005]")
        sys.exit(1)
