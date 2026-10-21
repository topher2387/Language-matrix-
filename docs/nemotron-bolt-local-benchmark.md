# Nemotron Bolt local benchmark

File: Nemotron-3.5-Bolt-74B-A9B-16GB-REAP50-IQ2_XXS.gguf (13,378,655,232 bytes).
Source: [anik-jha model card](https://huggingface.co/anik-jha/Nemotron-3.5-Bolt-74B-A9B-16GB-GGUF),
revision e24fd75e50990f625772f9ab0884dacaefd18d3d.
Local SHA256 matches published LFS hash:
09fec94203ef6e88b20b90bd1eb3a2f183927fb36839d61710c89bfe3abeac7a.

This is the community REAP50 expert-pruned variant, not the unpruned NVIDIA
74B parent. The publisher says REAP50 retains half the routed experts per layer;
74B-A9B names the parent. Local GGUF architecture is nemotron_h_moe,88blocks,
248experts, native context262144. No vision projector was loaded; text/tools only.

Before loading: Qwen/OpenCode were inactive after the reported crash. Their
session record and partial P04 files were preserved. An unrelated RWKV MIRE
embedding process held404MiB despite n-gpu-layers0. At user instruction it was
stopped temporarily, clearing compute workloads; desktop535MiB remained, with
7,297MiBfree. No Lichen change. MIRE brain remains paused while Bolt is loaded.
The Qwen crash cause has not been established; no unsupported attribution made.

Runtime: isolated llama.cpp4a45de4f2c68f3d144f6c2431ad7c1da7e53c99e,
CUDA86,64Kcontext,8threads,one slot,batch256/microbatch128,q8_0KV,
Flash Attention and CUDA graphs enabled. Routed experts in RAM with selective
GPU cache. Local endpoint127.0.0.1:11438. OpenCode benchmark tools enabled,
16Koutput allowance,24step cap; existing coding default preserved. Reasoning
explicitly off, matching this variant publisher's evaluated mode. Deterministic
smokes use temperature0,seed42. No paid inference or outstanding packet dispatch.

## Results

2GiBexpertcache: code assertions and tool roundtrip PASS;31.153generationtokens/s
on139tokens,5.466scoding wall;34-token tool call30.945tokens/s. Only219MiBfree
VRAM after short tests: rejected as the retained placement due to poor headroom.
Cache shutdown telemetry: small-batch hit rate64.89%,large-batch30.72%; specific
to this tiny test, not a general workload estimate.

Final1GiBexpertcache: code assertions and tool roundtrip PASS;25.628tokens/s
on139tokens,6.488scoding wall. Tool call25.452tokens/s and result26.530tokens/s.
After full workflow:6,588MiBtotal GPU usage,1,244MiBfree. Only Bolt held compute
VRAM. Retained64K context has not been validated at full occupancy or long duty.

Actual OpenCode workflow:87.127seconds wall from assignment to final response,
8assistant turns,9tool calls,2edits. First implementation omitted sorting and
failed1of5tests. Model corrected sorting without controller intervention, then
passed all5tests. Controller independently reran5tests and500seeded randomized
union-oracle cases: PASS. One confirmed self-correction,zero repetitive failure
loops,zero controller resumes. Tests were preserved; only ranges.py was edited.
This single small task does not prove P04 competence or general model quality.

GLM's earlier same small workflow took approximately126seconds with no correction;
its reasoning mode, quantization and placement differ. Qwen's code/API smoke
was a different execution path. No controlled overall model ranking is claimed.

Commands:

```bash
python3 benchmark.py bolt-cache2048
python3 benchmark.py bolt-cache1024
python3 -B -m unittest -v  # worker-benchmark directory
python3 verify-worker.py
```

Evidence: docs/evidence/nemotron-bolt-benchmark.json,
nemotron-bolt-worker-summary.json,nemotron-bolt-worker-verification.json,
nemotron-bolt-cache2048.log. Reproducible launcher/test files are in
config/local-coder/nemotron-bolt/. No merges, deployment, quota resets or hosted
calls. Qwen P04 is preserved and not accepted or resumed by this benchmark.
