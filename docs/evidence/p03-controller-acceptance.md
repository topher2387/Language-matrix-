# P03 controller acceptance — 2026-10-20

Verdict: **PASS for P03's strict capability runtime and approved mocked multi-speaker acceptance scope.** No merge or deployment is authorized by this verdict. P04/P05 are not launched.

Reviewed integration commit: `1e2332c6ac606f11b1c1a914f739038b852291d1` (PR #25). Its executable runtime is inherited from `04a73fec7bb9fce72d5385ba0ca96883b1d659fa`; this commit strengthens the fail-closed assertions. Subsequent evidence-only commits do not change that source pin.

## Corrections to Qwen80's draft

The worker draft is preserved verbatim at `../qwen80-p03-review.md` for model evaluation. It is superseded by this controller verdict. Its missing-file observation is true, but its recommendation to create and activate three contracts is not a P03 acceptance requirement: issue #4 requires strict whitelist/refusal semantics and a mocked multi-speaker flow. Unapproved phonology, transcription and image contracts intentionally fail closed. Creating them would introduce unreviewed contract decisions.

The draft incorrectly claims `tests/test_p03_qwen80_regressions.py` was created: no such file exists. Its claim that `test_valid_output_validation` fails is false: the old test only asserted a list was returned. The controller replaced that weak assertion with explicit unavailable-contract rejection, and strengthened the reserved-contract test to cover all three capabilities, zero handler calls/attempts, failure status and no released output. Several worker test names and source line references were inaccurate; the actual test files and fresh logs below govern acceptance.

## Acceptance matrix

| Gate | Verdict | Independently observed evidence |
|---|---|---|
| Versioned request, rationale, input, schema, limits, permissions, UTC deadline | PASS | `tests/test_contracts.py`, `tests/test_capabilities.py`: malformed/null/type/unknown capability/policy/schema-binding refusals |
| Independent permission grants and fixed local handler dispatch | PASS | `tests/test_execution_lifecycle.py`: no-grant, required-permission and unknown-provider/handler tests; requests cannot grant their own authority |
| Cancellation, deadlines, timeout, bounded retry budget | PASS | Lifecycle tests cover pre-cancel, mid-handler cancel, late output, validation time, finite/monotonic clock checks, max attempts and handler mutation |
| Validated detached output and failure handling | PASS | Invalid output never becomes ready; JSON hooks/nonfinite/aliased data boundaries and request snapshots tested |
| Registry hardening | PASS | Discovery mutation does not alter binding authority; incompatible capability/schema rejected |
| Schema reference hardening | PASS | `tests/test_schema_loading_qa.py`: real external references refused, local fragments accepted, literal data/property names preserved, schema-bearing keywords guarded |
| Approved mocked multi-speaker audio | PASS | Two distinct voices each pending→ready; permission/cancel/output-failure matrix below |
| Unapproved phonology/transcript/image execution | PASS (refused) | All three unavailable contracts rejected before handler invocation; not activated |
| Human approval provenance | PASS (limited) | `audio-schema-human-approval-20261020.json`: exact audio draft5740000 approved only for mocked-local metadata; byte identity tested |
| Real speech, licensing/consent, pronunciation/linguistic accuracy | NOT DEMONSTRATED / separately gated | Mocks produce metadata, no audio bytes or teaching-trust upgrade. These are not claimed as P03 mock acceptance |

No reproduced remaining defect blocks the issue #4 P03 mock-runtime acceptance criteria. This is a trusted, cooperative synchronous handler runtime, not a process sandbox: it discards late results but cannot forcibly kill a handler that never returns/checkpoints. Untrusted arbitrary programs and real providers require their own isolation and contract review.

## Exact validation commands and results

At clean tracked source pin `1e2332c6ac606f11b1c1a914f739038b852291d1`:

```sh
python3 /home/topher/Language-matrix-/.dev-harness/test-added-snapshot.py p03-acceptance-pinned-final
```

The helper snapshots tracked current files (config excluded) and executes `python3 -B -m unittest discover -s tests -v` in a network-disabled bubblewrap capsule. Return code0,159 tests PASS; no timeout/output truncation; process group exited. Exact full output: `p03-controller-acceptance/p03-acceptance-pinned-final.json`. Baseline before test changes:159 PASS in3.730s; strengthened working snapshot:159 PASS in3.518s. The pinned final log records its own measured duration.

The additional offline mock matrix ran `python3 -B tools/mock_audio_runtime.py` and the same command with `--no-grants`, `--cancelled`, `--invalid-output` in a capsule. Its exact orchestrating command is preserved in `mock-matrix-command.txt`; assertions verified JSON output, expected CLI exit codes and provider call counts. The matrix driver returned0:

| Flag | CLI exit | Both voice states | Provider calls | Output release |
|---|---:|---|---:|---|
| none | 0 | pending→ready | 2 | Valid mock metadata only |
| `--no-grants` | 1 | failure | 0 | none |
| `--cancelled` | 1 | pending→failure | 0 | none |
| `--invalid-output` | 1 | pending→failure | 2 | none |

## Benchmark handoff

The exact accepted integration starting point for P04/P05 is `1e2332c6ac606f11b1c1a914f739038b852291d1`. Resolve this commit explicitly into an isolated benchmark checkout; do not use older PR #23 head398d56e. P04/P05 scheduling still requires authorization and their own prerequisites; neither is started here. The North-vs-Qwen model comparison is a separately authorized later benchmark, not a claim that P04/P05 already ran.

Authorship: Qwen80 authored its draft report; the controller independently reviewed it, strengthened tests, ran validation, authored this acceptance evidence and published it. No new runtime source changes, paid model calls, quota changes, merges, deployment or Lichen modifications were performed.
