#!/bin/bash
set -euo pipefail
export HF_HUB_OFFLINE=1
exec /home/topher/llama.cpp/build/bin/llama-server \
 --model /home/topher/Language-matrix-coder/north-mini-setup/North-Mini-Code-1.0-UD-Q4_K_M.gguf \
 --alias north-mini-code-supervised:250k --host 127.0.0.1 --port 11435 \
 --ctx-size 250000 --parallel 1 --n-gpu-layers 99 --n-cpu-moe 43 \
 --flash-attn on --cache-type-k q4_0 --cache-type-v q4_0 \
 --batch-size 128 --ubatch-size 128 --threads 8 --threads-batch 8 \
 --jinja --temp 1.0 --top-p 0.95 --no-webui --api-key local-only
