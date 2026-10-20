# Export Worker Review — 2026-10-20

Scope: `tools/export_runtime_lesson.py` and `tests/test_runtime_export*.py` only.
This is a source review, not runtime approval. Tests were not executed (no bash in this
environment). No source or test files were edited.

## Blocking findings

1. **Generator is imported but never used; export is a fixture copy.**
   `tools/export_runtime_lesson.py:12` imports `generate_lesson`, but
   `export_lesson()` builds a request from `_sample_lesson()` (`:57`, `:63`) and
   `_lesson_handler` returns that fixture directly (`:27-30`). Nothing calls
   `generate_lesson`. This fails acceptance coverage that patches the generator and
   requires exactly one call (`tests/test_runtime_export_acceptance.py:20-23`) and
   makes the exported result a constant `hello-ko` fixture, not a generated lesson
   (`docs/contracts/sample-lesson.json:3`).

2. **The selector is parsed, then discarded.**
   `lesson_input` is accepted at `tools/export_runtime_lesson.py:33` and parsed at
   `:110-117`, but is never validated, resolved, or passed into the request/handler
   (`:50-78`). Consequences:
   - String/int/bool/dict selectors all silently export the same fixture.
   - Unknown selectors succeed, contradicting
     `tests/test_runtime_export_acceptance.py:28-31` and the CLI refusal case at
     `tests/test_runtime_export_acceptance.py:42-46`.
   - Authority-shaped input such as `{"permissions": [...]}` is neither rejected nor
     isolated from trusted request permissions (`:68`).
   - `True` is an `int` subclass; any future selector dispatch must explicitly reject
     booleans and non-resolving values.

3. **Deadline is hard-coded and already boundary-unsafe.**
   `tools/export_runtime_lesson.py:69` fixes `deadline_utc` to
   `"2026-10-20T12:00:00Z"`. The capability layer parses that exact format and enforces
   expiry (`language_matrix/capabilities.py:139-141`, `:556-560`). Any run after that
   instant fails; a run near it can expire between request construction and handler
   execution. The 30s timeout (`:65`) is not derived from the deadline. There is no
   injected clock or test coverage for just-before/just-after expiry.

4. **CLI contract does not match the acceptance contract.**
   `main()` defines only an optional positional `selector`
   (`tools/export_runtime_lesson.py:100-106`). The acceptance tests invoke
   `--lesson-id`, `--no-grants`, `--cancelled`, and `--unknown-argument`
   (`tests/test_runtime_export_acceptance.py:33-49`); argparse will reject the first
   three as unrecognized and exit 2. The tool has no CLI path to exercise the
   permission-denied or cancellation branches, so CLI refusal behavior is untested and
   unimplemented.

5. **Owned tests encode the defects instead of catching them.**
   - `tests/test_runtime_export.py:54-58` expects a malformed selector to succeed.
   - `tests/test_runtime_export.py:126-137` expects an unknown selector to succeed.
   - `tests/test_runtime_export.py:100-124` are named as grant/cancel failures but never
     pass `--no-grants`/`--cancelled`; they assert success.
   - `tests/test_runtime_export.py:35-40` claims selector coverage but only works because
     the fixture itself is `hello-ko`; it would pass with selector handling removed.
   - `tests/test_runtime_export.py:42-46` expects the message
     `"Requested permission not granted"`, while `export_lesson()` rewrites runtime
     failures as `"Lesson generation failed: ..."` (`tools/export_runtime_lesson.py:80-82`);
     the asserted text is not guaranteed by this code path.
   These false-negative tests conflict with the controller acceptance tests and would
   green-light a non-functional selector/generator.

6. **Missing boundary behavior.**
   No coverage or explicit handling for: selector type confusion (`int`, `bool`, JSON
   scalar), oversized/nested selector objects, unknown dict keys, deadline expiry
   during execution, cancellation before the handler checkpoint, or error output being
   empty on refusal. `capabilities.py` deadline parsing accepts only whole-second UTC
   `Z` strings, so arbitrary user-supplied deadline formats are not an alternative.

## Minimal repair checklist

- [ ] Call the real lesson resolver/generator (`generate_lesson` or the selector helper)
      once per export; remove the fixture-returning handler path or make it a test-only
      double. Assert the generated `lesson_id` and `verification.status == "unverified"`
      without weakening validation.
- [ ] Validate and normalize `lesson_input` before request construction: allow only
      supported scalar/dict forms, reject bools, unknown IDs, and authority-shaped keys;
      thread the resolved value into the generator input rather than `_sample_lesson()`.
- [ ] Replace the fixed deadline with a computed UTC deadline derived from an injected
      clock/now plus the bounded timeout (or accept an explicit deadline argument);
      keep `max_attempts` and timeout consistent. Add just-before/just-after expiry
      tests.
- [ ] Implement `--lesson-id`, `--no-grants`, and `--cancelled` (and explicit
      unknown-argument refusal); refusals must exit non-zero, write only stderr, and
      emit no stdout.
- [ ] Rewrite the mislabeled tests to assert the real contract: unknown/invalid selectors
      and malformed payloads raise/exit non-zero; grant/cancel cases actually exercise
      those branches; empty stdout on every refusal; generator is not called before a
      refusal.
- [ ] After repair, run (do not assume passing):
      `python -m pytest tests/test_runtime_export.py tests/test_runtime_export_acceptance.py`
      or the equivalent `python -m unittest` invocation. Treat acceptance failure as
      blocking.

## Assumptions

- Source inspected is the current worktree state as of 2026-10-20; no execution or import
  checks were performed.
- `language_matrix.lessons.generate_lesson` is the intended generator, per the import and
  acceptance test patch target.
- Artifact paths and line numbers refer to this worktree only.

Verdict: **not approved** for runtime/export use until findings 1-5 are repaired and the
acceptance suite is confirmed by the owner with actual execution evidence.

## Controller qualification

Independent offline controller run reproduced8 failing assertions across5 acceptance tests. The grant-message substring test actually passes in the initial implementation; that reviewer observation is not accepted as a reproduced defect. Ignored selector objects do not currently extend trusted grants, so no authority escalation is established. Scope remains None/exact string lesson IDs; broader dict/index selectors are not required. Use python3 unittest, not a new pytest dependency. The test worker exhausted12steps without writing its file and is incomplete; the review worker wrote this report in5steps. Both reported paid_cost0 and knownusage. No acceptance or code publication inferred.
