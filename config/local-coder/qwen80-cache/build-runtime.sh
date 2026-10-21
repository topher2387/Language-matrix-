#!/bin/bash
set -euo pipefail
runtime=/home/topher/Language-matrix-coder/qwen80-cache-setup/runtime
if [[ ! -d "$runtime/.git" ]]; then
 git clone https://github.com/ggml-org/llama.cpp.git "$runtime"
fi
if [[ -n "$(git -C "$runtime" status --porcelain --untracked-files=no)" ]]; then
 echo 'Runtime contains tracked changes; refusing to replace them.' >&2
 exit 1
fi
git -C "$runtime" checkout --detach 4a45de4f2c68f3d144f6c2431ad7c1da7e53c99e
cmake -S "$runtime" -B "$runtime/build" -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=ON -DLLAMA_CURL=OFF
cmake --build "$runtime/build" --target llama-server -j 6
