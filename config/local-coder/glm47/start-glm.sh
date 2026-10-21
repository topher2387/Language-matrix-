#!/bin/bash
set -euo pipefail
unset GGML_CUDA_DISABLE_GRAPHS
export HF_HUB_OFFLINE=1
exec /home/topher/llama.cpp/build/bin/llama-server --model /home/topher/Language-matrix-coder/glm47-setup/GLM-4.7-Flash-Q4_K_M.gguf --alias glm-4.7-flash-local --host 127.0.0.1 --port 11436 --ctx-size 65536 --parallel 1 --n-gpu-layers 99 --n-cpu-moe "${GLM_CPU_MOE:-42}" --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 --batch-size 256 --ubatch-size 128 --threads 8 --threads-batch 8 --no-mmap --jinja --reasoning-preserve --temp 0.7 --top-p 1.0 --no-webui --api-key local-only
