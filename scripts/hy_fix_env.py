#!/usr/bin/env python3
"""Hengyuan Cloud: cleanup + fix env + check GPU."""
import paramiko, os, sys

pass_file = os.path.expanduser("~/.hengyuan_pass")
with open(pass_file) as f:
    password = f.read().strip()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("i-1.gpushare.com", port=27672, username="root", password=password, timeout=15)

def run(cmd, timeout=120):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    return out, err

# Step 1: Cleanup old artifacts
print("=== 1. 清理旧产物 ===")
out, err = run("rm -rf /root/autodl-tmp/lingai-7b-merged /root/autodl-tmp/lingai-7b-reasoning-lora")
print(f"Deleted merged+lora: {out or 'OK'}")

out, err = run("pip cache purge 2>/dev/null; rm -rf ~/.cache/pip /tmp/pip-*; apt-get clean 2>/dev/null; rm -rf /var/cache/apt/archives/*.deb")
print(f"pip/apt cache cleaned: {out or 'OK'}")

out, err = run("df -h / /root/autodl-tmp")
print(f"\n磁盘状态:\n{out}")

# Step 2: Check CUDA version and fix PyTorch
print("\n=== 2. 检查CUDA版本 ===")
out, err = run("nvcc --version 2>/dev/null | tail -1 || echo 'no nvcc'")
print(f"nvcc: {out}")
out, err = run("python3 -c \"import torch; print('torch:', torch.__version__, 'CUDA built:', torch.version.cuda)\"")
print(f"{out}")

# CUDA 12.2 driver, need PyTorch built for cu121
print("\n=== 3. 重装PyTorch (cu121) ===")
out, err = run("pip install torch==2.5.1 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --break-system-packages 2>&1 | tail -5", timeout=300)
print(f"PyTorch install: {out}")

# Step 4: Fix transformers and peft
print("\n=== 4. 重装transformers + peft ===")
out, err = run("pip install transformers==4.46.3 peft trl accelerate bitsandbytes --break-system-packages 2>&1 | tail -5", timeout=120)
print(f"transformers+peft: {out}")

# Step 5: Verify
print("\n=== 5. 验证环境 ===")
out, err = run("""python3 -c '
import torch
print("torch:", torch.__version__, "CUDA:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0), f"{torch.cuda.get_device_properties(0).total_mem/1024**3:.1f}GB")
import transformers; print("transformers:", transformers.__version__)
import peft; print("peft:", peft.__version__)
' 2>&1""")
print(out)

# Step 6: Check if base model exists
print("\n=== 6. 检查基座模型 ===")
out, err = run("ls /root/autodl-tmp/Qwen2.5-Coder-7B-Instruct/ 2>/dev/null | head -5 || echo 'BASE MODEL NOT FOUND'")
print(out)

# Step 7: Check available memory
out, err = run("free -h | head -2")
print(f"\n内存:\n{out}")

ssh.close()
print("\n=== 完成 ===")
