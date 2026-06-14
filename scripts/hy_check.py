#!/usr/bin/env python3
"""Check Hengyuan Cloud GPU status via SSH."""
import paramiko, os

pass_file = os.path.expanduser("~/.hengyuan_pass")
with open(pass_file) as f:
    password = f.read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect("i-1.gpushare.com", port=27672, username="root", password=password, timeout=15)
    print("=== SSH连接成功 ===")

    commands = [
        ("hostname", "hostname"),
        ("disk", "df -h / /root/autodl-tmp 2>/dev/null"),
        ("gpu", "nvidia-smi 2>/dev/null || echo 'nvidia-smi FAILED'"),
        ("cuda", """python3 -c 'import torch; print("CUDA:", torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A")' 2>&1"""),
        ("transformers", """python3 -c 'import transformers; print("transformers:", transformers.__version__)' 2>&1"""),
        ("peft", """python3 -c 'import peft; print("peft:", peft.__version__)' 2>&1"""),
        ("base_model", "ls /root/autodl-tmp/Qwen2.5-Coder-7B-Instruct/ 2>/dev/null | head -5 || echo 'No base model'"),
        ("train_pkg", "ls /root/autodl-tmp/training_package_7b/ 2>/dev/null || echo 'No training package'"),
        ("old_artifacts", "du -sh /root/autodl-tmp/lingai* 2>/dev/null || echo 'No old artifacts'"),
    ]

    for name, cmd in commands:
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        print(f"\n--- {name} ---")
        if out: print(out[:500])
        if err and len(err) < 200: print(f"STDERR: {err}")

    ssh.close()
except Exception as e:
    print(f"SSH连接失败: {type(e).__name__}: {e}")
