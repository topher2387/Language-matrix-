# Qwen80 selective expert cache

User requested returning to Qwen80 with selective expert caching. GLM is unloaded;
its weights and benchmark evidence are retained. No development packets resume.

Model: existing Unsloth Qwen3-Coder-Next 80B-A3B UD-Q3_K_S GGUF, 33,320,267,776 bytes,
blob SHA256 1e641b93edc1222c5637c745c70525181cfcee65be3aa69fe2d5df31c63f0457.
Local API alias: `qwen3-coder-next-cache:64k`, provider `qwen-cache-local`.

The earlier installed llama.cpp b10075 lacked a selective expert cache. An isolated
upstream build at `4a45de4f2c68f3d144f6c2431ad7c1da7e53c99e` supplies
`--cpu-moe --moe-cache-mib 2048`. This is a bounded GPU cache of host-resident
expert tensors, with demand copies and reuse. It does not pin five entire expert
layers as the previous Qwen Ollama setup did. All routed expert weights remain
available; this does not prune experts or change the model.

Source: https://github.com/ggml-org/llama.cpp/blob/4a45de4f2c68f3d144f6c2431ad7c1da7e53c99e/src/llama-moe-cache.cpp

The build is local, CUDA architecture86, Release, CUDA graphs enabled. Existing
Ollama and `/home/topher/llama.cpp` installations are unmodified. Build instructions
are in `config/local-coder/qwen80-cache/build-runtime.sh`. The new upstream loader
uses `--load-mode none` instead of removed `--no-mmap`; correcting this launcher
option and an early readiness timeout were setup events, not model errors.

Settings: 65,536 context, q8_0 GPU KV cache, flash attention, 8 CPU threads,
batch256 / microbatch128, one slot, local127.0.0.1:11437. CUDA graphs enabled.
OpenCode retains tools, existing GitHub authentication and 24-step agent cap;
output allowance is16,384. No paid provider/fallback or quota change. Native
llama-server built-in tools are unnecessary: OpenCode supplies the agent tools.

Initial tests (`python3 benchmark.py cache2048`):

- Generated interval-merging code passed independent deterministic assertions.
- Structured add(17,25) call plus tool result handling passed.
- Code response184generated tokens:25.845 tokens/sec,8.238seconds wall.
- Tool call31tokens:26.578 tokens/sec; result17tokens:23.125 tokens/sec.
- Total GPU use6,255MiB, free1,577MiB after the tests.
- No model correction or tool error occurred in this bounded test.

These short-prompt timings do not establish long-context speed or sustained
coding reliability. The prior17.46tokens/sec result was on a52.8K context with
another runtime/placement; no controlled speedup percentage is claimed.
The64K setting is retained, but the new cache/runtime has not yet been validated
at full64K occupancy. No P04/P05, merge, deployment or Lichen change occurred.

Detailed runtime check confirms CUDA0 MoE cache2,047.57MiB for29,376MiB host
experts,48layers,1,712iq3_s slots (7.0% of total slots, not a hit-rate claim).
A repeated smoke measured25.792tokens/s for the same184-token code response,
with code assertions and complete tool roundtrip passing again. Post-test VRAM
6,259MiB used /1,574MiB free. CUDA graph reuse appears in captured logs. Cache
hit-rate counters are emitted on model destruction; they were not sampled live.

OpenCode has a new blank interactive session for the cache-backed model,
with no repository job dispatched. Launch using the local
`qwen80-cache-setup/open-qwen-cache.sh` script.

## User-requested 125K context update (2026-10-21)

Context raised from65536 to125000 to postpone compaction. The same Qwen3-Coder-Next80B-A3B UD-Q3_K_S weights, runtime,2GiB expert cache, GPU attention, q8_0 KV cache, CUDA graphs,8threads, batch256/micro128 and tools/GitHub access are retained. Runtime alias is now `qwen3-coder-next-cache:125k`; OpenCode default and qwen-cache-coder agent use that alias with context125000 and output allowance16384. Legacy64K entry remains for saved history; it is not the current default.

Idle chat/config were backed up before reload. Server `/slots` resolves context125184 (runtime alignment); OpenCode resolves125000. Health is OK and a bounded short inference returned READY. GPU use after that inference:7191MiB, free641MiB. Its two-token decode timing was19.62tokens/sec; this tiny readiness check is not a performance comparison. Full125K prompt occupancy, long-run speed and coding reliability have not been tested here. Earlier64K benchmark results above remain historical evidence and do not establish125K performance.

The existing direct-chat session is preserved. No development job was resumed and no Lichen configuration changed.
