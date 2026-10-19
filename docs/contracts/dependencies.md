# Execution dependencies

Source: GitHub execution issues #1–#9, inspected 2026-10-19. Follow explicit issue dependencies rather than interpreting the prose delivery order as a serial queue.

| Packet | Issue | Prerequisites | Acceptance boundary |
| --- | --- | --- | --- |
| P00 | #1 | none | Read-only harness evidence, schemas, valid samples, registry, dependency map. |
| P01 | #2 | P00 | Engine + semantic validation + phonology fixtures; independent review and accessible-model benchmarks must be honestly evidenced or blocked. |
| P02 | #3 | P00 | Independent mocked-lesson GUI; desktop/mobile and offline browser evidence. |
| P03 | #4 | P00; integrates P01/P02 | Refusal/approval semantics and pending/ready/failure flow; no arbitrary execution. |
| P04 | #5 | P00, P03 | External quota adapter, zero-cost hard stop, retry/deadline/idempotency/GPU tests. |
| P05 | #6 | P00, P03 | SQLite provenance, hash storage, dedup, corruption/migration/GC tests. Parallel with P04. |
| P06 | #7 | P04, P05 | Licensed accessible Korean TTS benchmark and playable multi-identity samples, or explicit failure. |
| P07 | #8 | P04, P05 | Optional images with provenance; availability never gates lesson usability. |
| P08 | #9 | P01, P02, P03, P04, P05, P06 | Integrated phone/offline demo, actual audio, resource measurements and tests. P07 optional. |

Start P01 and P02 concurrently once P00 contracts land. P03 can start from contracts as a third bounded worker, integrating engine/GUI only when ready. Dispatch P04/P05 after accepted P03, and P06/P07 after both prerequisites. Do not equate a provider stub or queued assignment with execution evidence. Separate branches/PRs per packet; coordinator reviews/tests before merge. Close issues only with merged PR and real acceptance evidence. Unavailable model, human linguistic review, licence, credentials, service or free quota remains an explicit blocker; never buy access.
