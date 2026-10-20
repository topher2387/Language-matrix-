# Local GLM-4.7-Flash benchmark

Model: zai-org/GLM-4.7-Flash, Unsloth Q4_K_M GGUF, revision
`0d32489ecb9db6d2a4fc93bd27ef01519f95474d`. File size 18,312,339,808 bytes;
SHA256 `29837ed2c0fc5f51981adf8ac8083fcf80743c598381f13e9f06cbad0498b174`.
Download checksum verified before loading. North weights were deleted at the user's request;
its logs and session remain preserved. Qwen and Korean tutor weights are retained.

Runtime: llama.cpp b10075 / 76f46ad29. RTX 3060 Ti 8 GB; i7-10700F;
approximately 48 GB system RAM. Local API binds only 127.0.0.1:11436.

Configuration: 65,536 context, one slot, 40 first-layer MoE expert groups on CPU,
remaining expert groups and attention on CUDA, q8_0 GPU cache, flash attention,
CUDA graphs enabled, 8 CPU threads, batch 256 / microbatch 128, direct RAM loading
(`--no-mmap`). Preserved reasoning enabled and template support verified through
`/props`. OpenCode output allowance is 16,384 tokens; tools and existing GitHub
credentials remain enabled. Existing supervisors and human approval gates remain.
No repository packet is assigned by this configuration.

The [official model card](https://huggingface.co/zai-org/GLM-4.7-Flash)
recommends preserved reasoning for multi-turn agentic use and temperature 0.7,
top-p 1.0, output 16,384 for coding evaluations. Deterministic smoke comparisons
use temperature 0 and seed 42; these are smoke tests, not published SWE-bench scores.
The GGUF native context metadata is 202,752; this setup does not claim 250K support.

Commands (run from a directory containing `results/`):

```bash
python3 benchmark.py cpu40-64k
python3 benchmark.py cpu40-64k-no-mmap
python3 long-context.py
```

Initial comparisons: both returned correct interval-merging code under independent
assertions and completed a structured add(17,25) call plus tool-result response.
Mapped baseline: 22.32 generation tokens/s on 2,276 generated tokens; coding wall
103.269 s; tool roundtrip 8.218 s. Direct RAM loading: 22.03 generation tokens/s,
104.417 s coding wall; tool roundtrip 6.947 s. One comparison per setting, so no
statistical speedup claim. Short-prompt total VRAM about 6.5 GiB with 1.3 GiB free.
Long-context and actual OpenCode edit/test evidence is recorded separately.

All benchmark model calls are local, zero-cost. No Lichen modifications, merges,
deployments, quota resets or paid fallbacks are authorized by this setup.
