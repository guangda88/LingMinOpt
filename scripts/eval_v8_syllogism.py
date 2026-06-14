"""V8 LoRA 三段论评估 — 灵研12道三段论基准"""
import json, os, time
from llama_cpp import Llama

BASE_GGUF = "/home/ai/models/lingai-7b-Q4_K_M.gguf"
LORA_GGUF = "/home/ai/models/v8-lora-qwen2.gguf"
OUTPUT = "/home/ai/lingminopt/data/lingai_7b_v8_syllogism_results.json"

QUESTIONS = [
    {"id":"SYL-001","type":"undistributed_middle","is_valid":False,
     "prompt":"所有的猫都是动物。有些动物是黑色的。能否推出\"有些猫是黑色的\"？"},
    {"id":"SYL-002","type":"affirming_consequent","is_valid":False,
     "prompt":"如果下雨，地面会湿。地面湿了。能否推出\"下过雨\"？"},
    {"id":"SYL-003","type":"denying_antecedent","is_valid":False,
     "prompt":"如果下雨，地面会湿。没下雨。能否推出\"地面没有湿\"？"},
    {"id":"SYL-004","type":"undistributed_middle","is_valid":False,
     "prompt":"所有哺乳动物都用肺呼吸。有些用肺呼吸的生物是鱼（肺鱼）。能否推出\"有些哺乳动物是鱼\"？"},
    {"id":"SYL-005","type":"affirming_consequent","is_valid":False,
     "prompt":"如果一个人发烧了，他的体温会升高。小明体温升高了。能否推出\"小明发烧了\"？"},
    {"id":"SYL-006","type":"denying_antecedent","is_valid":False,
     "prompt":"如果使用缓存，查询会变快。我们没有使用缓存。能否推出\"查询不快\"？"},
    {"id":"SYL-007","type":"barbara","is_valid":True,
     "prompt":"所有人都会死。苏格拉底是人。能否推出\"苏格拉底会死\"？"},
    {"id":"SYL-008","type":"cesare","is_valid":True,
     "prompt":"没有鱼是哺乳动物。鲸鱼是哺乳动物。能否推出\"没有鲸鱼是鱼\"？"},
    {"id":"SYL-009","type":"barbara","is_valid":True,
     "prompt":"所有正方形都是矩形。所有矩形都有四个直角。能否推出\"所有正方形都有四个直角\"？"},
    {"id":"SYL-010","type":"modus_tollens","is_valid":True,
     "prompt":"如果A那么B。非B。能否推出\"非A\"？"},
    {"id":"SYL-011","type":"modus_ponens","is_valid":True,
     "prompt":"如果下雨我就带伞。下雨了。能否推出\"我带伞了\"？"},
    {"id":"SYL-012","type":"barbara","is_valid":True,
     "prompt":"所有质数大于1。2是质数。能否推出\"2大于1\"？"},
]

def evaluate(q, resp):
    r = resp.strip()
    if q["is_valid"]:
        if "能推出" in r: return True, "correct_accept"
        elif "不能推出" in r: return False, "wrong_reject"
        else: return False, "ambiguous"
    else:
        if "不能推出" in r: return True, "correct_reject"
        elif "能推出" in r: return False, "wrong_accept"
        else: return False, "ambiguous"

def main():
    print("=== V8 LoRA Syllogism Eval (12 tests) ===")
    t0 = time.time()
    llm = Llama(model_path=BASE_GGUF, lora_path=LORA_GGUF,
                n_ctx=2048, n_gpu_layers=20, n_threads=4, verbose=False)
    print(f"Loaded in {time.time()-t0:.0f}s")

    results = []
    fallacy_correct = 0
    valid_correct = 0

    for i, q in enumerate(QUESTIONS):
        t1 = time.time()
        resp = llm.create_chat_completion(messages=[
            {"role":"system","content":"你是灵族AI助手。回复简洁，直接给答案。"},
            {"role":"user","content":q["prompt"]}
        ], max_tokens=150, temperature=0.3)
        content = resp["choices"][0]["message"]["content"].strip()
        elapsed = time.time() - t1

        correct, verdict = evaluate(q, content)
        if correct:
            if q["is_valid"]: valid_correct += 1
            else: fallacy_correct += 1

        status = "PASS" if correct else "FAIL"
        print(f"  [{i+1:02d}/12] {status} {q['id']} ({q['type']}, {'有效' if q['is_valid'] else '谬误'}): {verdict} ({elapsed:.1f}s)")
        print(f"         → {content[:120]}{'...' if len(content)>120 else ''}")

        results.append({
            "id": q["id"], "type": q["type"], "is_valid": q["is_valid"],
            "prompt": q["prompt"], "response": content,
            "correct": correct, "verdict": verdict, "elapsed": round(elapsed,1),
        })

    total = fallacy_correct + valid_correct
    print(f"\n=== Syllogism Results ===")
    print(f"谬误拒绝: {fallacy_correct}/6")
    print(f"有效接受: {valid_correct}/6")
    print(f"总分: {total}/12 ({total/12*100:.0f}%)")
    print(f"Time: {time.time()-t0:.0f}s")

    report = {
        "model": "lingai-7b-v8-lora",
        "test": "syllogism",
        "fallacy_reject": f"{fallacy_correct}/6",
        "valid_accept": f"{valid_correct}/6",
        "total": f"{total}/12",
        "score": round(total/12, 4),
        "results": results,
    }
    with open(OUTPUT, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Saved: {OUTPUT}")

if __name__ == "__main__":
    main()
