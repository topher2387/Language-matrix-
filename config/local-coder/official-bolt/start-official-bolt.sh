#!/bin/bash
set -euo pipefail
mode=${1:-baseline}
case "$mode" in baseline|speculative) ;; *) echo 'Use baseline or speculative' >&2; exit 2;; esac
setup=/home/topher/Language-matrix-coder/official-bolt-setup
# Preparation only: refuse to interrupt any existing GPU worker.
active=$(nvidia-smi --query-compute-apps=pid --format=csv,noheader)
if [[ -n "$active" ]]; then
 echo 'GPU compute is active. Save/pause that assignment and clear VRAM before benchmarking.' >&2
 exit 1
fi
python3 - "$setup" <<'PY'
import json,pathlib,sys
D=pathlib.Path(sys.argv[1]);manifest=json.loads((D/'manifest.json').read_text());status=json.loads((D/'download-status.json').read_text())
for m in manifest:
 assert status.get(m['filename'],{}).get('status')=='verified','Download not verified: '+m['filename']
 assert status[m['filename']]['sha256']==m['sha256']
 assert pathlib.Path(m['path']).stat().st_size==m['bytes']
PY
unset GGML_CUDA_DISABLE_GRAPHS
args=(--model "$setup/models/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf"
 --alias official-bolt-local --host 127.0.0.1 --port 11439
 --ctx-size 65536 --parallel 1 --n-gpu-layers all --cpu-moe --moe-cache-mib "${BOLT_EXPERT_CACHE_MIB:-512}"
 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0
 --batch-size 128 --ubatch-size 64 --threads 8 --threads-batch 8
 --load-mode none --log-verbosity 4 --jinja --reasoning off --reasoning-format deepseek --temp 0 --no-ui --api-key local-only)
if [[ "$mode" == speculative ]]; then
 args+=(--spec-type draft-dflash --spec-draft-model '/media/topher/New Volume/models/local_models/official-bolt-draft/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-LiLiCorr.gguf'
 --spec-draft-n-max "${BOLT_DRAFT_TOKENS:-6}" --spec-draft-ngl "${BOLT_DRAFT_GPU_LAYERS:-0}")
fi
exec /home/topher/Language-matrix-coder/qwen80-cache-setup/runtime/build/bin/llama-server "${args[@]}"
