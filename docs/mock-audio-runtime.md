# Mocked two-voice metadata demonstration

Run `python3 tools/mock_audio_runtime.py` from the repository root, or pass the script's absolute path from another directory. The single JSON envelope contains two actual trusted local runtime outcomes, provider-call evidence, and explicit `fixture_only` / `no_audio_bytes` flags.

`--no-grants` and `--cancelled` refuse before provider calls. `--invalid-output` exercises schema rejection after the mock provider returns. These failure demonstrations exit1; default successful metadata validation exits0; invalid arguments exit2.

All metadata is illustrative: zero hashes do not identify real media, content remains unverified, license evidence is unknown, and nothing is played, generated or stored as audio. Runtime readiness is not teaching approval. Two sequential requests demonstrate separate voice IDs, not a new dialogue output contract or automatic full P03 acceptance.

Authorship: Qwen supplied the initial draft; after repeated empty repair turns, the controller replaced the implementation and tests to resolve verified defects. Independent review and offline tests remain required.
