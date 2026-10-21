# P04 Worker Adapter Progress — qwen80/p04-worker-adapter

## Status: Implementation in progress — BLOCKED on two defects

### Completed
- [x] Read issue requirements and progress tracking
- [x] Inspect existing scheduler version/API (read-only)
- [x] Inspect Lichen harness tools (read-only)
- [x] Inspect dispatch config and quota ledger (read-only)
- [x] Implement worker_adapter.py with quota-aware adapter
- [x] Fix _admit_model fail-closed admission defects (missing/negative/NaN/malformed cost, malformed expiry, nonboolean flags, absent privacy/rate evidence)
- [x] Add provider-only admission lookup (is_admitted_by_provider, get_admissions_by_provider, get_admission_by_provider)
- [x] Fix WorkerAdapter.submit_job to resolve admission by provider when request has no model
- [x] Fix tests: timeout_seconds 600 -> 300; remove schema-rejected "model" field; align config provider with request provider ("local"); add cost_usd: 0 and privacy_level/rate_limit to admit configs

### In Progress
- [ ] Run full test suite and verify PASS (currently 1 failure + 5 errors)
- [ ] Write targeted regression tests for _admit_model fail-closed defects
- [ ] Write docs/worker-adapter.md
- [ ] Commit changes, push branch, create DRAFT PR
- [ ] Post progress and evidence to issue5 and tracker24

### Blockers (2)
1. **sqlite3.ProgrammingError: Cannot operate on a closed database** — MockScheduler caches connections by path `":memory:"`; `submit_job` closes the cooldown-check db in `finally`, then `_attempt_reservation` re-connects `":memory:"` and gets the same closed connection. Fix: MockScheduler `_get_db` must recreate a connection if the cached one is closed (or `submit_job` must not close the cooldown-check db before reservation).
2. **test_submit_expired_provider** — `'expired' not found in 'Provider not admitted: local'`. The provider-only lookup `is_admitted_by_provider("local")` returns False even though the config admits "local/model-a". Need to debug why admission is not registered or lookup fails.

### Next Steps
- [ ] Fix MockScheduler connection management (closed-db reuse)
- [ ] Debug and fix test_submit_expired_provider admission lookup
- [ ] Run full test suite and verify 159 PASS
- [ ] Add regression tests for fail-closed admission defects
- [ ] Write docs/worker-adapter.md
- [ ] Commit owned changes, push branch qwen80/p04-worker-adapter
- [ ] Create DRAFT PR against review/added-work-20261019 via gh --body-file
- [ ] Post factual progress and final evidence in issue5 and tracker24

## Source Commit/API Documentation

### Lichen Scheduler Interface (read-only)
- **Repository**: topher2387/Lichen-forge-service-activation-20261018
- **Commit**: 8fe63dbbca3fe78846d85fec71b8ddb50e4b04e2
- **Key Files**:
  - `tools/quota_ledger.py` - SQLite quota ledger with `reserve()`, `observe()`, `connect()`
  - `tools/free_dispatch_gate.py` - Free-only dispatch gate using quota ledger
  - `tools/free_model_router.py` - Model selector with quota reservations
  - `tools/provider_cooldowns.py` - Provider/scope cooldown ledger

### Scheduler API Summary
```python
# quota_ledger.py
def connect(path) -> sqlite3.Connection
def reserve(db, *, task, provider, model, scope, daily_limit, minute_limit, 
            token_limit, tokens, reserve_fraction=0.15, now=None, requests=1,
            daily_token_limit=None, protected_requests=0, protected_tokens=0) -> str
def observe(db, provider, scope, metric, window, remaining, source, now=None) -> None
```

### Dispatch Gate API Summary
```python
# free_dispatch_gate.py
def dispatch(config, db, task, *, now=None) -> dict
# Returns: {"status": "selected"|"defer", ...}
```

### Model Router API Summary
```python
# free_model_router.py
def validate(config) -> dict
def classify(task) -> str  # "routine"|"coding"|"reasoning"
def choose(config, state, task, now=None) -> dict|None
def reserve(state, model, task, now=None) -> dict
```

## Implementation Plan

### worker_adapter.py
1. **ProviderRegistry** - Admit only verified free providers with explicit quotas
2. **WorkerAdapter** - Inject scheduler interface, delegate quota logic
3. **Job States** - pending/running/ready/failure/refused
4. **Idempotency** - Reservation-based admission with SQLite
5. **Bounded Retries** - Configurable retry budget
6. **Cancellation/Deadlines** - Integrate with existing capability request deadlines
7. **Quota Exhaustion Fallback** - Only to explicitly admitted zero-cost alternative
8. **GPU Concurrency Guard** - Single GPU-heavy job at a time

### Test Strategy
- Mock scheduler/provider for offline tests
- Cover all job states
- Test idempotency
- Test quota exhaustion fallback
- Test paid/unknown provider refusal
- Test adversarial inputs

## Commands
```bash
# Run P04 tests
python3 /home/topher/Language-matrix-coder/qwen80-cache-setup/test-p04-snapshot.py LABEL

# Full suite
python3 -B -m unittest discover -s tests -v
```
