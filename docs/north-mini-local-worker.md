# Local North Mini Code setup

Model: CohereLabs North-Mini-Code-1.0, Unsloth UD-Q4_K_M GGUF. Quant repository revision e306bb4bf0df610f5471d97a01de2b6e0b24d356; file SHA256 d59f4cb3abec1bd3e5e185b99cdd811e3be3402cbc2bab8223081a460d5724bf;19203186784bytes. Checksum verified locally before load.

Runtime: existing CUDA llama.cpp build10075, commit76f46ad29 with cohere2moe support. Dedicated loopback11435; Qwen Ollama service and weights retained but unloaded. No runtime/source changes to Lichen.

Requested context250000; runtime pads slot to250112. Flash Attention enabled; K/V caches q4_0 on GPU. First43expert layers in RAM; remaining expert layers on GPU; shared attention remains on GPU. Single sequence, batch128, eight CPU threads. OpenCode advertises250000context and4096output, north-coder agent24steps. Tools and GitHub access retain existing permissions. Temperature1.0/top_p0.95 defaults follow model-card guidance; deterministic smoke tests use temperature0.

The model card documents up to256K context. Configuring/loading capacity and passing short smoke tests do not demonstrate reliable250K retrieval or performance. Full-window quality benchmarking remains to be performed. Initial128-token smoke budget cut off reasoning/tool arguments; corrected to1024. That truncation was a test configuration issue, not a model coding failure.

Start with config/local-coder/north/start-north.sh. The local OpenCode profile selects north-local/north-mini-code-supervised:250k. config/local-coder/north/open-north.sh attaches the prepared, empty supervised session. Existing Qwen sessions and tutor configuration are preserved. No development packet, merge or deployment starts automatically.
