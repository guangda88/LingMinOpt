#!/usr/bin/env python3
"""Upload Qwen2.5-Coder-7B-Instruct model to 恒源云 + restart training"""
import sys, time, os
from pathlib import Path
import paramiko

HOST, PORT = "i-1.gpushare.com", 27672
USER = "root"
with open(os.path.expanduser("~/.hengyuan_pass")) as _f:
    PASSWORD = _f.read().strip()
LOCAL_MODEL = Path("/home/ai/models/Qwen2.5-Coder-7B-Instruct")
REMOTE_MODEL = "/root/.cache/huggingface/hub/models--Qwen--Qwen2.5-Coder-7B-Instruct/snapshots/main"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=60)
sftp = c.open_sftp()

def mkdirs(path):
    parts = path.strip("/").split("/")
    for i in range(2, len(parts)+1):
        try: sftp.mkdir("/" + "/".join(parts[:i]))
        except: pass

# Clean old partial cache
print("Cleaning old cache...", flush=True)
c.exec_command("rm -rf /root/.cache/huggingface/hub/models--Qwen--Qwen2.5-Coder-7B-Instruct 2>/dev/null", timeout=30)

# Upload all model files
files = list(LOCAL_MODEL.iterdir())
total = len(files)
for i, f in enumerate(files, 1):
    remote_path = f"{REMOTE_MODEL}/{f.name}"
    mkdirs(str(Path(remote_path).parent))
    size_mb = f.stat().st_size / 1024 / 1024
    print(f"[{i}/{total}] {f.name} ({size_mb:.0f}MB)...", flush=True)
    t0 = time.time()
    sftp.put(str(f), remote_path, confirm=False)
    elapsed = time.time() - t0
    speed = size_mb / elapsed if elapsed > 0 else 0
    print(f"  {elapsed:.0f}s @ {speed:.0f}MB/s", flush=True)

# Create blobs symlinks for HF cache
print("\nSetting up HF cache structure...", flush=True)
setup_cmd = """
cd /root/.cache/huggingface/hub/models--Qwen--Qwen2.5-Coder-7B-Instruct
mkdir -p blobs refs

# Create blobs from snapshots files
for f in snapshots/main/*; do
  basename=$(basename "$f")
  if [ -f "$f" ]; then
    # Compute hash if .safetensors or .json
    if echo "$basename" | grep -qE '\.(safetensors|json)$'; then
      hash=$(sha256sum "$f" | cut -d' ' -f1)
      if [ ! -f "blobs/$hash" ]; then
        ln -sf "../snapshots/main/$basename" "blobs/$hash"
      fi
    fi
  fi
done

# Create ref
echo "main" > refs/main

# Also point local models dir
rm -f /root/autodl-tmp/models/Qwen/Qwen2.5-Coder-7B-Instruct
ln -sf /root/.cache/huggingface/hub/models--Qwen--Qwen2.5-Coder-7B-Instruct/snapshots/main /root/autodl-tmp/models/Qwen/Qwen2.5-Coder-7B-Instruct

echo "Setup done"
"""
stdin, stdout, stderr = c.exec_command(setup_cmd, timeout=120)
print(stdout.read().decode().strip(), flush=True)
err = stderr.read().decode().strip()
if err: print(f"ERR: {err[:200]}", flush=True)

sftp.close()

# Start training with local model
print("\nStarting training...", flush=True)
train_cmd = (
    f"cd /root/autodl-tmp/lingminopt && "
    f"HF_HOME=/root/.cache/huggingface "
    f"DATA_ROOT=/root/autodl-tmp/lingresearch "
    f"OUTPUT_DIR=/root/autodl-tmp/lingai-7b-reasoning-lora "
    f"nohup python3 scripts/train_lingai_7b_reasoning_lora.py "
    f"> /root/autodl-tmp/train.log 2>&1 &"
)
c.exec_command("pkill -f train_lingai_7b 2>/dev/null; sleep 2", timeout=15)
c.exec_command(train_cmd, timeout=15)

time.sleep(10)
_, stdout, _ = c.exec_command("ps aux | grep train_lingai | grep -v grep | head -2", timeout=10)
print(f"PID: {stdout.read().decode().strip()[:100]}", flush=True)
_, stdout, _ = c.exec_command("tail -15 /root/autodl-tmp/train.log", timeout=10)
print(f"Log:\n{stdout.read().decode().strip()}", flush=True)

c.close()
print("\nDone", flush=True)
