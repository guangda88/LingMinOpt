#!/usr/bin/env python3
"""Upload files + run training on 恒源云"""
import sys, time, os
from pathlib import Path
import paramiko

HOST, PORT = "i-1.gpushare.com", 27672
USER = "root"
with open(os.path.expanduser("~/.hengyuan_pass")) as _f:
    PASSWORD = _f.read().strip()
LOCAL = Path("/home/ai/lingminopt")
REMOTE = "/root/autodl-tmp/lingminopt"
OUT = "/root/autodl-tmp/lingai-7b-reasoning-lora"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=60)

def run(cmd, t=600):
    _, o, e = c.exec_command(cmd, timeout=t)
    ec = o.channel.recv_exit_status()
    return ec, o.read().decode(), e.read().decode()

sftp = c.open_sftp()

# Upload files
print("Uploading...", flush=True)
files = [
    (str(LOCAL/"scripts/train_lingai_7b_reasoning_lora.py"), f"{REMOTE}/scripts/"),
    (str(LOCAL/"data/training/phase4_reasoning_depth.jsonl"), f"{REMOTE}/data/training/"),
    (str(Path("/home/ai/lingresearch/data/training_dataset/merged/merged_all.jsonl")), "/root/autodl-tmp/lingresearch/merged/"),
]
for local, remote_dir in files:
    parts = remote_dir.strip("/").split("/")
    for i in range(2, len(parts)+1):
        try: sftp.mkdir("/" + "/".join(parts[:i]))
        except: pass
    sftp.put(local, remote_dir + Path(local).name)
    print(f"  {Path(local).name}", flush=True)

sftp.close()
c.close()
print("Upload done, running training via nohup...", flush=True)

# Reconnect and start training
c2 = paramiko.SSHClient()
c2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c2.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=60)

# Run training in background, log to file
train_cmd = (
    f"cd {REMOTE} && "
    f"DATA_ROOT=/root/autodl-tmp/lingresearch "
    f"OUTPUT_DIR={OUT} "
    f"nohup python3 scripts/train_lingai_7b_reasoning_lora.py "
    f"> /root/autodl-tmp/train.log 2>&1 &"
)
_, stdout, stderr = c2.exec_command(train_cmd, timeout=30)
ec = stdout.channel.recv_exit_status()
print(f"Training started (exit={ec})", flush=True)

# Wait a moment then check
import time; time.sleep(5)
_, stdout, _ = c2.exec_command("ps aux | grep train_lingai | grep -v grep", timeout=10)
pid_info = stdout.read().decode().strip()
print(f"PID info: {pid_info}", flush=True)
_, stdout, _ = c2.exec_command("tail -5 /root/autodl-tmp/train.log", timeout=10)
log_tail = stdout.read().decode().strip()
print(f"Log:\n{log_tail}", flush=True)

c2.close()
