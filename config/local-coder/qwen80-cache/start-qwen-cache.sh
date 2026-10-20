#!/bin/bash
set -euo pipefail
unset GGML_CUDA_DISABLE_GRAPHS LLAMA_ARG_N_CPU_MOE LLAMA_ARG_CPU_MOE
export HF_HUB_OFFLINE=1
exec /home/topher/Language-matrix-coder/qwen80-cache-setup/runtime/build/bin/llama-server \
 --model /home/topher/Language-matrix-coder/models/blobs/sha256-1e641b93edc1222c5637c745c70525181cfcee65be3aa69fe2d5df31c63f0457 \
 --alias qwen3-coder-next-cache:64k --host 127.0.0.1 --port 11437 \
 --ctx-size 65536 --parallel 1 --n-gpu-layers all --cpu-moe --moe-cache-mib "${QWEN_EXPERT_CACHE_MIB:-2048}" \
 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0 \
 --batch-size 256 --ubatch-size 128 --threads 8 --threads-batch 8 \
 --load-mode none --log-verbosity 4 --jinja --temp 0.2 --no-webui --api-key local-only
