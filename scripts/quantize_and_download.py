#!/usr/bin/env python3
"""Step 1: Quantize merged model to GGUF Q4_K_M on remote"""
import sys, time, os
import paramiko

HOST, PORT = "i-1.gpushare.com", 27672
USER = "root"
with open(os.path.expanduser("~/.hengyuan_pass")) as _f:
    PASSWORD = _f.read().strip()

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=60)

def run(cmd, t=600):
    print(f"$ {cmd[:120]}...")
    _, o, e = c.exec_command(cmd, timeout=t)
    ec = o.channel.recv_exit_status()
    out = o.read().decode()
    err = e.read().decode()
    if out.strip():
        print(out[-2000:])
    if err.strip() and ec != 0:
        print(f"STDERR: {err[-1000:]}")
    return ec, out, err

# Check merged model exists
run("ls -lh /root/autodl-tmp/lingai-7b-merged/*.safetensors | head -5", t=10)

# Install llama-cpp-python with conversion support
print("\n=== Installing llama.cpp ===")
run("pip install llama-cpp-python[server] 2>&1 | tail -3", t=120)

# Convert to GGUF FP16 first, then quantize to Q4_K_M
# Use transformers + llama.cpp convert script
print("\n=== Converting to GGUF FP16 ===")

convert_script = """
import sys
sys.path.insert(0, '/usr/local/lib/python3.11/dist-packages')

from pathlib import Path
import json

# Use convert_hf_to_gguf.py from llama.cpp if available, otherwise manual convert
import subprocess

# Try llama-cpp-convert first
result = subprocess.run(
    ['python3', '-c', 'import llama_cpp; print(lla_cpp.__file__)'],
    capture_output=True, text=True
)
print(f"llama_cpp location: {result.stdout.strip()}")

# Use transformers to save as GGUF
# Actually, let's use the simpler approach: convert with llama-server's built-in tools
# or use the huggingface convert script

# Method: use convert-hf-to-gguf.py from llama.cpp repo
print("Cloning llama.cpp for conversion tools...")
subprocess.run(['git', 'clone', '--depth', '1', 'https://github.com/ggerganov/llama.cpp.git', '/root/autodl-tmp/llama.cpp'], 
               capture_output=True, timeout=120)

print("Installing conversion dependencies...")
subprocess.run(['pip', 'install', '-r', '/root/autodl-tmp/llama.cpp/requirements/requirements-convert_hf_to_gguf.txt'],
               capture_output=True, timeout=120)

print("Converting HF to GGUF FP16...")
result = subprocess.run(
    ['python3', '/root/autodl-tmp/llama.cpp/convert_hf_to_gguf.py',
     '/root/autodl-tmp/lingai-7b-merged',
     '--outfile', '/root/autodl-tmp/lingai-7b-f16.gguf',
     '--outtype', 'f16'],
    capture_output=True, text=True, timeout=1800
)
print(f"Convert stdout: {result.stdout[-500:]}")
print(f"Convert stderr: {result.stderr[-500:]}")
print(f"Convert exit: {result.returncode}")

if result.returncode == 0:
    print("FP16 GGUF created successfully!")
    # Quantize to Q4_K_M
    print("Quantizing to Q4_K_M...")
    result2 = subprocess.run(
        ['/root/autodl-tmp/llama.cpp/llama-quantize',
         '/root/autodl-tmp/lingai-7b-f16.gguf',
         '/root/autodl-tmp/lingai-7b-q4km.gguf',
         'Q4_K_M'],
        capture_output=True, text=True, timeout=1800
    )
    print(f"Quantize stdout: {result2.stdout[-500:]}")
    print(f"Quantize stderr: {result2.stderr[-500:]}")
    print(f"Quantize exit: {result2.returncode}")
else:
    print("FP16 conversion failed, trying alternative method...")
    # Alternative: use GGUF from Qwen2.5 base + apply LoRA directly with gguf-adapter
    print("Trying direct Q4_K_M conversion...")
    result3 = subprocess.run(
        ['python3', '/root/autodl-tmp/llama.cpp/convert_hf_to_gguf.py',
         '/root/autodl-tmp/lingai-7b-merged',
         '--outfile', '/root/autodl-tmp/lingai-7b-q4km.gguf',
         '--outtype', 'q4_k_m'],
        capture_output=True, text=True, timeout=1800
    )
    print(f"Direct Q4 stdout: {result3.stdout[-500:]}")
    print(f"Direct Q4 stderr: {result3.stderr[-500:]}")
    print(f"Direct Q4 exit: {result3.returncode}")
"""

# Write and run the conversion script
_, o, e = c.exec_command(f"cat > /root/autodl-tmp/convert_gguf.py << 'PYEOF'\n{convert_script}\nPYEOF", timeout=10)
o.channel.recv_exit_status()

print("\n=== Running conversion (this takes ~10-15 min) ===")
run("cd /root/autodl-tmp && python3 convert_gguf.py 2>&1", t=1800)

# Verify output
print("\n=== Checking output ===")
run("ls -lh /root/autodl-tmp/lingai-7b-q4km.gguf 2>/dev/null || echo 'GGUF not found'", t=10)
run("ls -lh /root/autodl-tmp/lingai-7b-f16.gguf 2>/dev/null || echo 'F16 not found'", t=10)

c.close()
print("\nDone!")
