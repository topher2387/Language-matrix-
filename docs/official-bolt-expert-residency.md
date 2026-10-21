# Workload-guided expert residency: initial feasibility and bounded follow-up

This exploratory study preserves the original four-case benchmark, routing, weights, context, CUDA graphs and approval gates. No Lichen changes, backend rewrite, new downloads, production changes or main-branch changes. The follow-up waits for both the original matrix's terminal status and its service to finish before loading anything. Its launcher refuses other active GPU compute.

## Identity and implementation evidence

Target: NVIDIA-Nemotron-3.5-Bolt-74B-A9B-24GB.gguf, official checkpoint e0fecb69cb3e5e4c5e8a056fa2aec98c78e91246; SHA256 91d63363e782c8a3d5f4be42816eba8e0d42dd2530bd07a7d0d2dc440599af75. Backend llama.cpp 4a45de4f2c68f3d144f6c2431ad7c1da7e53c99e, CUDA/graphs enabled. This is sparse nemotron_h_moe, 88 hybrid blocks, 496 routed expert IDs per applicable layer; metadata lists nine selected experts in applicable layers and one shared expert. Mixed tensor types: 489 F32, 114 Q8_0, 160 IQ2_XXS, 80 NVFP4. The loader's overall IQ2_XXS label is not a uniform quantization description.

Source evidence: src/llama-moe-cache.cpp implements segmented LRU, probation/protected queues, adaptive fills and grouped expert banks. Routed IDs are read internally in copy(). log_stats() exports only aggregate hit/miss/upload counters at destruction. get_slot_map() bypasses cache updates for large batches; large-batch copy_experts() can read resident entries. Therefore cache utility differs between prefill and decode.

No CLI for arbitrary static expert-ID placement, frequency-ranked preload, or latency-per-byte residency was found. Whole-tensor placement is not individual expert placement. The existing eval-callback diagnostic is not built, evaluates a single prompt rather than a coding session, and its common debug printer truncates dimensions to first/last three elements. The model selects nine experts: truncated diagnostics cannot supply complete routing traces. Enabling that callback also synchronizes tensor reads, contaminating performance measurements. We have not modified or built a custom collector. Aggregate counters cannot reconstruct activation frequencies, co-occurrence, reuse distance or a defensible static ranking.

## Existing measured baseline (not held-out coding-session acceptance)

Run 20261020T200010Z; resolved context 125184, actual large prompt 108006 tokens, identical original protocol. Loading includes normal runtime warmup and benefits from available OS file cache; it is a fresh-process load, not a proven cold-disk load.

| Configuration | Load seconds | First full prompt seconds | Warm full median seconds | Prefix-reuse median seconds | Peak GPU MiB |
|---|---:|---:|---:|---:|---:|
| A: no draft, no cache | 52.886 | 963.165 | 965.363 | 1.033 | 6206 |
| D: no draft, adaptive 512 MiB | 60.885 | 961.178 | 957.444 | 1.157 | 6530 |
| Draft, no cache | 58.690 | 986.707 | 987.274 | 1.133 | 7095 |

All three completed cases passed seven boundary-marker recalls and independent small coding/tool smoke assertions. Full-prefill cache_n was zero; prefix reuse was separately confirmed. A decoded approximately 19–19.5 tokens/s on short large-context replies and 24.82 tokens/s on its small coding response. These are different workloads. A first-content TTFT was 962.382 seconds. The final draft/cache case is still underway at this checkpoint and is not altered.

D's shutdown cache counters: 15897 hits, 107700 misses, 12.86% hit rate, 124905 MiB uploaded across the entire run. These are cache-policy counters, not per-token activation probabilities; unique-fill miss semantics must not be treated as identical to individual selection counts. The 512 MiB request resolved to 487.78 MiB of expert-bank allocation for 16262.81 MiB of host experts. Groups differ in expert byte size, and some groups have zero slots. Exact per-expert sizes/rankings are not yet extracted. Upload volume is measured by runtime counters; transfer time and causal latency savings are unmeasured.

The observed warm-full median difference is 7.918 seconds (0.82%) in D's favor, without randomized/interleaved replication. It is not evidence of a significant or causal speedup. Prefix reuse was slightly slower with D in these samples. Baseline samples recorded available system RAM, not process RSS or CPU utilization; do not invent those missing metrics.

## Budget

At the current 125K context and graphs, 512 MiB requested is the only tested adaptive budget. Without the draft model the measured GPU peak leaves 1302 MiB; keeping a provisional 1024 MiB display/transient reserve leaves only 278 MiB for a possible additional cache allocation. This suggests roughly 768 MiB requested as a conservative next candidate, not a verified maximum. The draft/cache run has reached 7602/7832 MiB: only 230 MiB remains, so expanding that configuration is not justified. Practical maximum remains BLOCKED pending completed peaks and a separate bounded fit test. No live settings were changed.

## Matrix

| Requirement | Status | Evidence/limitation |
|---|---|---|
| Sparse individually routed MoE identity | PASS | Loader metadata and model graph |
| Existing selective adaptive caching | PASS | SLRU implementation and runtime counters |
| Complete routing trace via current server | BLOCKED | No exposed per-ID collector; debug output incomplete |
| Ten-minute representative expert profile | BLOCKED | Cannot produce valid counts without complete traces |
| B static frequency-ranked placement | BLOCKED | No placement interface or complete traces |
| C savings-per-byte placement | BLOCKED | No complete traces or measured per-expert transfer costs |
| Offline B/C placement simulation | BLOCKED | No collected complete traces; no fabricated rankings |
| A/D held-out representative tasks | BLOCKED, queued | Starts only after original owner finishes; bounded separately |
| Coding-quality preservation | PASS for existing smoke only | Not repository acceptance or full workload validation |
| Exact maximum expert budget | BLOCKED | Only one positive budget tested |
| Profiling repays ten-minute cost | BLOCKED | No measured profile-based speedup |

No FAIL is assigned merely for unsupported instrumentation, and NOT APPLICABLE does not apply because the target is MoE.

## Follow-up and amortization

expert-residency/followup.py queues a maximum two-hour passive wait, then A and D on separate held-out Python semantics, debugging, code-navigation and structured tool-call tasks. Each model load is bounded at 240 seconds and each request at 90 seconds. It records raw responses/correctness, model timings, wall time, GPU utilization/VRAM, process RSS/swap and process CPU ticks. It owns and unloads only its test servers. CPU percent can be derived from tick deltas / clock tick rate / elapsed seconds (one-core basis); do not compare instrumented CPU traces to uninstrumented server timings without qualification. Timing TTFT for this follow-up is unavailable because requests are non-streaming; original streamed TTFT remains the baseline. The follow-up is a feasibility diagnostic, not a substitute for unavailable expert profiling. Full session-time savings and transfer-time attribution remain unmeasured.

For a ten-minute profiling cost, break-even requires saved inference time >600 seconds: 16.67% over one hour of baseline inference, 4.17% over four hours, 2.08% over eight hours. If only fraction f of a wall-clock session is inference, required reduction is 600/(session_seconds*f). Net saving = baseline inference seconds * measured reduction -600. A 0.82% reduction, even if independently confirmed, would take about 20.3 hours of continuous inference to repay profiling; the present comparison is not profile-guided and cannot establish that benefit.

Minimal next experiment: inspect held-out A/D evidence and complete the current matrix. If adaptive caching still fails to yield material gains, stop here. Obtaining a real frequency-ranked B/C comparison requires a separately authorized complete routing-trace collector or an existing compatible runtime feature; rewriting the cache is not justified by current evidence.
