# Language Matrix
Standalone, local-first Korean language tutor. **P00 contracts are validated and published for review; P01/P02/P03 worker execution is underway. No usable-product milestone is claimed yet.**

Current execution evidence: [ledger](docs/evidence/execution-ledger.md), [P00 PR #10](https://github.com/topher2387/Language-matrix-/pull/10), and [contracts](docs/contracts/README.md). GPU access works under approved host execution; the restricted sandbox hides GPU devices.

## Start here (Codex / worker coordinator)
1. Read [implementation charter](docs/IMPLEMENTATION_PLAN.md) and all [execution packets](https://github.com/topher2387/Language-matrix-/issues).
2. Start [P00 — contracts/harness inspection](https://github.com/topher2387/Language-matrix-/issues/1). Observe the actual existing quota-worker interfaces in Lichen/Forge read-only; do not assume they have a particular API.
3. After P00 contracts, independently delegate [P01 lesson engine](https://github.com/topher2387/Language-matrix-/issues/2) and [P02 browser GUI](https://github.com/topher2387/Language-matrix-/issues/3) in parallel to appropriately skilled workers/models. These are the urgent usable-product path.
4. [P03 capability requests](https://github.com/topher2387/Language-matrix-/issues/4), [P04 worker adapter](https://github.com/topher2387/Language-matrix-/issues/5), [P05 asset library](https://github.com/topher2387/Language-matrix-/issues/6) then [P06 synthetic Korean voices](https://github.com/topher2387/Language-matrix-/issues/7), [P07 illustrations](https://github.com/topher2387/Language-matrix-/issues/8), [P08 integrated demo](https://github.com/topher2387/Language-matrix-/issues/9) according to explicit dependencies.

## Execution rules
- This is a **work queue**, not permission to bypass approval gates or spend money. The coordinating worker is responsible for PR integration and acceptance evidence, not necessarily code authoring.
- Delegate bounded, independent tasks; each assignment must carry issue number, objective, dependencies, files owned, validation command, expected deliverable and stop conditions.
- Distinct branches/PRs per packet. No automatic merges without passing tests and review.
- Prefer free local/open models; remote quotas only when allowed by provider terms and configured. Never activate billing.
- Maintain English / Hangul / accurate *spoken* phonetics / phonological explanation in every lesson.
- Cached lessons must work offline. No student telemetry/adaptation in v1.
- Close an issue only with links to merged PR, tests and actual operation evidence. Report blocked work explicitly.

## Paste into Codex
> Open topher2387/Language-matrix- (exact repo: topher2387/Language-matrix-, remove any zero-width spacing). Read README.md and docs/IMPLEMENTATION_PLAN.md, then GitHub issues #1–#9. Act as coordinator: execute P00 first, delegate P01 and P02 as independent bounded packets after contracts, use verified existing workers and other models where possible, respect dependencies, 0-cost gate, PR review/tests, and do not alter the upstream Lichen repo. Publish all work and evidence back to GitHub. Do not mark a task complete until its acceptance checks run.

