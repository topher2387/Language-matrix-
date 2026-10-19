# P06 preparatory model/licence research — 2026-10-19

Documentation only; P06 implementation/inference remains gated on accepted P04/P05. No weights, packages or reference recordings downloaded; no generation, paid calls, credentials or Lichen writes. The coordinator separately confirmed an RTX 3060 Ti 8-GB host and tiny CUDA computation; sandbox device visibility does not establish a driver failure. This report does not benchmark that host.

## Exact candidates and licences

| Candidate | Weight licence and Korean claim | Reference-free path |
| --- | --- | --- |
| `Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign` | Apache-2.0 metadata; Korean listed in the [exact cached-revision model card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign/blob/5ecdb67327fd37bb2e042aab12ff7391903235d3/README.md). | Description-driven `generate_voice_design(text, language, instruct)`; no human recording input. |
| `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | Apache-2.0 metadata; Korean and built-in speaker Sohee in the [exact cached-revision card](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice/blob/85e237c12c027371202489a0ec509ded67b5e4b5/README.md). | Built-in speaker selection, no human recording required. This is a finite-identity fallback, not arbitrary new identity design. |
| `openbmb/VoxCPM2` | Current [model card](https://huggingface.co/openbmb/VoxCPM2) declares Apache-2.0 and Korean among 30 languages. | Natural-language voice description prefixed in parentheses; explicitly requires no reference audio. No local VoxCPM2 snapshot was established. |

The Qwen implementation has an [Apache-2.0 code LICENSE](https://github.com/QwenLM/Qwen3-TTS/blob/main/LICENSE). Its [official usage documentation](https://github.com/QwenLM/Qwen3-TTS#python-package-usage) distinguishes VoiceDesign, CustomVoice and Base cloning. Base cloning accepts reference audio; it is not needed for either requested first-stage path. That documentation proposes synthetic VoiceDesign output followed by Base cloning for reusable character identity; this would require separately pinned Base provenance and sequential model loading on this machine. The [tokenizer model card](https://huggingface.co/Qwen/Qwen3-TTS-Tokenizer-12Hz) also declares Apache-2.0; retain its actual embedded-weight provenance separately.

OpenBMB explicitly says both weights and code are Apache-2.0 in its [official repository](https://github.com/OpenBMB/VoxCPM), with the [code licence text](https://github.com/OpenBMB/VoxCPM/blob/main/LICENSE). Its documented usage restrictions prohibit impersonation, fraud and disinformation and recommend marking synthetic content. Preserve applicable licence/attribution notices and generated-asset provenance; a model licence is not evidence of Korean accuracy or authentic dialects.

## Cached snapshot confidence

Read-only inspection of cache `refs/main` independently matched the two full Qwen revisions above. The hosted README at **each exact revision** exposes `license: apache-2.0`, so licence attribution can be tied to the cached snapshot identity with confidence, rather than inferred from the installed code licence. The current hosted file trees also showed matching shortened revisions [VoiceDesign `5ecdb67`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign/tree/main) and [CustomVoice `85e237c`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice/tree/main); no revision mismatch was observed.

This improves on the earlier local-only inventory: README/LICENSE absence locally does not mean upstream metadata is unknown. It does **not** authenticate cached weight bytes. Before P06 execution, retain immutable card references, weight checksums, runtime/package version and tokenizer provenance in P05. A future `main` change must not silently change that approval basis.

## CPU and 8-GB feasibility

- **Qwen:** official examples use CUDA/BF16 and recommend FlashAttention 2 to reduce memory. They provide no measured 8-GB peak or CPU latency guarantee. Their “less than 96GB RAM” note concerns FlashAttention compilation parallelism, not an inference RAM requirement. Existing disk inventory is approximately 4.52 GB including tokenizer for VoiceDesign versus 2.49 GB for CustomVoice; disk size is not peak VRAM. Treat single-model, short, batch-one inference as a later experiment, not proven fit. CPU fallback remains unbenchmarked.
- **VoxCPM2:** current card reports approximately 8 GB VRAM and BF16, with Python ≥3.10, PyTorch ≥2.5 and CUDA ≥12 in its quickstart. Its RTX 4090 timing is not transferable to this 3060 Ti. Eight GB leaves uncertain desktop/runtime headroom. Official repository exposes CPU device selection but supplies no CPU RAM/latency measurement; CPU feasibility remains unproven here. Disable optional denoiser/network dependencies for any later offline experiment only after dependency/licence review.

Remaining acceptance work: P04/P05 first; pin actual runtime/weights and dependencies, enforce offline loading and bounded jobs, measure peak memory/time, and independently assess Korean intelligibility, phonology, identity consistency and five playable samples across two distinct identities. No dialect or teaching-quality approval follows from vendor language lists. No tests were run because this change is source-linked documentation only.
