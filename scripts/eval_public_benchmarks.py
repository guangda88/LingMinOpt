#!/usr/bin/env python3
"""
公开 Benchmark 评测（离线版）— 从内嵌JSON加载标准题目，无需网络。

支持基准: gsm8k, mmlu, humaneval

用法:
  python3 eval_public_benchmarks.py --model /path/to/model.gguf --name model_name --ngl 20
  python3 eval_public_benchmarks.py --api http://localhost:8102/v1 --name model_name
  python3 eval_public_benchmarks.py --model model.gguf --benchmarks gsm8k mmlu

环境变量:
  MODEL_PATH, MODEL_NAME, N_GPU_LAYERS (默认 0), N_CTX (默认 2048)
  API_BASE, BENCHMARKS (空格分隔), NUM_SAMPLES
"""
import json, os, re, sys, time, argparse
from pathlib import Path
from datetime import datetime

BENCH_DIR = Path(__file__).parent.parent / "data" / "benchmarks"

BENCHMARK_FILES = {
    "gsm8k": "gsm8k_sample.json",
    "mmlu": "mmlu_sample.json",
    "humaneval": "humaneval_sample.json",
}


def load_benchmark(name):
    fpath = BENCH_DIR / BENCHMARK_FILES[name]
    if not fpath.exists():
        print(f"ERROR: 基准文件不存在: {fpath}")
        sys.exit(1)
    with open(fpath) as f:
        tests = json.load(f)
    for t in tests:
        t["benchmark"] = name
        if "category" not in t:
            t["category"] = t.get("subject", name)
    return tests


# ============================================================
# 评分函数
# ============================================================

def score_gsm8k(response, gold):
    numbers = re.findall(r'-?[\d,]+\.?\d*', response.replace(",", ""))
    if not numbers:
        return 0.0
    try:
        predicted = float(numbers[-1])
        gold_num = float(gold)
        return 1.0 if abs(predicted - gold_num) < 1e-4 else 0.0
    except ValueError:
        return 0.0


def score_mmlu(response, gold):
    response_upper = response.strip().upper()
    match = re.search(r'\b([ABCD])\b', response_upper)
    if not match:
        if response_upper and response_upper[0] in "ABCD":
            return 1.0 if response_upper[0] == gold.upper() else 0.0
        return 0.0
    predicted = match.group(1)
    return 1.0 if predicted == gold.upper() else 0.0


def score_humaneval(response, gold, entry_point=""):
    has_def = bool(re.search(r'def\s+\w+\s*\(', response))
    has_return = "return" in response.lower()
    has_entry = entry_point.lower() in response.lower() if entry_point else True
    if has_def and has_return and has_entry:
        return 1.0
    elif has_def:
        return 0.5
    return 0.0


SCORERS = {
    "gsm8k": lambda t, r: score_gsm8k(r, t["gold"]),
    "mmlu": lambda t, r: score_mmlu(r, t["gold"]),
    "humaneval": lambda t, r: score_humaneval(r, t.get("gold", ""), t.get("entry_point", "")),
}


# ============================================================
# 推理引擎
# ============================================================

SYS_GENERAL = "You are a helpful assistant. Solve the problem step by step. Be concise. End with 'Answer: X' where X is the final number."
SYS_CODE = "You are an expert Python programmer. Complete the function implementation. Write only code."
SYS_CHOICE = "You are a helpful assistant. Answer the multiple choice question with a single letter (A, B, C, or D)."


def init_llama(model_path, ngl, ctx):
    from llama_cpp import Llama
    print(f"加载模型: {model_path} (n_gpu_layers={ngl}, n_ctx={ctx})...", flush=True)
    t0 = time.time()
    llm = Llama(model_path=model_path, n_ctx=ctx, n_gpu_layers=ngl, verbose=False)
    print(f"  耗时: {time.time()-t0:.0f}s", flush=True)
    return llm


def query_llama(llm, prompt, benchmark):
    sys_map = {"gsm8k": SYS_GENERAL, "mmlu": SYS_CHOICE, "humaneval": SYS_CODE}
    system = sys_map.get(benchmark, SYS_GENERAL)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    resp = llm.create_chat_completion(messages=messages, max_tokens=768, temperature=0.0)
    return resp["choices"][0]["message"]["content"].strip()


def query_api(api_base, prompt, benchmark):
    import requests
    sys_map = {"gsm8k": SYS_GENERAL, "mmlu": SYS_CHOICE, "humaneval": SYS_CODE}
    system = sys_map.get(benchmark, SYS_GENERAL)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    resp = requests.post(f"{api_base}/chat/completions",
                         json={"messages": messages, "max_tokens": 512, "temperature": 0.0},
                         timeout=120)
    return resp.json()["choices"][0]["message"]["content"].strip()


# ============================================================
# 主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="公开 Benchmark 评测（离线版）")
    parser.add_argument("--model", help="GGUF model path")
    parser.add_argument("--name", default="unknown")
    parser.add_argument("--ngl", type=int, default=0)
    parser.add_argument("--ctx", type=int, default=2048)
    parser.add_argument("--api", help="API base URL")
    parser.add_argument("--benchmarks", nargs="+", default=["gsm8k", "mmlu"],
                        choices=list(BENCHMARK_FILES.keys()))
    parser.add_argument("--num-samples", type=int, default=0, help="每基准采样题数 (0=全部)")
    parser.add_argument("--output", help="输出 JSON 路径")
    args = parser.parse_args()

    model_path = args.model or os.environ.get("MODEL_PATH", "")
    model_name = args.name or os.environ.get("MODEL_NAME", "unknown")
    ngl = args.ngl or int(os.environ.get("N_GPU_LAYERS", "0"))
    ctx = args.ctx or int(os.environ.get("N_CTX", "2048"))
    api_base = args.api or os.environ.get("API_BASE", "")
    num_samples = args.num_samples or int(os.environ.get("NUM_SAMPLES", "0"))
    output = args.output or str(
        Path(__file__).parent.parent / "data" /
        f"eval_public_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    )

    # 加载数据
    all_tests = []
    for bench in args.benchmarks:
        tests = load_benchmark(bench)
        if num_samples and num_samples > 0:
            tests = tests[:num_samples]
        all_tests.extend(tests)
        print(f"  {bench}: {len(tests)} 题", flush=True)

    print(f"\n总计 {len(all_tests)} 题 | 模型: {model_name}", flush=True)
    print("=" * 60, flush=True)

    # 初始化引擎
    llm = None
    if api_base:
        print(f"使用 API: {api_base}", flush=True)
    else:
        if not model_path:
            print("ERROR: 需要 --model 或 MODEL_PATH")
            sys.exit(1)
        llm = init_llama(model_path, ngl, ctx)

    # 评测
    t_start = time.time()
    results = []
    bench_scores = {}

    for i, test in enumerate(all_tests):
        bench = test["benchmark"]
        t1 = time.time()
        try:
            if llm:
                response = query_llama(llm, test["prompt"], bench)
            else:
                response = query_api(api_base, test["prompt"], bench)
        except Exception as e:
            response = f"ERROR: {e}"
        elapsed = time.time() - t1

        score = SCORERS[bench](test, response)
        bench_scores.setdefault(bench, []).append(score)
        status = "PASS" if score >= 0.8 else "WARN" if score >= 0.5 else "FAIL"
        print(f"  [{i+1:03d}/{len(all_tests)}] {status} {test['id']}: {score:.2f} ({elapsed:.1f}s)", flush=True)
        results.append({
            "id": test["id"], "benchmark": bench,
            "category": test.get("category", bench),
            "prompt": test["prompt"][:300],
            "response": response[:500],
            "gold": str(test.get("gold", ""))[:200],
            "score": score, "elapsed": round(elapsed, 1),
        })

    total = sum(s for scores in bench_scores.values() for s in scores) / len(all_tests) if all_tests else 0

    print(f"\n{'='*60}", flush=True)
    print(f"模型: {model_name}", flush=True)
    print(f"总分: {total:.4f}", flush=True)
    print(f"总耗时: {(time.time()-t_start)/60:.1f}分", flush=True)
    print("\n按基准:", flush=True)
    bench_summary = {}
    for bench, scores in sorted(bench_scores.items()):
        avg = sum(scores) / len(scores)
        passed = sum(1 for s in scores if s >= 0.8)
        bench_summary[bench] = {"score": round(avg, 4), "passed": passed, "total": len(scores)}
        print(f"  {bench}: {avg:.4f} ({passed}/{len(scores)} passed)", flush=True)

    report = {
        "model": model_name,
        "benchmarks": args.benchmarks,
        "num_tests": len(all_tests),
        "total_score": round(total, 4),
        "benchmark_scores": bench_summary,
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {output}", flush=True)


if __name__ == "__main__":
    main()
