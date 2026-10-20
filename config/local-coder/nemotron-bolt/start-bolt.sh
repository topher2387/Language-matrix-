#!/bin/bash
set -euo pipefail
unset GGML_CUDA_DISABLE_GRAPHS
exec /home/topher/Language-matrix-coder/qwen80-cache-setup/runtime/build/bin/llama-server \
 --model '/media/topher/New Volume/models/local_models/Nemotron-3.5-Bolt-74B-A9B-16GB-REAP50-IQ2_XXS.gguf' \
 --alias nemotron-bolt-reap50-local --host 127.0.0.1 --port 11438 \
 --ctx-size 65536 --parallel 1 --n-gpu-layers all --cpu-moe --moe-cache-mib 1024 \
 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 --batch-size 256 --ubatch-size 128 \
 --threads 8 --threads-batch 8 --load-mode none --log-verbosity 4 \
 --jinja --reasoning off --reasoning-format deepseek --temp 1 --top-p 0.95 --no-ui --api-key local-only
