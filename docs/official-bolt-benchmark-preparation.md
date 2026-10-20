# Official NVIDIA Bolt + LiLiCorr preparation

User authorized download and preparation, without interrupting the active REAP50
Bolt P04 worker. These files are official NVIDIA releases, not the community
expert-pruned REAP50 model currently running.

- Target: nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-GGUF,
  revision e0fecb69cb3e5e4c5e8a056fa2aec98c78e91246,
  NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf,22,018,326,528bytes,
  SHA25691d63363e782c8a3d5f4be42816eba8e0d42dd2530bd07a7d0d2dc440599af75.
- Companion: nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-LiLiCorr-GGUF,
  revision182d2987939e12f458298b5d5f6ef98912f4ad6c,
  NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-LiLiCorr.gguf,998,242,560bytes,
  SHA256080e1ea41c9562a7804dbf30c6fbd4d17e216c6b8ff666f88e6edb1816010194.

[Official target instructions](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-GGUF)
and [official companion](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB-LiLiCorr-GGUF)
specify DFlash/LiLiCorr. The companion is not a standalone chat model and is paired
with the unpruned official target, not the active REAP50 variant. Model license
listed by NVIDIA is OpenMDW1.1. Vision projector omitted for this text/tool benchmark.

Downloads run under language-matrix-official-bolt-download.service, local-only
script at /home/topher/Language-matrix-coder/official-bolt-setup/download.py.
Pinned URLs, resumable .part files, exact size and SHA256 verification, atomic
rename after verification. Download-status.json and download-completed.txt record
actual completion; committed preparation does not mean weights are downloaded.
No model files are committed to GitHub. No new model has been loaded by this prep.

Storage: after the user freed space, both files are placed in
/media/topher/New Volume/models/local_models/official-bolt. Existing partial
target bytes were moved and resumed; verified drafter was moved on the same
filesystem. Root-drive copy removed only after successful move. Download service
is now language-matrix-official-bolt-download-resume.service. The preflight still
reserves at least4GiBfree. No existing model weights deleted.

Runtime4a45de4f2c68f3d144f6c2431ad7c1da7e53c99e supports draft-dflash,
LiLiCorr metadata, --spec-draft-model, --spec-draft-n-max and --spec-draft-ngl.
Actual inference compatibility and GPU/RAM fit remain unverified until loading.

Prepared launch script: config/local-coder/official-bolt/start-official-bolt.sh.
Four modes: baseline-no-cache, baseline-cache, speculative-no-cache, speculative-cache. Legacy baseline/speculative aliases retain cache enabled. Both refuse to start with any active GPU compute
process and require both downloads verified. Defaults:125,000-token context,one slot,
GPU attention/q8_0cache/Flash Attention/CUDA graphs,CPU expert weights,512MiBGPU
expert cache,8CPUthreads,batch128/microbatch64. Draft initially on CPU for8GBVRAM
headroom,6draft tokens. Placement/cache/draft length can be tuned after measuring.
These are cautious proposed settings, not a demonstrated optimal configuration.
No paid API, provider fallback, Lichen changes or approval-gate change.

Once the current assignment is safely saved and paused and compute VRAM cleared:

1. Run baseline launcher, then `python3 benchmark.py official-baseline`.
2. Save server logs/resource measurements and stop baseline server cleanly.
3. Run speculative launcher, then `python3 benchmark.py official-speculative`.
4. Compare identical prompts/seed/temperature/context/output budget/target placement,
   correctness, full tool roundtrip, cold/warm prefill, generation and end-to-end
   wall time, draft proposals/acceptance, GPU peak, RAM and swap. Repeat bounded
   runs before claiming a speedup. Draft overhead may outweigh benefit on this GPU.
5. Run an isolated OpenCode edit/test task plus independent assertions before
   assigning repository coding. No automatic P04/P05 dispatch.

Validation performed now: shell syntax, Python syntax, runtime flag/source support,
and busy-GPU launch guard (expected refusal). Benchmark inference not started.

User-expanded comparison:125,000tokens, all four combinations:

| Mode | LiLiCorr | Selective GPU expert cache |
| --- | --- | --- |
| baseline-no-cache | Off | Off(0MiB) |
| baseline-cache | Off | On(512MiB) |
| speculative-no-cache | On | Off(0MiB) |
| speculative-cache | On | On(512MiB) |

GPU attention,q8_0KV,Flash Attention and CUDA graphs remain enabled for all four.
All routed expert source weights remain in CPU RAM. Cache-off does not move
attention to CPU or disable KV caching. Draft initially CPU-only in both draft
cases; target placement, prompts,seed and output budget remain matched. Main
runtime may pad125,000internally; record resolved context from /props/logs.

Test both short and near-full-context workloads: target approximately108,000input
tokens with16,384output headroom under125,000configured total. Loading with a
large allocation alone is not proof of long-context recall or performance. Record
OOM/fit failure truthfully, keep context/graphs fixed for comparison, and label any
later fallback as a separate configuration. No125Kfit/speed result exists yet.

Configuration verification: shell syntax PASS; all four --print-args cases assert
125000context,expected cache0/512,and draft absent/present. No model launched.
Matrix and metrics are saved in config/local-coder/official-bolt/benchmark-matrix.json.
