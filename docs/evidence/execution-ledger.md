# Language Matrix execution ledger

Coordinator run: 2026-10-19. User scope: execute P00, delegate remaining bounded packets according to dependencies, publish tested work/evidence, zero spending, no Lichen modifications.

## Accepted foundation

P00 commit `30e4696`, PR [#10](https://github.com/topher2387/Language-matrix-/pull/10). Seven structural/security contract tests pass. Independent read-only review checked the pinned upstream interfaces and found no material P00 gaps. PR is open; no issues closed.

## Dependency queue

| Packet | Execution state | Dependency / next acceptance gate |
| --- | --- | --- |
| P01 #2 | Admitted: [worker #11](https://github.com/topher2387/Language-matrix-/issues/11) | P00 contracts; semantic validator, 25 provisional cases, independent Korean review and model benchmark evidence distinct from code tests. |
| P02 #3 | Admitted: [worker #12](https://github.com/topher2387/Language-matrix-/issues/12) | P00 contracts; mocked lesson, browser mobile/desktop and actual offline reload evidence. |
| P03 #4 | Admitted: [worker #13](https://github.com/topher2387/Language-matrix-/issues/13) | P00 contracts; mocked provider state flow, adversarial requests, output/deadline/permission validation. |
| P04 #5 | Dependency blocked | Accepted P03; external adapter only, zero-cost/quota/idempotency/GPU guard evidence. |
| P05 #6 | Dependency blocked | Accepted P03; SQLite/blob integrity/migration/GC evidence, parallel with P04. |
| P06 #7 | Dependency blocked; host GPU available | Accepted P04/P05; weight licences, approved host CUDA execution, Korean review and playable synthetic voice evidence. |
| P07 #8 | Dependency blocked; optional | Accepted P04/P05; safe image fallback and asset provenance. |
| P08 #9 | Dependency blocked | Accepted P01–P06; actual phone/offline/audio demonstration and resource evidence. P07 optional. |

The Forge supervisor serializes model phases through one shared provider quota ledger. Independent packets may be admitted together, while inference is bounded and serialized. Operator ceilings are local safety limits, not claims of provider entitlement. Fresh zero-price catalogue checks precede inference; no paid/unknown fallback or billing activation.

## Known limits

- All linguistic development fixtures are unverified; tests do not constitute human Korean review.
- Initial sandbox GPU probe failed because device nodes are hidden. Approved host probe succeeds: RTX 3060 Ti, 8192 MiB, driver 580.178.04; A tiny PyTorch CUDA calculation passed (see p00-cuda-host.txt); model workload measurements are separate.
- Cached Qwen code/weights exist but weight licence confirmation and audio assessment remain outstanding (see p06-readiness.md).
- Lichen and the inspected Forge checkout were clean at observed baselines. No writes to either checkout are authorized or performed by this project.
- State/config/raw transport transcripts stay in ignored `.dev-harness`; only sanitized outcomes are public evidence.

No queued/deferred job is marked complete from a worker assertion. Record command outputs, review findings, PR URLs and unresolved acceptance items before advancing dependent packets.
