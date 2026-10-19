# P06 preliminary local readiness (2026-10-19)

This is read-only inventory, not P06 implementation or benchmark acceptance. P06 remains gated on P04/P05. No TTS inference, download, audio synthesis, billing, driver changes or service startup occurred. The coordinator subsequently performed the approved tiny host CUDA computation recorded below. **No Korean audio was tested or independently assessed here.**

## Upstream working-tree baseline

`git -C /home/topher/Lichen status --short` returned empty output at HEAD `6bdaa82a529e19b00a6134b67d2115e8f14a6fc8`.

`git -C /home/topher/Lichen-forge-service-activation-20261018 status --short` returned empty output at HEAD `8fe63dbbca3fe78846d85fec71b8ddb50e4b04e2`.

These are observed clean snapshots during this inventory, not proof of historical changes. Only read commands were issued to these trees. No upstream files were changed by this inspection.

## Installed candidates and cached weights

The existing `/home/topher/miniconda/envs/qwen3tts/bin/python` metadata inventory reports `qwen-tts==0.1.1`, `torch==2.6.0+cu124`, `transformers==4.57.3` and `soundfile==0.13.1` (soundfile resolves from the user site). Imports/inference were not tested. VoxCPM distribution was not installed in either this environment or the base miniconda Python inventory; that is not an exhaustive search of all possible environments.

Package metadata and the installed `qwen_tts-0.1.1.dist-info/licenses/LICENSE` identify the Qwen TTS **code** licence as Apache-2.0. The installed METADATA lines 103–107 list Korean support for VoiceDesign and CustomVoice; line 227 describes the Sohee Korean speaker. These are installed vendor claims, not demonstrated Korean intelligibility or voice authenticity.

The Hugging Face hub is a symlink to `/media/topher/New Volume/cache/huggingface/hub`. Read-only snapshot inventory found:

| Model | Snapshot | Model weights bytes | Tokenizer weights bytes |
| --- | --- | ---: | ---: |
| Qwen3-TTS-12Hz-1.7B-VoiceDesign | `5ecdb67327fd37bb2e042aab12ff7391903235d3` | 3,833,402,552 | 682,293,092 |
| Qwen3-TTS-12Hz-0.6B-CustomVoice | `85e237c12c027371202489a0ec509ded67b5e4b5` | 1,811,626,576 | 682,293,092 |
| Qwen3-TTS-12Hz-1.7B-Base | `fd4b254389122332181a7c3db7f27e918eec64e3` | 3,857,413,744 | 682,293,092 |

These are disk sizes, not VRAM measurements, load verification or checksums. No README/model-card or LICENSE files were found in these inspected snapshots during the initial local-only inventory. Subsequent independent research in [p06-licences.md](p06-licences.md) pins hosted model cards at the exact cached VoiceDesign and CustomVoice revisions above, both declaring Apache-2.0. That resolves their model-card licence attribution; cached weight checksums, embedded tokenizer provenance and runtime workload assessment remain pending. Do not infer weight-byte authenticity or teaching quality from this licence evidence. VoiceDesign is a description-driven candidate; 0.6B CustomVoice is a smaller candidate whose built-in identities must be assessed rather than assumed to satisfy description-driven voice requirements.

Other read-only inventory: base miniconda metadata reports `chatterbox-tts==0.1.7` (MIT code), `f5-tts==1.1.21` (MIT code), `piper-tts==1.4.2` (GPL-3.0-or-later code). None establishes availability/licence/Korean suitability of the associated weights. GPT-SoVITS source at `/home/topher/GPT-SoVITS` has an MIT code LICENSE and cached `s2Gv4.pth`/`vocoder.pth`/`s2Gv3.pth`; it is not the requested description-driven P06 path and was not tested. No existing human reference clips were read or used.

## Sandbox boundary, confirmed host CUDA, and later acceptance

The initial sandbox `nvidia-smi` returned exit 9: `NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.` This observed failure is preserved, but it does **not** indicate a host driver fault: the execution sandbox hides `/dev/nvidia` devices. The coordinator's approved host query outside the sandbox identified an RTX 3060 Ti, driver 580.178.04, 8192 MiB total and 2510 MiB used at that query.

The coordinator then ran an approved offline CUDA calculation outside the sandbox using `/home/topher/miniconda/envs/qwen3tts/bin/python`. The authoritative raw evidence is [p00-cuda-host.txt](p00-cuda-host.txt): exit 0; torch `2.6.0+cu124`; `cuda_available=True`; `device_count=1`; device `NVIDIA GeForce RTX 3060 Ti`; `arange(16)` squares summed to `1240.0` with synchronization; peak allocated memory `1536` bytes; free/total memory `(5410521088, 8211660800)` bytes, approximately **5.04 GiB free** at that moment. No model was loaded or downloaded, and no driver/system/container changes or Lichen edits occurred. My separate approval request was interrupted; these are the coordinator's executed results, not a duplicate probe.

Real host CUDA compute is established. TTS model load/peak VRAM, latency, CPU fallback, intelligibility and actual 8-GB workload feasibility remain unmeasured. Available headroom changes with other running workloads; neither cached disk sizes nor a tiny tensor calculation proves a TTS model fits.

After accepted P04/P05, retain the pinned licence evidence, authenticate cached weight bytes/tokenizer provenance and obtain reviewer-approved phrases; use isolated offline execution before any benchmark. Then measure real load/peak VRAM, timings, intelligibility and repeatability across five phrases and five prompts; retain provenance/checksums and human review evidence. P06 requires at least five playable samples across two audibly distinct identities or an explicit failure. ASR back-check alone cannot verify accent/dialect fidelity. Until that runs, P06 audio acceptance and the audio-dependent P08 demonstration remain open.
