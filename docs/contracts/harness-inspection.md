# Existing harness inspection (P00)

Read-only source inspection on 2026-10-19. No worker, service, inference, or existing database was started or modified for this inspection.

## Sources pinned

- Forge checkout: `/home/topher/Lichen-forge-service-activation-20261018`, HEAD `8fe63dbbca3fe78846d85fec71b8ddb50e4b04e2`.
- Lichen checkout: `/home/topher/Lichen`, HEAD `6bdaa82a529e19b00a6134b67d2115e8f14a6fc8`.
- Observed interfaces: `tools/free_harness_supervisor.py`, `free_harness_runtime.py`, `free_model_router.py`, `quota_ledger.py`, `provider_cooldowns.py`, `github_opencode_poller.py`, `forge_capsule.py`; operator contracts `docs/forge/{supervised-activation,user-service}.md`.

## Concrete boundary

Forge is a Python module/CLI, not an HTTP worker service. `Supervisor(repo, db_path, config, transport)` manages durable phases and calls `Runtime.model`, `.tests`, `.deliver_code`, `.publish`, `.reconcile_quota`. The supervisor CLI actions are `run`, `once`, `status`, `discover`, `sleep`, `wake`, `activity`; options include `--repo`, `--db`, `--config`, `--issue`, `--max-ticks`, `--interval`.

External repositories are supported through the local `--repo` path and `config.repo` GitHub identity. Database identity binds both paths; use a new Language Matrix database. Worktrees are made under the target repository. Run the module with imports resolving to the installed Forge checkout and all writable configuration/state under Language Matrix. Do not copy upstream code or write configuration/state into Lichen. Existing `status` is not a read-only probe: constructing `Supervisor` initializes/migrates state, memory and sleep-control files.

Issue intake requires the configured owner as author, labels `lichen-approved` and `lichen-opencode-task`, and an entire body containing a fenced JSON object with `id`, `model`, `prompt`, optional `complexity` (`routine|coding|reasoning`) and `importance` (`routine|important|critical`). Ordinary execution issues are therefore coordinator specifications, not directly executable worker prompts. Intake is immutable after acceptance. Dependency ordering must be enforced by the Language Matrix coordinator; no packet DAG interface was observed.

## Zero-cost and safe readiness probes

`Runtime.discover(absolute_standalone_opencode_path)` runs `models --refresh --verbose --pure` in a fresh Bubblewrap workspace with no auth, empty environment, denied tools and bounded 60-second execution. It uses network for catalogue retrieval but performs no inference. It does not establish authentication or capacity. Prefer this API to discovery through a Snap wrapper. A catalogue can be obtained without any GitHub token:

```python
from tools.free_harness_runtime import Runtime
catalogue = Runtime.discover('/absolute/path/to/standalone/opencode')
```

Before each model dispatch, Forge requires the exact model ID in `LICHEN_FREE_MODELS`, `verified_free: true`, enabled configuration, fresh catalogue pricing with numeric zero input/output and all other supplied costs, and nondeprecated status. Catalogue failure clears positive pricing evidence. Operator quotas are conservative configured ceilings, not provider entitlement claims. Quota reservation, cooldowns and independent reviewer eligibility remain required. No billing activation, paid fallback or guessed quota is allowed. A bounded inference pilot is a separate readiness test after these gates; failed/unknown cost, timeout or missing final stop event must block/defer visibly.

Configuration uses explicit public `model_source_paths`, including intended new outputs; these are also the write-back boundary. Set `require_independent_review: true`, exact model limits and an operator-controlled argv `test_command`. A reasoning reviewer distinct from every author used across repairs is required. Worker calls reserve 2–32 requests; reviewers reserve two. Tests run offline with installed system tools and must not download dependencies.

## Security, delivery and licensing limits

Worker capsules expose selected source only, fresh denied tool permissions, and only the selected provider auth entry; provider network access is shared and is not a domain egress firewall. Test capsules omit credentials and Git history and have no network. No host-home mounting or unsandboxed fallback. GitHub credentials stay in the parent publisher environment and must never appear in config, argv, logs or public evidence.

Interruption leaves durable inflight uncertainty and blocks replay; do not clear markers to retry publication. Publish reviewed/tested draft PRs and sanitized evidence, never automatically merge/deploy. Raw private databases and model transcripts are not automatically safe GitHub artifacts. The systemd adapter is optional lifecycle tooling, not a new scheduler; do not install/start it for this project.

Lichen's `lichen/runtime/scheduler.py` exposes `Scheduler(registry, budget, observations).choose(candidates)` for semantic/resource admission, returns `SchedulerResult(plan, rejections)`, and commits resource reservations after fresh observation. It is not a provider quota worker API and should not be imported as the Language Matrix dispatch service.

No license grant was found in the inspected upstream README/pyproject or repository license filenames. This is not a legal conclusion: inspect and obtain explicit licensing permission before copying upstream implementation. Integrate through an external adapter contract. Language Matrix assets must independently retain generator/model/license/provenance and verification metadata; never mark unverified output canonical.

## Availability conclusion

Source interfaces and safety gates are established. No claim of current free provider availability, authentication, inference success, or remaining quota follows from this read-only inspection. Record fresh discovery and a bounded pilot separately before assigning remote work.
