"""将合并后的V8模型转换为GGUF Q4_K_M格式"""
import subprocess, sys, os

MERGED_DIR = "/home/ai/models/lingai-7b-v8-merged"
OUTPUT_GGUF = "/home/ai/models/lingai-7b-v8-Q4_K_M.gguf"
LLAMA_CPP_DIR = "/home/ai/.local/lib/python3.12/site-packages/llama_cpp/llama.cpp"

# 方法1: 使用llama-cpp-python内置的convert脚本
# 方法2: 使用gguf库直接转换
# 方法3: 使用llama.cpp的convert-hf-to-gguf.py

print("=== V8 GGUF Convert ===")

# 查找convert-hf-to-gguf脚本
convert_script = None
candidates = [
    os.path.join(LLAMA_CPP_DIR, "convert_hf_to_gguf.py"),
    os.path.join(LLAMA_CPP_DIR, "convert-hf-to-gguf.py"),
    os.path.join(LLAMA_CPP_DIR, "examples", "convert-hf-to-gguf.py"),
]
for c in candidates:
    if os.path.exists(c):
        convert_script = c
        break

if not convert_script:
    # 搜索
    import glob
    results = glob.glob("/home/ai/.local/lib/python3.12/site-packages/llama_cpp/**/convert*gguf*", recursive=True)
    if results:
        convert_script = results[0]
    else:
        # 搜索pypi gguf包的转换脚本
        results = glob.glob("/home/ai/lingminopt/.venv-v8eval/lib/**/convert*gguf*", recursive=True)
        if results:
            convert_script = results[0]

if convert_script:
    print(f"Found convert script: {convert_script}")
    # 先转换到fp16 GGUF
    fp16_output = "/home/ai/models/lingai-7b-v8-f16.gguf"
    cmd = [
        sys.executable, convert_script,
        MERGED_DIR,
        "--outfile", fp16_output,
        "--outtype", "f16",
    ]
    print(f"Running: {' '.join(cmd)}")
    ret = subprocess.run(cmd)
    if ret.returncode != 0:
        print(f"ERROR: convert failed with code {ret.returncode}")
        sys.exit(1)

    # 量化到Q4_K_M
    print(f"Quantizing to Q4_K_M...")
    # 使用llama-quantize
    quantize_bin = None
    for p in ["/usr/local/bin/llama-quantize", os.path.join(LLAMA_CPP_DIR, "build/bin/llama-quantize")]:
        if os.path.exists(p):
            quantize_bin = p
            break

    if quantize_bin:
        cmd = [quantize_bin, fp16_output, OUTPUT_GGUF, "Q4_K_M"]
        print(f"Running: {' '.join(cmd)}")
        ret = subprocess.run(cmd)
        if ret.returncode == 0:
            print(f"Q4_K_M saved: {OUTPUT_GGUF}")
            os.unlink(fp16_output)  # 清理fp16
        else:
            print(f"ERROR: quantize failed")
            sys.exit(1)
    else:
        print("llama-quantize not found, keeping fp16")
        print(f"fp16 GGUF: {fp16_output}")
else:
    print("ERROR: No convert script found")
    print("Searching for alternatives...")
    import glob
    for pattern in ["**/convert*hf*", "**/convert*gguf*"]:
        for base in ["/home/ai/.local", "/home/ai/lingminopt/.venv-v8eval"]:
            results = glob.glob(os.path.join(base, pattern), recursive=True)
            for r in results[:3]:
                print(f"  {r}")
    sys.exit(1)

print("=== Done ===")
