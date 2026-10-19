# Language Matrix — implementation charter
Status: planned; code not yet implemented. 2026-10-19.

## Goal
Standalone, local-first English→Korean interactive tutor. Launch a *usable* lesson engine plus GUI before tracking or adaptive instruction. Preserve a language-neutral architecture for later experiments in two or three languages. Do not couple to Lichen until validated.

## User experience / hard requirements
Each teaching unit co-displays: (1) English meaning and natural translation, (2) correct written Hangul, (3) approachable **spoken** phonetic rendering (not blindly transliterated spelling), and (4) concise causal explanation of relevant Korean phonological changes. Include audio, multiple voices, comparisons of Korean vs English sentence structure/particles/register, and short listening/reading exercises. Explain subtitle paraphrases versus literal meaning. Distinguish genuine dialect variation from standard connected-speech sound rules. Phonetic romanisation is a learner aid, not a replacement for Hangul. Provide control over playback speed and repetition.

## System
- Korean-focused bilingual teaching LLM (benchmark Kanana/EXAONE against held-out expert-reviewed fixtures, licences, measured local memory); model is replaceable, not implicitly authoritative.
- Model emits strictly validated, versioned JSON **lesson plans** and **capability requests**. GUI renders a finite component registry (not arbitrary generated HTML/JS or model-driven shell execution). Build minimal browser GUI immediately after basic engine.
- Extend/adapt existing quota-aware worker mechanisms ONLY after inspecting actual upstream interfaces in Lichen/Forge. Do not copy unverified integrations or couple runtime repos. Expose adapter boundary for local/remote generation providers, rate limits, zero-cost policy, retries, deadlines and audit logs.
- Capabilities: text lessons, Korean phonology/romanisation checks, synthetic Korean voice TTS (Qwen3-TTS, VoxCPM 2 candidates), ASR, images, optional video; deterministic comparison charts and GUI widgets. Voices generated from descriptions where supported; speaker identity consistency, linguistic accuracy and authentic dialects require tests, not assumptions.
- Scheduling: lookup in cache first; validate permission/licence and data; only generate missing resources; queue batch jobs asynchronously, one GPU-heavy job at a time if needed. Deduplicate identical requests, resumable/idempotent jobs, finite retry budgets and no paid API fallback or billing activation.
- Asset storage: SQLite as source of truth for lesson/phrase/asset/provider/provenance/approval relations; content-addressed files for media; optional vector semantic index as derived, rebuildable search view (not authority). Metadata includes prompt, voice profile, generator/version, settings/seed, Korean text, licence, verification status, checksum. Never treat unverified output as canonical teaching content. Avoid retaining student recordings unless opt-in.
- Korean instruction validation: manually verified fixture corpus of phonological transformations, particles, grammar, pragmatic translation. Separate deterministic checks from independent reviewer model checks; latter may disagree. Audio ASR back-check is weak evidence only; human Korean assessment needed for accent fidelity.
- Local first; free remote model capacity is optional and fluctuates. Remote provider use must be explicit, obey terms/limits, redact personal data. No cloud dependency to view cached lessons.
- Security: capability requests are data and require permissioned tool registry; no agent-run code or arbitrary network endpoints. No unattended changes to upstream Lichen. Human approval for financial/credential/repo-permission changes; PR review gates for architectural changes.

## Delivery order
P00 inspection + contracts → P01 bilingual Korean lesson generator + validators → P02 minimal browser GUI → P03 capability request protocol & safe runtime → P04 worker quota adapter → P05 asset library → P06 synthetic Korean voices + multi-speaker exercises → P07 illustrative images/other media → P08 full offline demonstration and benchmarks. P01/P02 start the usable path; P03–P07 are incremental upgrades. Deferred: persistent learner analytics, adaptive teaching, generated video, full personal learning profile.

## First milestone / definition of done
From a phone browser, open a cached or freshly generated Korean lesson; view English/Hangul/true spoken phonetic rendering/explanation simultaneously; play one verified Korean example and repeat; complete a checked exercise; app stays functional offline for cached lessons. All generated content schema-validated and labelled verified/unverified. Demonstrated on intended 8-GB-VRAM computer with realistic resource measurements.

## Worker management
Codex is **coordinator/integrator**, not sole worker. Delegate isolated research, fixture authoring, interface work, benchmarks, tests and documentation to suitable workers/models through existing harness where verified; use separate branches/PRs, test evidence and bounded scopes. Each packet below defines inputs, output, acceptance criteria, dependencies, handoff. Never mark jobs complete from a worker assertion alone. Stop and report missing credentials/services rather than buying access.
