# Export Runtime Lesson — Final Review (2026-10-20)

**Owner:** this file only.
**Reviewed source:** `tools/export_runtime_lesson.py` (184 lines, single-file static review).
**Method:** static source inspection only. No test execution, no imports, no runtime calls.
**Verdict:** The seven requested controls are present at source level. No high/medium blocking defect found. Four low-severity actionable issues are listed below; they are source-visible and do not rely on the controller's test claims.

## Control verification

| Control | Source evidence | Assessment |
|---|---|---|
| Real `generate_lesson` invocation | Import at line 13; called at line 36 as `generate_lesson(lesson_text)` inside the registered handler | Real call is made, not a static fixture return. Arity/signature compatibility is **unverified** because `language_matrix/lessons.py` was outside the bounded review scope. |
| Exact string selector guard | Lines 55–65: rejects non-`str` (except `None`), loads fixture IDs, requires exact set membership, raises `ValueError` for unknown IDs | Exact, case-sensitive ID match is enforced for explicit `--lesson-id`/API input. `None` is allowed intentionally. |
| Fixed grants / local-only registry | Lines 68–72 register only `("local", "lesson.generate")` with `required_permissions=("local.generate",)`; lines 89–101 request `provider="local"`, no network, zero cost, one attempt, `local.generate`; default grants line 40; `--no-grants` line 157 | Registry is fixed and local-only. Default grant matches handler requirement. `--no-grants` passes an empty grant tuple. Caveat: request `permissions` remains hard-coded to `["local.generate"]` even under `--no-grants` (line 99). |
| Dynamic UTC deadline | Lines 75–77: `datetime.now(timezone.utc)`, `+ timedelta(minutes=5)`, `%Y-%m-%dT%H:%M:%SZ` | Deadline is computed per call, not fixed. Microseconds are truncated before adding five minutes, making the deadline conservatively up to <1s short of exactly five minutes. |
| Boolean cancellation CLI | `--cancelled` is `store_true` (lines 142–146); closure at line 158; passed to runtime at line 108; handler calls `context.checkpoint()` at line 24 | Boolean cancellation is wired through correctly. Cancellation is checked only at handler entry; generation itself is not interruptible after that checkpoint. |
| Semantic `validate_lesson` before release | Line 111 status gate; line 118 `validate_lesson(output, trusted_reviewers=())`; return at line 119; validation failure re-raised at line 121 | Validation occurs after runtime success and before any return/print. Empty trusted reviewers are passed. Signature/trust semantics of `validate_lesson` are **unverified** in this bounded scope. |
| JSON stdout / errors stderr | Success JSON printed only at line 168; `ValueError` to stderr at line 172; unexpected errors to stderr at line 179; exit 1 at 173/180 | Success path emits JSON on stdout; expected and unexpected failures go to stderr with non-zero exit. Argparse errors use argparse's standard stderr/exit behavior. |

## Actionable findings (low severity)

1. **Default selector bypasses the exact-ID guard** — lines 32–33 and 84 hard-code `"nasalisation-1"` when no selector is supplied. The guard at lines 55–65 validates explicit inputs only, so a missing/renamed default fixture fails later in generation instead of being rejected by the same selector validation. **Action:** resolve the default from the fixture set once, or validate the default through the same membership check.

2. **Constant request ID** — line 91 uses `"request_id": "export-runtime-lesson"` for every export. If the runtime uses request IDs for idempotency, deduplication, or audit correlation, repeated exports in one process/session can collide. **Action:** generate a unique request ID per invocation.

3. **Private fixture accessor dependency** — line 61 calls `lessons._fixtures()`. This couples the public exporter and selector guard to a private API; a signature or return-shape change can break validation. **Action:** use a public fixture accessor if one exists, or isolate the private call behind a small adapter with an explicit contract check.

4. **Hard-coded request permissions under `--no-grants`** — line 99 always declares `["local.generate"]` while line 157 can pass `granted_permissions=()`. If request permissions are treated as authority rather than merely requested scope, the no-grants denial path is ambiguous; even if treated as request-only, audit output can mislead. **Action:** derive the request permission list from `granted_permissions`, or document explicitly that permissions are request-only.

## Non-blocking limitations observed

- Cancellation is checked only at `context.checkpoint()` before generation (line 24), so a cancellation signal arriving during `generate_lesson` is not observed until the handler returns.
- `errors` is assumed to be an iterable of strings at line 112. A string error payload would be joined character-by-character.
- Validation catches only `ValueError` (line 120); other validation exceptions fall through to the generic stderr handler.
- The runtime status string is assumed to be exactly `"ready"` (line 111); the contract was not verified.

## Limitations of this review

- **No tests were executed.** No bash is available, and no test execution was performed or claimed. The controller's reported five acceptance-test passes were **not verified** here; this review is source-based.
- No imports or runtime behavior checks were performed. `generate_lesson`, `execute_capability_request`, `validate_lesson`, and `lessons._fixtures()` contracts are assumed from call sites, not verified.
- This is **not full P03 approval**. It is a bounded, single-file review only.
- No production code, existing tests, or other files were edited. No Lichen changes, downloads, spending, paid fallback, commits, publication, or delegation occurred.
- Export implementation ownership remains with Qwen in the other worktree; this report does not modify or overlap that implementation.

## Commands and assumptions

- Commands run for this review: **none** (bash unavailable). The source was inspected via a single file read; this report was written via the file-write tool.
- Assumptions: `lessons._fixtures()` returns an iterable of mappings containing `lesson_id`; `execute_capability_request(...)` returns a mapping with `status`, optional `errors`, and `output`; `validate_lesson(output, trusted_reviewers=...)` accepts an iterable of trusted reviewers; the handler context exposes `checkpoint()`.

## Controller triage and verification

All126 tests passed in the final offline sandbox snapshot (export-final-full-0603-tests.json), including5 controller acceptance tests. The request permission list is requested scope, never authority; do not derive it from grants to hide denial. Runtime independently checks supervisor grants and checkpoints again after handler return, so the source-only cancellation limitation is cooperative latency, not release of cancelled output. Runtime currently has no idempotency store; constant request ID is a future audit/integration concern. Default-ID drift/private accessor coupling remain maintenance follow-ups. No current fixture drift or idempotency collision reproduced.

Authorship: Qwen wrote adapter, tests and initial docs; controller corrected malformed-output test selector/assertion, no-call assertions, actual subprocess cwd and false documentation claims; controller authored separate acceptance tests and stripped whitespace. Final source review preceded whitespace-only adapter normalization. No production semantics changed after review.
