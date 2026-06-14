#!/usr/bin/env python3
"""对比v2/v3评估结果，找出分数变化"""
import json, sys
from pathlib import Path

def load(p):
    d = json.load(open(p))
    return {x['id']: x for x in d} if isinstance(d, list) else {x['id']: x for x in d.get('results', [])}

v2 = load('data/eval_fewshot_83q_v2.json')
v3_file = sys.argv[1] if len(sys.argv) > 1 else 'data/eval_fewshot_83q_v3.json'
v3 = load(v3_file)

changes = []
for qid in sorted(set(v2) | set(v3)):
    s2 = v2.get(qid, {}).get('score', None)
    s3 = v3.get(qid, {}).get('score', None)
    if s2 is None or s3 is None:
        continue
    if abs(s2 - s3) > 0.01:
        changes.append((qid, v3[qid].get('category',''), s2, s3, s3 - s2))

print(f"v2平均: {sum(x['score'] for x in v2.values())/len(v2):.4f} ({sum(1 for x in v2.values() if x['score']>=0.6)}/{len(v2)}通过)")
print(f"v3平均: {sum(x['score'] for x in v3.values())/len(v3):.4f} ({sum(1 for x in v3.values() if x['score']>=0.6)}/{len(v3)}通过)")
print(f"\n变化题数: {len(changes)}")
if changes:
    print(f"\n{'ID':<12} {'类别':<10} {'v2':>5} {'v3':>5} {'变化':>6}")
    for qid, cat, s2, s3, d in sorted(changes, key=lambda x: x[4]):
        flag = '⬆️' if d > 0 else '⬇️'
        print(f"{qid:<12} {cat:<10} {s2:>5.2f} {s3:>5.2f} {d:>+5.2f} {flag}")
