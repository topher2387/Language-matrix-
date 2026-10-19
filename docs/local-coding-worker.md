# Supervised local coding worker

The local coding role is Qwen3-Coder; Kanana is retained exclusively for Korean teaching and advice. Setup initially admitted no development packet. The user subsequently explicitly authorized one fixture-validation CLI job; no other packet is authorized. A successful readiness probe is not evidence of autonomous coding reliability.

## Exact identities and scope

- Download: `qwen3-coder:30b-a3b-q4_K_M`, verified in the [official Ollama tag catalogue](https://ollama.com/library/qwen3-coder/tags).
- Runtime alias: `qwen3-coder-supervised:32k`, created from that download using `config/local-coder/Modelfile`. The alias changes runtime parameters, not weights.
- OpenCode: `ollama-local/qwen3-coder-supervised:32k`, using the OpenAI-compatible endpoint at `http://127.0.0.1:11434/v1`.
- Preserved tutor: `language-matrix/kanana-2-30b-a3b`, existing GGUF and chat history under the user's home. Its prompt and launchers now prohibit coding assignments.

These are workstation settings for `/home/topher`. Weights, credentials, generated logs and OpenCode databases are not committed. The dummy `local-only` API key is not a credential.

## Hardware and launch

Observed host: RTX 3060 Ti 8 GB, 46 GiB usable RAM. Start conservatively with 32768 context tokens, all attention layers and KV cache on GPU, CPU RAM for MoE expert weights, batch 128, eight CPU threads, quantized KV cache, one parallel request and one loaded Ollama model. The dedicated Ollama service exports `LLAMA_ARG_CPU_MOE=1` and the model alias sets `num_gpu 99` (all layers eligible; expert tensors remain CPU). The unrelated existing RWKV server is preserved. Kanana's server was unloaded to free memory; its weights and restart script remain intact. Avoid loading both large models concurrently on this GPU.

Installed workstation copies live under `/home/topher/Language-matrix-coder`:

1. `./start-ollama.sh` starts loopback-only Ollama with cloud features disabled. Do not run a duplicate server if port 11434 is already served by this configured process.
2. `ollama pull qwen3-coder:30b-a3b-q4_K_M` downloads the verified tag.
3. `ollama create qwen3-coder-supervised:32k -f Modelfile` creates the runtime alias.
4. `./start-opencode.sh` starts the single loopback OpenCode server on port 4097; `./open-coder.sh --session SESSION_ID` attaches the interactive terminal to that same live server. It supplies no development prompt and does not resume old sessions by default. The first fixture CLI assignment was subsequently launched by explicit user authorization.

OpenCode uses isolated XDG configuration/data/state, only the local provider, no plugins/MCP, and all built-in tools and existing GitHub CLI access enabled, as explicitly requested. No tool deny entries are added. The existing supervisor's independent review, tests and publication checks still apply. User approval is required before assigning any additional outstanding packet.

To return to Korean tutoring, first unload Qwen with `ollama stop qwen3-coder-supervised:32k`, restart `/home/topher/Language-matrix-chat/start-model.sh`, then run `/home/topher/Language-matrix-chat/open-chat.sh`. Its default prompt is now tutor-only. Do not reuse old coding prompts.

## Forge inspection and remaining integration boundary

The actual Language Matrix Forge configuration is `.dev-harness/dispatch-config.json`: coding was `opencode/deepseek-v4.1-flash-free`, reviewer `opencode/big-pickle`. Kanana was a separately launched local OpenCode worker, never a configured Forge catalogue entry. The Lichen user service points at a completed-issue verification configuration with those same hosted identities; it is not an authorization to run Language Matrix packets.

Both Forge configurations, their quotas, databases, worker routing, independent reviewer and Lichen source checkouts are unchanged. The local coding slot is replaced through the separate OpenCode profile and role manifest in `config/local-coder/worker-routing.json`.

Native Forge generates a fresh provider configuration and a fresh isolated model catalogue. It does not import this custom local provider. Merely changing its model ID would fail its zero-cost admission checks. Automated Qwen admission therefore remains blocked pending a separately reviewed local-provider integration. No host-execution fallback, catalogue fabrication, safety-check removal, quota reset or hidden paid fallback is used.

## Evidence standard

`config/local-coder/smoke.py` reads Ollama metadata and requires Q4_K_M and tool capability, asks for a synthetic function call, checks its parsed name/arguments, sends its result back, and records real timing/placement. It executes no model-selected code. A separate bounded OpenCode read probe checks the actual application's tool path. Result evidence belongs in `docs/evidence/local-coder-readiness.json` after observed results are available.

For real assignments the supervisor must independently inspect file diffs, run meaningful tests, and verify commit SHA and GitHub PR head. Model prose and successful branch creation are insufficient. The earlier Kanana runs produced no accepted coding implementation; no existing worker PR is attributed to Kanana.

Observed readiness: verified Q4_K_M metadata and base digest `06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca`; parsed synthetic tool call and explicit final acknowledgement passed. Warm short-probe generation measured about 16–21 tokens/second, not a coding throughput benchmark. GPU allocation was about 4.83 GB with 12/49 layers offloaded in the initial 8K probe. First cold load took about 73 seconds and the initial 301-token prompt took about 25 seconds; larger OpenCode prompts will take longer.

## Context and session correction

The original 8K coding run saturated its window: a recorded step had 8191 input tokens and only one output token, finishing for length. It produced no implementation. The job and terminal had also been separate embedded OpenCode processes sharing only the database, rather than one live server. That made the visible session state unreliable. The corrected profile uses a 32768-token model context and matching OpenCode limit, with 4096 output tokens and ten GPU layers for additional KV-cache headroom. Both the job client and visible terminal now attach to the same loopback server on port 4097. All tools and existing GitHub access remain enabled. The initial 8K smoke evidence is historical; it is not evidence that the 32K coding assignment completed.

## Server lifetime recovery

The local connection failure was reproduced: neither Ollama (11434) nor OpenCode (4097) had a running listener; only the terminal client survived. Kernel logs contained no OOM/crash record in the inspected interval, and the original tool process handles were gone. The exact exit cause is unknown. Their launch lifetime was coupled to interactive tool execution rather than a service manager.

Installed dedicated user units `language-matrix-ollama.service` and `language-matrix-opencode.service` from this directory. They are started manually, not enabled at login/boot, and restart on failure with a bounded start-rate limit. They modify no existing Forge or Lichen service. Service logs are available with `journalctl --user -u language-matrix-opencode -u language-matrix-ollama`. The OpenCode unit requires the Ollama unit. `open-coder.sh` now starts the dedicated services and checks health before attaching, preventing silent attachment to a missing server. Do not also launch standalone serve scripts while these units are active.

Observed recovery: both services active with zero restarts, OpenCode health healthy, abort accepted in 0.86 seconds and session idle, then a new prompt returned `RECOVERY_OK` in about 61 seconds including prompt processing. The terminal was reopened on the original assignment session. The unfinished coding job is paused; its generated CLI and full session history were preserved. No test/commit/PR claim is made for that partial implementation. `check-recovery.py` reproduces the no-code-change prompt/abort/response check in a separate test session. Tools and GitHub permissions remain enabled.

## Long-context performance correction

Whole-layer offload left most attention and KV cache on CPU. An actual coding turn at 16119 total context tokens evaluated 2725 new prompt tokens at 80.41 tokens/sec and generated 63 tokens at 1.17 tokens/sec. The model process had no swapped memory.

The installed Ollama 0.30.7 backend documents `LLAMA_ARG_CPU_MOE` and inherits the parent environment ([upstream runner source](https://github.com/ollama/ollama/blob/v0.30.7/llm/llama_server.go)). The dedicated service now exports this flag; `num_gpu 99` puts all 49 layers eligible on GPU while expert FFN weights are overridden to CPU. Logs verify 784 MiB GPU model buffers, 1632 MiB GPU KV cache and CPU expert tensors. Context remains 32768 and all tools remain enabled. Ollama model size/processor percentages do not describe CPU expert placement accurately with tensor overrides; use actual backend buffer logs.

Observed after-change probe: 16035 prompt tokens processed in 81.77 seconds (about 196 tokens/sec), followed by 96 generated tokens at 14.16 tokens/sec; short generation 16.40 tokens/sec. The earlier coding turn and synthetic probe use different text, so this is comparable-context operational evidence, not a controlled identical-prompt speedup. A large uncached prompt still delays first output; prefix cache reuse helps subsequent turns. No model weight, quantization, tutor, existing RWKV service, quota or Lichen file changed.
