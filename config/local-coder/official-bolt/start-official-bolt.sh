#!/bin/bash
set -euo pipefail
mode=${1:-baseline-cache}
case "$mode" in
 baseline|baseline-cache) draft=off; cache=on ;;
 baseline-no-cache) draft=off; cache=off ;;
 speculative|speculative-cache) draft=on; cache=on ;;
 speculative-no-cache) draft=on; cache=off ;;
 *) echo 'Use baseline-no-cache, baseline-cache, speculative-no-cache, or speculative-cache' >&2; exit 2 ;;
esac
cache_mib=0
if [[ "$cache" == on ]]; then
 cache_mib=${BOLT_EXPERT_CACHE_MIB:-512}
 [[ "$cache_mib" =~ ^[1-9][0-9]*$ ]] || { echo 'Cache enabled requires a positive integer MiB budget' >&2; exit 2; }
fi
setup=/home/topher/Language-matrix-coder/official-bolt-setup
unset GGML_CUDA_DISABLE_GRAPHS
args=(--model '/media/topher/New Volume/models/local_models/official-bolt/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf'
 --alias official-bolt-local --host 127.0.0.1 --port 11439
 --ctx-size 125000 --parallel 1 --n-gpu-layers all --cpu-moe --moe-cache-mib "$cache_mib"
 --flash-attn on --cache-type-k q8_0 --cache-type-v q8_0
 --batch-size 128 --ubatch-size 64 --threads 8 --threads-batch 8
 --load-mode none --log-verbosity 4 --jinja --reasoning off --reasoning-format deepseek --temp 0 --no-ui --api-key local-only)
if [[ "$draft" == on ]]; then
 args+=(--spec-type draft-dflash --spec-draft-model '/media/topher/New Volume/models/local_models/official-bolt/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-LiLiCorr.gguf'
 --spec-draft-n-max "${BOLT_DRAFT_TOKENS:-6}" --spec-draft-ngl "${BOLT_DRAFT_GPU_LAYERS:-0}")
fi
if [[ "${2:-}" == --print-args ]]; then
 printf '%s\n' "${args[@]}"
 exit 0
fi
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
exec /home/topher/Language-matrix-coder/qwen80-cache-setup/runtime/build/bin/llama-server "${args[@]}"
