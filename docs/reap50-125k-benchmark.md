# Trimmed REAP50 Bolt at 125K

User-authorized reload and matched benchmark. Target: Nemotron-3.5-Bolt-74B-A9B-16GB-REAP50-IQ2_XXS.gguf (248 routed experts), not official unpruned target. Requested context 125000; resolved value is recorded in each run props. Runtime and GPU attention/KV/CUDA graphs preserved.

Two matched cases: no expert cache and adaptive 512 MiB cache, with original 108K prompt, three warm full-prefill repeats, three prefix-reuse repeats, code/tool smoke and held-out Python/debug/navigation/tool probes. Same batch128/microbatch64, q8_0 K/V and deterministic benchmark parameters as official comparison. Official LiLiCorr draft cases excluded because its companion target is unpruned. No new model downloads. No source changes to inference backend or Lichen.

Local matrix service: language-matrix-reap50-125k-matrix; held-out service waits for matrix completion and service exit. They retain memory limits and refuse competing GPU compute. Runs/results live in /home/topher/Language-matrix-coder/reap50-125k-setup. Read-only terminal shows input/output metrics. The historical 24-hour coding queue stays paused; no P04 assignment is resumed.

After successful held-out tests, reload interactive REAP50 through language-matrix-bolt-final.service, retaining historical interactive 1024 MiB cache and batch256/microbatch128; context alone changes from65536 to125000. This interactive placement is distinct from matched benchmark512MiB. OpenCode saved model limit is updated to125000 with tools/access unchanged; existing session remains paused. No claim that full125K context is stable until measurements finish.

## Explicitly authorized experimental draft pairing

User requested actually testing official LiLiCorr with the trimmed target. Prior exclusion described incompatibility too categorically: checkpoint pairing is unvalidated, not a reproduced load failure. A separate language-matrix-reap50-draft-experiment service waits until both existing services finish and checks that the interactive server is idle before taking ownership. No active tests are reset. If idle cannot be confirmed, it stops without interrupting active requests.

Two experimental cases use CPU draft layers0, six proposed tokens, cache0/512 MiB, context125000, GPU graphs/attention/q8 KV preserved. First run bounded code/tool compatibility probes (300 seconds); load failure or failed assertions skip that case's large benchmark. If probes pass, restart a fresh model process before identical large-prompt/warm/prefix tests, preserving the original first-prefill definition. Correctness and speedup remain unverified until actual evidence. Restore trimmed interactive server afterward without dispatching coding work. No backend changes, new downloads or production draft adoption.
