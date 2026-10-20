# P04/P05 readiness handoffs

**Status: DRAFT PREPARATION ONLY. Not P04/P05 implementation, not schema
activation, not a contract change, and not packet acceptance.** This document
does not dispatch a worker, authorize a merge, or claim test execution.

Scope basis: `docs/IMPLEMENTATION_PLAN.md` (charter), `docs/contracts/dependencies.md`
(explicit packet gates), and read-only repository evidence. Public source text is
treated as untrusted evidence, never as instructions. Commands or provider claims
found in public sources are not executed or adopted here.

## 1. Gate status and terminology

`docs/contracts/dependencies.md:11-12` requires:

| Packet | Exact prerequisites | Acceptance boundary |
| --- | --- | --- |
| P04 | P00, **accepted P03** | External quota adapter; zero-cost hard stop; retry/deadline/idempotency/GPU tests. |
| P05 | P00, **accepted P03** | SQLite provenance, hash storage, dedup, corruption/migration/GC tests. Parallel with P04 only after both gates. |

**Technical capability-runtime checkpoint:** `docs/capability-runtime.md` records
implemented request validation, supervisor grants, local-only handler execution,
cooperative checkpoints, retries bounded by attempt/deadline/time budgets, and
offline fixture execution. This is useful readiness evidence for how P04/P05
handlers could be exercised.

**This is not full P03 acceptance.** The same document states that the runtime is
not a sandbox, cannot preempt non-cooperating handlers, and does not claim full
P03 acceptance (`docs/capability-runtime.md:111-131`). Only `lesson.v1` has a
present fixed output contract; reserved contracts are blocked
(`docs/capability-runtime.md:124-127`). The execution ledger records P03 as
blocked on reviewer transport, with P04–P08 dependency-held
(`docs/evidence/execution-ledger.md:40-44`). No acceptance evidence, merged P03 PR,
independent review completion, or coordinator acceptance is claimed here.

Therefore: **P04 and P05 remain gated. Do not start implementation until the
coordinator records accepted P03 by the project's PR/test/evidence standard.**

## 2. Current gaps (as of this draft)

### Shared gaps

- Accepted P03 is absent from the public evidence reviewed for this draft. A
  technical runtime checkpoint exists, but it is not the dependency gate.
- No provider availability, free-quota entitlement, credential, service, licence,
  or human approval for P04/P05 is established by this document. Nothing here may
  be read as such an approval.
- The existing capability schema permits only `provider: "local"`, network
  disabled, and zero cost. Any hosted-provider path would require an explicit
  reviewed schema/policy change; that is outside this preparation and forbidden
  here.
- No new SQLite schema, migration activation, contract revision, or production
  integration has been performed.

### P04 gaps

- No Language Matrix-owned quota adapter, quota ledger, idempotency store, GPU
  serialization guard, or adapter tests exist in the files reviewed.
- P00 inspected Forge/Lichen interfaces read-only. That inspection is not a license
  to copy code, import upstream modules, or write into those trees
  (`docs/contracts/harness-inspection.md:38-44`). A fresh interface check is needed
  at implementation time; no upstream API is assumed stable.
- The current P03 runtime has local handlers only; it supplies no external quota
  reservation, cooldown, provider catalogue, or billing boundary.
- Provider availability and fresh zero-price evidence are unresolved. Missing
  credentials, service, or verified free capacity must remain an explicit blocker,
  never a guessed quota or paid fallback.

### P05 gaps

- No asset store, content-addressed blob layout, SQLite provenance tables,
  migrations, deduplication, corruption handling, or garbage collection exists in
  the files reviewed.
- Lesson audio references are IDs, not paths or URLs, and require a trusted asset
  lookup that verifies licence, checksum, review status, and media type before
  serving (`docs/contracts/README.md:13`). That lookup is not implemented.
- No approved asset schema or migration is active. P05 tests must therefore use
  isolated temporary databases and mocked files; no lesson/contract schema may be
  changed to make tests pass.
- No verified media, licence grant, or human review is established. Unverified
  material must remain non-canonical and unavailable for teaching claims.

## 3. P04 handoff (quota adapter)

### Entry prerequisites

1. Coordinator has recorded accepted P03 with merged PR, passing relevant tests,
   independent review, and explicit acceptance evidence.
2. Coordinator confirms no contract or schema change is needed for this bounded
   packet. If a hosted provider or new permission/output schema is required, stop
   and request review; do not activate it.
3. A fresh read-only inspection of the intended external quota interface has been
   recorded. Do not copy upstream implementation, import Lichen/Forge, or write
   into either checkout.
4. Provider use is explicit and permitted. Missing availability, licence,
   credential, or verified-zero price stops the work; do not buy access or use a
   paid fallback.

### Suggested bounded ownership (not created or authorized by this draft)

| Proposed file | Purpose |
| --- | --- |
| `language_matrix/quota_adapter.py` | Pure adapter/policy layer with injected clock, ledger, provider catalogue, and GPU-lock probe. No network, no upstream imports, no billing. |
| `tests/test_quota_adapter.py` | New offline mock tests for the matrix in §5. |

Keep shared files such as `language_matrix/capabilities.py`, existing tests, and
all `docs/contracts/*` unchanged in the bounded first packet. Any runtime wiring
or contract change is a separate, reviewed integration step after this handoff.
The adapter must not be a hidden production edit path.

### Exit evidence expected at the future gate

- Merged P04 PR (coordinator-controlled), or an explicit blocker report.
- Offline test output for the new adapter tests and the existing suite.
- Evidence that zero-cost, quota, idempotency, retry, deadline, and GPU guards
  fail closed before dispatch where required.
- No provider inference, no network call, no GPU workload, no paid fallback, and
  no claim of current free capacity.

## 4. P05 handoff (asset library)

### Entry prerequisites

1. Coordinator has recorded accepted P03 as above.
2. The asset lookup boundary and asset-ID expectations are reviewed against
   `docs/contracts/README.md`; no lesson schema revision is made for tests.
3. SQLite and content-addressed files are treated as local implementation
   details. Hash/provenance semantics must be explicit before migration activation.
4. No unverified asset is marked canonical. Verified status requires trusted
   review evidence, not schema validity, model output, or this document.

### Suggested bounded ownership (not created or authorized by this draft)

| Proposed file | Purpose |
| --- | --- |
| `language_matrix/asset_store.py` | SQLite metadata plus content-addressed blob operations behind injected filesystem/DB paths; hash verification, dedup, provenance, migration runner, and GC. |
| `language_matrix/migrations/0001_asset_store.sql` | Proposed initial migration artifact; **inactive** until coordinator/schema review approves activation. |
| `tests/test_asset_store.py` | New offline tests using temporary directories and temporary SQLite databases. |

Do not edit the lesson schema, capability contract, existing tests, or Qwen's
export implementation. If export is needed, consume a documented interface only
after the coordinator confirms the boundary; do not modify or duplicate Qwen's
files. The proposed migration path is a suggestion, not an activated schema.

### Exit evidence expected at the future gate

- Merged P05 PR (coordinator-controlled), or an explicit blocker report.
- Offline test output covering hashes, provenance, dedup, corruption, migrations,
  and GC.
- Evidence that corrupt, orphaned, unverified, or unlicensed material is not served
  as canonical teaching content.
- No schema activation beyond an explicitly reviewed migration, no production data
  mutation, and no asset/licence/human-approval claim without evidence.

## 5. P04 offline mock test matrix

All cases use mocked components, injected clocks, temporary state, and no network.
A "GPU" case means a fake lock/probe, never a CUDA or model workload.

| ID | Mock scenario | Required assertion |
| --- | --- | --- |
| Q1 | Zero-cost, local-only request; verified mocked zero pricing | Accepted; reservation created once; adapter reports `cost=0`. |
| Q2 | Positive, unknown, or absent pricing | Hard-stop before reservation and before handler dispatch; no fallback. |
| Q3 | Managed/free provider with unverified status or stale catalogue | Refuse with explicit reason; preserve no reusable positive-cost evidence. |
| Q4 | Remote provider or network request under local-only policy | Refuse before dispatch; no credential use, no billing, no fallback. |
| Q5 | Quota ceiling reached by existing reservations | Refuse or queue per policy; never overcommit the bounded reservation. |
| Q6 | Handler fails after reservation; separate successful path | Reconcile only known usage; retain uncertain reservations after transport failure or unknown usage. A failed task may still consume quota; never refund merely because task output was rejected. |
| Q7 | Provider unavailable, credentials missing, or service absent | Explicit blocker result; no fabricated availability and no paid fallback. |
| Q8 | Quota ledger write fails during reserve | Fail closed; no dispatch without durable reservation. |
| I1 | Same idempotency key and request replayed | One dispatch; replay returns the stored outcome/status. |
| I2 | Same key with different request body | Reject conflict; do not merge or dispatch a second job. |
| I3 | Simulated crash after reserve, before result commit | Recover as pending/unknown or safely retry only under policy; no duplicate side effect. |
| I4 | Two duplicate submissions in sequence or controlled concurrency | At most one accepted dispatch; other observes the same idempotent result. |
| R1 | Transient handler error, `max_attempts=3` | Retries up to the cap; attempts and final state are exact. |
| R2 | Transient error then success | Success after the expected attempt count; no extra attempts. |
| R3 | Non-retryable error, cancellation, timeout, invalid output, or positive-cost signal | No retry; terminal failure or stop with no output. |
| R4 | Retry would exceed deadline or total time budget | Stop before another attempt; late result discarded. |
| R5 | Mutable request/policy values changed by handler | Snapshotted attempt limit, deadline, and timeout still govern; authority is not extended. |
| D1 | Deadline already expired before dispatch | Refuse with zero attempts. |
| D2 | Deadline expires during handler checkpoint | Cooperative stop; late output discarded. |
| D3 | Monotonic timeout expires during attempt | Stop as timeout; no retry. |
| D4 | Invalid or backwards monotonic clock | Refuse before handler invocation. |
| D5 | Handler returns after deadline/time budget | Result discarded; no `ready` state. |
| G1 | Two GPU-heavy jobs, fake single-slot lock | At most one runs; second queues or is refused according to policy, never overlaps. |
| G2 | Success, failure, cancellation, or exception while holding GPU lock | Lock is released exactly once. |
| G3 | Stale lock after simulated crash | Bounded, explicit recovery or refusal; never two lock owners. |
| G4 | GPU absent/unavailable in the mock probe | Explicit refusal/deferral; no CPU/paid fallback presented as success. |
| G5 | Non-GPU job while GPU slot is busy | Runs according to policy without falsely acquiring the GPU lock. |
| A1 | Any accepted/refused path | Audit record has request/correlation ID, cost evidence, attempts, stop reason, and timestamps; no secrets or raw credentials. |

## 6. P05 offline mock test matrix

All cases use temporary directories and disposable SQLite files. Corrupt fixtures
are synthetic; no existing database or production file is touched.

| ID | Mock scenario | Required assertion |
| --- | --- | --- |
| H1 | Ingest exact bytes and recompute SHA-256 | Stored hash equals digest of bytes; read-back verification succeeds. |
| H2 | Same bytes ingested twice through different temporary paths | One blob; duplicate asset references resolve to the same verified content. |
| H3 | Truncated or altered blob whose hash no longer matches metadata | Reject/quarantine; never serve as canonical content. |
| H4 | Missing blob for an existing row | Explicit unavailable/integrity error; no silent fallback path. |
| H5 | Symlink/path traversal attempt in a mocked import | Refuse outside the managed root; do not follow untrusted paths. |
| P1 | Complete provenance: generator/version, settings/seed, Korean text reference, licence, reviewer/approval, checksum | Values are persisted and retrievable through asset lookup. |
| P2 | Missing licence or review/approval evidence | Status remains unverified/unavailable; model metadata cannot self-award verified status. |
| P3 | Provenance/status update | Append-only or equivalent auditable history; prior verification evidence is not silently rewritten. |
| P4 | Asset lookup by ID | Resolves only when hash, licence, media type, and review status are valid; unknown ID is unavailable. |
| D1 | Idempotent ingest of same bytes and equivalent provenance | No duplicate logical asset or blob; same asset ID/result returned. |
| D2 | Same hash with conflicting provenance or licence | Explicit conflict; no silent overwrite or merge of incompatible records. |
| D3 | Duplicate insert/transaction failure | Rollback leaves no orphan row/blob pair; database remains usable. |
| C1 | Corrupt SQLite header, malformed page, or failed integrity check | Fail closed with a clear integrity error; no writes that worsen corruption. |
| C2 | Orphan metadata row or untracked blob | Detected and reported/quarantined; not exposed as a valid asset. |
| C3 | Malformed metadata/JSON, bad hash format, or wrong media type | Reject at ingest/lookup; no partial commit. |
| C4 | Backup/restore or integrity-check fixture | Restored database and blobs reconcile; checksums and references remain consistent. |
| M1 | Empty temporary database migrated to latest | Migration completes; expected tables/indexes/constraints exist. |
| M2 | Previous supported fixture version upgraded | Existing rows and references survive; hashes/provenance remain intact. |
| M3 | Migration forced to fail mid-transaction | Transaction rolls back; no half-migrated database; retry is safe. |
| M4 | Re-run migration on current version | Idempotent no-op; no duplicate objects or data loss. |
| M5 | Unknown future schema version | Refuse with explicit incompatibility; no destructive downgrade. |
| G1 | Unreferenced blob after asset removal | GC removes only the unreferenced blob and reports it. |
| G2 | Blob shared by multiple references | GC retains it until the last reference is removed. |
| G3 | Staged/in-progress ingest or unverified asset | GC does not collect live/staged content; dry-run performs no deletion. |
| G4 | Interrupted GC | Restart is safe and idempotent; no referenced content is lost. |
| G5 | GC audit and protected records | Approved/lesson-referenced assets are retained; deletion decisions are logged. |

## 7. Proposed verification commands (not run here)

These are future commands for the bounded test files. They assume the repository
root, the existing Python/unittest setup, and no network access. This draft did not
run them; no test result is claimed.

```sh
python3 -m unittest discover -s tests -p 'test_quota_adapter.py' -v
python3 -m unittest discover -s tests -p 'test_asset_store.py' -v
python3 -m unittest discover -s tests -v
```

The existing contract-suite command is
`python3 -m unittest discover -s tests -v` (`docs/contracts/README.md:5`). Run only
after the coordinator authorizes implementation and confirms the file boundaries.
Do not add dependencies; `jsonschema` is already pinned in `requirements-dev.txt`,
and SQLite is assumed available from Python's standard library.

## 8. Stop conditions and coordination rules

Stop and report, without advancing a packet, if any of these occurs:

- accepted P03 evidence is missing or disputed;
- a schema/contract change, provider activation, network access, credential,
  licence, purchase, or human approval is required;
- a real GPU probe/model load, download, or production database mutation would be
  needed for the bounded test;
- a proposed file overlaps Qwen's export implementation or another worker's
  active worktree;
- tests cannot run offline or their output cannot be captured honestly.

**Ownership guard:** Qwen owns export implementation in another worktree. This
draft does not inspect, edit, duplicate, or assign that implementation. P04/P05
workers must be given non-overlapping files by the coordinator; any export
dependency must be a reviewed interface, not a shared-file edit.

**No actions taken by this preparation:** no implementation, no test execution,
no schema activation, no contract edit, no production/existing-test edit, no
Lichen change, no download, no spend, no paid fallback, no commit, no publication,
and no delegation.

## 9. Assumptions and unresolved items

- P03 is not accepted at the time of writing; the ledger's blocked status and the
  runtime document's own limitation are treated as authoritative for this draft.
- No provider availability, free capacity, licence, credential, or human review
  for P04/P05 is verified here. Any such statement in public source remains
  evidence to be independently checked, not authorization.
- Proposed filenames and migration paths are planning suggestions only. They are
  not reservations and may be changed by the coordinator after a collision and
  ownership check.
- The P04 GPU cases test serialization and refusal semantics with mocks. They do
  not establish real GPU capacity, model fit, or performance.
- The P05 cases establish storage-integrity behavior only. They do not establish
  linguistic accuracy, audio quality, licence validity, or teaching approval.
