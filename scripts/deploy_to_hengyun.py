#!/usr/bin/env python3
"""部署 lingAI 7B 推理深度微调到恒源云 + 自动下载"""
import sys, time, os
from pathlib import Path
import paramiko

HOST, PORT = "i-1.gpushare.com", 27672
with open(os.path.expanduser("~/.hengyuan_pass")) as _f:
    PASSWORD = _f.read().strip()
USER = "root"
LOCAL = Path("/home/ai/lingminopt")
REMOTE = "/root/autodl-tmp/lingminopt"
OUT = "/root/autodl-tmp/lingai-7b-reasoning-lora"
LOCAL_OUT = Path("/home/ai/models")

FILES = [
    (str(LOCAL/"scripts/train_lingai_7b_reasoning_lora.py"),
     f"{REMOTE}/scripts/train_lingai_7b_reasoning_lora.py"),
    (str(LOCAL/"data/training/phase4_reasoning_depth.jsonl"),
     f"{REMOTE}/data/training/phase4_reasoning_depth.jsonl"),
    (str(Path("/home/ai/lingresearch/data/training_dataset/merged/merged_all.jsonl")),
     "/root/autodl-tmp/lingresearch/merged/merged_all.jsonl"),
]

def log(m): print(m, flush=True)

def ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log(f"连接 {HOST}:{PORT} ...")
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=60)
    return c

def run(cli, cmd, t=3600):
    log(f"> {cmd[:100]}")
    _, stdout, stderr = cli.exec_command(cmd, timeout=t)
    c = stdout.channel.recv_exit_status()
    o, e = stdout.read().decode().strip(), stderr.read().decode().strip()
    if o: log(o[:3000])
    if e and c: log(f"ERR: {e[:300]}")
    return c, o

def mkdirs(sftp, path):
    parts = path.strip("/").split("/")
    for i in range(2, len(parts)+1):
        d = "/" + "/".join(parts[:i])
        try: sftp.mkdir(d)
        except: pass

def main():
    t0 = time.time()
    cli = ssh()
    sftp = cli.open_sftp()
    try:
        # === Upload ===
        log("\n=== 1/3 上传文件 ===")
        for local, remote in FILES:
            mkdirs(sftp, str(Path(remote).parent))
            sftp.put(local, remote)
            log(f"  {Path(local).name} ({Path(local).stat().st_size/1024:.0f} KB)")

        # === Install deps ===
        log("\n=== 2/3 安装依赖 + 训练 ===")
        run(cli, "pip install -U torch transformers peft trl accelerate datasets bitsandbytes -q 2>&1 | tail -3", 300)

        # === Train (blocking, streams output) ===
        cmd = (f"cd {REMOTE} && DATA_ROOT=/root/autodl-tmp/lingresearch "
               f"OUTPUT_DIR={OUT} python3 scripts/train_lingai_7b_reasoning_lora.py")
        stdin, stdout, stderr = cli.exec_command(cmd, timeout=7200)
        for line in iter(stdout.readline, ""):
            if line.strip(): log(line.rstrip())
        ec = stdout.channel.recv_exit_status()
        err = stderr.read().decode().strip()
        if ec:
            log(f"训练退出码={ec}")
            if err: log(f"ERR: {err[:300]}")
            return

        # === Merge + Quantize ===
        log("\n=== 合并 + 量化 ===")
        merge = f"""
cd /root/autodl-tmp
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
base = 'Qwen/Qwen2.5-Coder-7B-Instruct'
t = AutoTokenizer.from_pretrained(base, trust_remote_code=True)
m = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.bfloat16, device_map='auto', trust_remote_code=True)
m = PeftModel.from_pretrained(m, '{OUT}')
m = m.merge_and_unload()
m.save_pretrained('/root/autodl-tmp/lingai-7b-merged')
t.save_pretrained('/root/autodl-tmp/lingai-7b-merged')
print('合并完成')
"
pip install llama-cpp-python -q 2>&1 | tail -1
python3 -m llama_cpp.convert /root/autodl-tmp/lingai-7b-merged --outtype q4_k_m --outfile /root/autodl-tmp/lingai-7b-reasoning-q4km.gguf 2>&1 || echo "GGUF转换跳过"
tar czf /root/autodl-tmp/lingai-7b-reasoning-output.tar.gz /root/autodl-tmp/lingai-7b-merged /root/autodl-tmp/lingai-7b-reasoning-q4km.gguf {OUT} 2>/dev/null
ls -lh /root/autodl-tmp/lingai-7b-reasoning-output.tar.gz
"""
        run(cli, merge, 1800)

        # === Download ===
        log("\n=== 3/3 下载 ===")
        LOCAL_OUT.mkdir(parents=True, exist_ok=True)
        for name in ["lingai-7b-reasoning-q4km.gguf", "train.log"]:
            rp = f"/root/autodl-tmp/{name}"
            try:
                sftp.stat(rp)
                lp = LOCAL_OUT / name
                log(f"  下载 {name} ...")
                sftp.get(rp, str(lp))
                log(f"    -> {lp}")
            except: pass
        # LoRA
        try:
            lr = LOCAL_OUT / "lingai-7b-reasoning-lora"
            lr.mkdir(exist_ok=True)
            for f in sftp.listdir(OUT):
                sftp.get(f"{OUT}/{f}", str(lr/f))
            log(f"  -> {lr}")
        except: pass
        # log
        try:
            sftp.get("/root/autodl-tmp/train.log", str(LOCAL_OUT/"train_7b_reasoning.log"))
        except: pass

        log(f"\n✅ 完成! {(time.time()-t0)/60:.1f}分")
    finally:
        sftp.close()
        cli.close()

if __name__ == "__main__":
    main()
