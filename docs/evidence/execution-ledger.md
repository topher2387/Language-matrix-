# Language Matrix execution ledger

Coordinator run: 2026-10-19. User scope: execute P00, delegate remaining bounded packets according to dependencies, publish tested work/evidence, zero spending, no Lichen modifications.

## Accepted foundation

P00 commit `30e4696`, PR [#10](https://github.com/topher2387/Language-matrix-/pull/10). Seven structural/security contract tests pass. Independent read-only review checked the pinned upstream interfaces and found no material P00 gaps. PR is open; no issues closed.

## Dependency queue

| Packet | Execution state | Dependency / next acceptance gate |
| --- | --- | --- |
| P01 #2 | Initial [worker #11](https://github.com/topher2387/Language-matrix-/issues/11) timed out/blocked; compact successor [#19](https://github.com/topher2387/Language-matrix-/issues/19) staged | P00 contracts; semantic validator, 25 provisional cases, independent Korean review and model benchmark evidence distinct from code tests. |
| P02 #3 | Admitted: [worker #12](https://github.com/topher2387/Language-matrix-/issues/12) | P00 contracts; mocked lesson, browser mobile/desktop and actual offline reload evidence. |
| P03 #4 | Admitted: [worker #13](https://github.com/topher2387/Language-matrix-/issues/13) | P00 contracts; mocked provider state flow, adversarial requests, output/deadline/permission validation. |
| P04 #5 | [Worker #14](https://github.com/topher2387/Language-matrix-/issues/14); dependency blocked | Accepted P03; external adapter only, zero-cost/quota/idempotency/GPU guard evidence. |
| P05 #6 | [Worker #15](https://github.com/topher2387/Language-matrix-/issues/15); dependency blocked | Accepted P03; SQLite/blob integrity/migration/GC evidence, parallel with P04. |
| P06 #7 | [Worker #16](https://github.com/topher2387/Language-matrix-/issues/16); dependency blocked; host GPU available | Accepted P04/P05; weight licences, approved host CUDA execution, Korean review and playable synthetic voice evidence. |
| P07 #8 | [Worker #17](https://github.com/topher2387/Language-matrix-/issues/17); dependency blocked; optional | Accepted P04/P05; safe image fallback and asset provenance. |
| P08 #9 | [Worker #18](https://github.com/topher2387/Language-matrix-/issues/18); dependency blocked | Accepted P01–P06; actual phone/offline/audio demonstration and resource evidence. P07 optional. |

The Forge supervisor serializes model phases through one shared provider quota ledger. Independent packets may be admitted together, while inference is bounded and serialized. Operator ceilings are local safety limits, not claims of provider entitlement. Fresh zero-price catalogue checks precede inference; no paid/unknown fallback or billing activation.

## Known limits

- All linguistic development fixtures are unverified; tests do not constitute human Korean review.
- Initial sandbox GPU probe failed because device nodes are hidden. Approved host probe succeeds: RTX 3060 Ti, 8192 MiB, driver 580.178.04; A tiny PyTorch CUDA calculation passed (see p00-cuda-host.txt); model workload measurements are separate.
- Cached Qwen code/weights exist but weight licence confirmation and audio assessment remain outstanding (see p06-readiness.md).
- Lichen and the inspected Forge checkout were clean at observed baselines. No writes to either checkout are authorized or performed by this project.
- State/config/raw transport transcripts stay in ignored `.dev-harness`; only sanitized outcomes are public evidence.

No queued/deferred job is marked complete from a worker assertion. Record command outputs, review findings, PR URLs and unresolved acceptance items before advancing dependent packets.

## Worker diagnosis and operator forecast ruling

P01 first worker timed out at 240 seconds after 8 completed steps; process group exited, no partial outputs copied back, final usage unknown. Original job and its full 16-request reservation remain preserved. P02 generation returned a complete stop result at 16 steps and zero reported cost, with 579849 observed tokens. Its source still requires tests, independent review and real browser evidence.

The initial 12000-token forecast was too small because every context/cached input counts across steps. Before further inference, project-local ceilings changed to 240 requests/day and 10M tokens/day with 20% reserve; forecasts are 700k/worker and 150k/reviewer, finite 16-step/600-second worker calls. These are bounded operator safety budgets, never provider-entitlement claims. Shared DB, reservations and pricing/429/positive-cost hard stops remain intact. No billing activation or paid fallback. The compact P01 successor reuses jsonschema and narrows gratuitous APIs rather than replaying the failed original job.
