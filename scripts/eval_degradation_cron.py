#!/usr/bin/env python3
"""
退化检测 cron 脚本 — 自动运行评估 + 与上次结果对比 + 退化告警。

crontab 用法 (每天 03:00 运行):
  0 3 * * * cd /home/ai/lingminopt && python3 scripts/eval_degradation_cron.py >> /home/ai/lingminopt/logs/degradation_cron.log 2>&1

或通过 LingBus 触发:
  收到 idle_self_drive + degradation_check 指令时执行

环境变量:
  EVAL_MODEL — GGUF 模型路径 (默认 /home/ai/models/qwen2.5-7b-instruct-q4_k_m.gguf)
  EVAL_NGL — GPU layers (默认 20)
  EVAL_CTX — context length (默认 2048)
  EVAL_API — API 地址 (优先于本地模型)
  ALERT_THRESHOLD — 退化告警阈值 pp (默认 0.5)
"""
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

MODEL_PATH = os.environ.get("EVAL_MODEL", "/home/ai/models/qwen2.5-7b-instruct-q4_k_m.gguf")
EVAL_NGL = int(os.environ.get("EVAL_NGL", "20"))
EVAL_CTX = int(os.environ.get("EVAL_CTX", "4096"))
EVAL_API = os.environ.get("EVAL_API", "")
ALERT_THRESHOLD = float(os.environ.get("ALERT_THRESHOLD", "0.5")) / 100


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def find_latest_eval(data_dir):
    """找到最新的 eval_*83q.json 文件"""
    files = sorted(data_dir.glob("eval_*83q.json"))
    if not files:
        # 也检查 eval_public_* 格式
        files = sorted(data_dir.glob("eval_public_*.json"))
    return files[-1] if files else None


def run_eval():
    """运行 eval_unified.py"""
    sys.path.insert(0, str(SCRIPT_DIR))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = DATA_DIR / f"eval_cron_{timestamp}_83q.json"

    log(f"开始评估 | 模型: {MODEL_PATH}")

    if EVAL_API:
        log(f"使用 API: {EVAL_API}")
        import subprocess
        cmd = [
            sys.executable, str(SCRIPT_DIR / "eval_unified.py"),
            "--api", EVAL_API,
            "--name", f"cron-check-{timestamp}",
            "--output", str(output_path),
        ]
    else:
        import subprocess
        cmd = [
            sys.executable, str(SCRIPT_DIR / "eval_unified.py"),
            "--model", MODEL_PATH,
            "--name", f"cron-check-{timestamp}",
            "--ngl", str(EVAL_NGL),
            "--ctx", str(EVAL_CTX),
            "--output", str(output_path),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode != 0:
        log(f"ERROR: 评估失败\n{result.stderr}")
        return None

    log(f"评估完成: {output_path}")
    return output_path


def check_degradation(new_path):
    """与上次评估结果对比"""
    # 找到上一个评估文件（排除当前这个）
    all_evals = sorted(DATA_DIR.glob("eval_*83q.json"))
    prev_evals = [f for f in all_evals if f != new_path]
    if not prev_evals:
        log("无历史评估文件，跳过退化检测")
        return None

    prev_path = prev_evals[-1]
    log(f"对比: {prev_path.name} → {new_path.name}")

    with open(prev_path) as f:
        prev = json.load(f)
    with open(new_path) as f:
        curr = json.load(f)

    prev_score = prev.get("total_score", 0)
    curr_score = curr.get("total_score", 0)
    delta = curr_score - prev_score
    delta_pp = delta * 100

    log(f"分数: {prev_score:.4f} → {curr_score:.4f} ({delta_pp:+.2f}pp)")

    # 退化检测
    degraded_categories = []
    if delta < -ALERT_THRESHOLD:
        log(f"⚠️ 退化告警! 下降 {abs(delta_pp):.2f}pp (阈值 {ALERT_THRESHOLD*100:.1f}pp)")
        prev_cats = prev.get("category_scores", {})
        curr_cats = curr.get("category_scores", {})
        for cat in prev_cats:
            if cat in curr_cats:
                cat_delta = curr_cats[cat] - prev_cats[cat]
                if cat_delta < 0:
                    degraded_categories.append({
                        "category": cat,
                        "prev": prev_cats[cat],
                        "curr": curr_cats[cat],
                        "delta": round(cat_delta, 4),
                    })
        for dc in degraded_categories:
            log(f"  退化类别: {dc['category']}: {dc['prev']:.2f}→{dc['curr']:.2f} ({dc['delta']:+.4f})")
    else:
        log("✅ 无退化告警")

    return {
        "degraded": delta < -ALERT_THRESHOLD,
        "prev_score": prev_score,
        "curr_score": curr_score,
        "delta": delta,
        "delta_pp": round(delta_pp, 2),
        "degraded_categories": degraded_categories,
        "timestamp": datetime.now().isoformat(),
    }


def main():
    log("=" * 50)
    log("退化检测 cron 启动")
    log("=" * 50)

    # Step 1: 运行评估
    new_eval = run_eval()
    if not new_eval:
        log("评估失败，退出")
        sys.exit(1)

    # Step 2: 退化检测
    result = check_degradation(new_eval)

    # Step 3: 写入结果摘要
    if result:
        summary_path = LOG_DIR / "degradation_last_result.json"
        with open(summary_path, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log(f"结果摘要: {summary_path}")

        if result["degraded"]:
            log("建议: 检查最近 system prompt / 知识库 / 模型变更")
            sys.exit(2)  # 退出码2表示退化告警

    log("cron 完成")


if __name__ == "__main__":
    main()
