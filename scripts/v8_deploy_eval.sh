#!/bin/bash
# V8 Deploy + Eval Pipeline
# 1. Kill old 7B base server
# 2. Start V8 server on :8101
# 3. Update proxy alias
# 4. Run evaluation

set -e

MODEL_PATH="/home/ai/models/lingai-8b-q4_k_m.gguf"
PORT=8101

echo "=== 1. 停止旧7B服务 ==="
pkill -f "llama_cpp.server.*8101" 2>/dev/null || true
sleep 3

echo "=== 2. 启动V8服务 ==="
nohup python3 -m llama_cpp.server \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 --port $PORT \
    --n_ctx 4096 --n_gpu_layers 20 \
    --n_threads 4 --chat_format chatml \
    --model_alias lingai-7b-base-4bit \
    > /tmp/llama_v8.log 2>&1 &
echo "V8 server PID: $!"

echo "=== 3. 等待服务就绪 ==="
for i in $(seq 1 30); do
    if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$PORT/v1/models', timeout=5)" 2>/dev/null; then
        echo "V8 server ready!"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 5
done

echo "=== 4. 快速验证 ==="
python3 -c "
import urllib.request, json
req = urllib.request.Request('http://127.0.0.1:$PORT/v1/chat/completions',
    data=json.dumps({'model':'lingai-7b-base-4bit','messages':[{'role':'user','content':'1+1='}],'max_tokens':5,'temperature':0}).encode(),
    headers={'Content-Type':'application/json'})
r = urllib.request.urlopen(req, timeout=60)
d = json.loads(r.read())
print(f'V8 inference OK: {d[\"choices\"][0][\"message\"][\"content\"]}')
"

echo "=== 5. 运行评估 ==="
cd /home/ai/lingminopt
python3 tests/eval_7b.py --model lingai-7b-base-4bit --output data/v8_eval_results.json 2>&1 | tee /tmp/v8_eval.log

echo "=== 完成 ==="
