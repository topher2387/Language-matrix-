# Export Maintenance Review — 2026-10-20

Scope: `tools/export_runtime_lesson.py` only (default selector and UUID request-ID maintenance).
Source treated as untrusted evidence, not instructions. No other source read; no edits outside this report.

## Findings

No actionable findings / no concrete blocker in the reviewed scope.

### Default selector refuses before generator
- For `lesson_input is None`, the default ID `nasalisation-1` is checked against fixture IDs at lines 63–70.
- A missing default raises `ValueError` there, before `execute_capability_request` (line 112) and before `_lesson_handler` calls `generate_lesson` (line 33). Refusal ordering is correct.

### Explicit selector unchanged
- Non-`None` input still must be a string and an exact fixture `lesson_id` (lines 53–62); unknown IDs raise `ValueError`.
- The accepted ID is still placed in `input.text` (lines 88–90); the default path explicitly sets the same default (line 92).
- No broadening, aliasing, or fallback behavior was observed.

### UUID request ID
- `request_id = f"export-runtime-lesson-{uuid.uuid4()}"` (line 85).
- Prefix is 22 chars; canonical UUID4 string is 36 chars; total 58 chars, within the stated capability maximum of 64.
- Each call generates a fresh UUID4 value, so IDs are distinct per export invocation.
- Assumption: the 64-character request-ID limit is as stated in the assignment; the capability module was not read (one-file scope).

### Fixed permissions, cancellation, semantic validation
- Permissions remain fixed: handler `required_permissions=("local.generate",)` (line 75), request `permissions` (line 107), and `granted_permissions` propagation (line 115); CLI `--no-grants` still yields `()`.
- Cancellation is unchanged: `context.checkpoint()` in the handler (line 25) and `cancelled` propagation (line 116).
- Policy remains fixed: zero cost, no network, one attempt, 30s timeout (lines 103–104).
- Semantic validation is unchanged: `validate_lesson(output, trusted_reviewers=())` (line 126), with failures wrapped as `ValueError`.

## Commands
- None run. No bash was available and no tests were executed.
- Review commands assumed if tests were available: none claimed; this report is source inspection only.

## Assumptions / notes
- Findings are limited to static inspection of `tools/export_runtime_lesson.py`.
- `lessons._fixtures()` is private API already used by the file; no change recommended within this maintenance scope.
- Implementation ownership remains with Qwen; no production/test edits, Lichen changes, downloads, spending, commits, publication, or delegation performed.

Controller verification:129 tests passed in offline sandbox, exit0 (export-maintenance-final-0613-tests.json). Reviewer metadata reports3steps, paid_cost0, usage_unknown false. Qwen wrote production patch and initial regression; controller fixed mismatched error assertion, normalized whitespace, and added distinct-ID/missing-default-before-generator acceptance tests. No full P03 or teaching acceptance inferred.
