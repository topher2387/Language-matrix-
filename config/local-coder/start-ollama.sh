#!/bin/bash
set -euo pipefail
export OLLAMA_MODELS=/home/topher/Language-matrix-coder/models
export OLLAMA_HOST=127.0.0.1:11434
export OLLAMA_NO_CLOUD=1
export OLLAMA_CONTEXT_LENGTH=32768
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
export LLAMA_ARG_CPU_MOE=1
exec /usr/local/bin/ollama serve
