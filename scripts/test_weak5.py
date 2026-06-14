#!/usr/bin/env python3
"""针对性测试5个弱项题，验证few-shot注入效果"""
import json, requests, time, re, sys, os
os.environ['PYTHONUNBUFFERED'] = '1'

# 加载评估器模块获取题目和system prompt
import importlib.util
spec = importlib.util.spec_from_file_location("eval", os.path.join(os.path.dirname(__file__), "eval_unified.py"))
eval_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eval_mod)

weak_ids = ['HALL_07','MATH_05','MATH_02','ZH_03','HSAFE_02']
tests = [t for t in eval_mod.DEDUPED_TESTS if t.get('id','') in weak_ids]
print(f"找到弱项题: {[t['id'] for t in tests]}", flush=True)

system_prompt = eval_mod.SYSTEM_PROMPT
print(f"System prompt长度: {len(system_prompt)} 字符", flush=True)

api_base = "http://localhost:8102/v1"
results = []

for t in tests:
    tid = t['id']
    cat = t.get('category','')
    prompt = t.get('prompt', t.get('question',''))
    print(f"\n[{tid}] {cat}", flush=True)
    print(f"Q: {prompt[:100]}", flush=True)
    t0 = time.time()
    try:
        resp = requests.post(f"{api_base}/chat/completions", json={
            "messages": [
                {"role":"system","content":system_prompt},
                {"role":"user","content":prompt}
            ],
            "max_tokens": 400, "temperature": 0.3
        }, timeout=180)
        answer = resp.json()["choices"][0]["message"]["content"].strip()
        answer = eval_mod.filter_tool_call_format(answer)
        elapsed = time.time() - t0
        print(f"A ({elapsed:.1f}s): {answer[:250]}", flush=True)
        
        # 用题目的eval函数评分（评估器用eval字段非check）
        eval_fn = t.get('eval')
        score = eval_fn(answer) if callable(eval_fn) else 0.0
        results.append({'id':tid,'category':cat,'answer':answer,'score':score,'elapsed':elapsed})
        print(f"SCORE: {score:.2f}", flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        results.append({'id':tid,'category':cat,'answer':str(e),'score':0.0,'elapsed':0})

print("\n" + "="*50, flush=True)
print("结果汇总:", flush=True)
total = 0
for r in results:
    total += r['score']
    print(f"  {r['id']:12s} {r['category']:8s} score={r['score']:.2f} ({r['elapsed']:.0f}s)", flush=True)
avg = total/len(results) if results else 0
print(f"  弱项平均: {avg:.3f} (基线: 0.40)", flush=True)

# 保存结果
with open('data/eval_fewshot_weak5.json','w',encoding='utf-8') as f:
    json.dump({'results':results,'avg':avg,'baseline':0.40}, f, ensure_ascii=False, indent=2)
print("结果已保存到 data/eval_fewshot_weak5.json", flush=True)
