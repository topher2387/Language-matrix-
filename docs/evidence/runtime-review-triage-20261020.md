# Runtime review checkpoint and controller triage

Scope: integration commit `6fcff85`, capability runtime and fixture example. This is not full P03 acceptance, schema approval, a merge authorization or teaching/audio approval.

The independent zero-cost worker inspected source but reached its 12-step limit before writing its assigned report. It ran no tests. Its returned prose is preserved below as candidate observations, not an accepted review verdict. Transport metadata reported returncode 0, paid_cost 0 and usage_unknown false; those fields do not establish task completion.

Controller source inspection confirmed mutable permission/output-schema registries, schema loading without the fixture CLI's external-reference rejection, and a live-object helper permission validator. None demonstrates a request-controlled exploit under the existing trusted local-handler/contract boundary. Treat these as pending hardening candidates. External-reference resolution is a conditional risk if trusted on-disk schemas are altered; no network access was exercised to test it. Review against the supported jsonschema version before changing behavior.

The runtime structurally validates output; lesson semantic/trust validation remains a consumer obligation. The export adapter must call `validate_lesson` before release. The example intentionally returns a fixed fixture; the new export assignment must invoke the actual generator and honor its selector. Controller acceptance tests already detected that the first adapter did neither; publication is withheld pending correction.

No reviewer approval is inferred from missing findings or step-limit termination. Whole-runtime acceptance remains pending.

## Worker self-report, unverified candidate findings

Maximum steps for this agent were reached before I could write the owned evidence file. I made no code or test edits, ran no tests, and made no claims of P03 approval, audio acceptance, or sandbox isolation.

Work completed:
- Inspected `language_matrix/capabilities.py`, `integration_example.py`, the capability/lesson contracts, and related tests (`test_capabilities.py`, `test_execution_lifecycle.py`, `test_runtime_worker_qa.py`, `test_component_bridge_qa.py`, `test_integration.py`).
- Candidate findings for the evidence file:
  - Low, `language_matrix/capabilities.py:28` and `:35`: `PERMISSION_REGISTRY` and `OUTPUT_SCHEMA_REGISTRY` remain mutable globals while `CAPABILITY_REGISTRY` is an immutable proxy. This is inconsistent with “fixed” registry authority, but is not request-controlled and has no demonstrated current exploit.
  - Low/medium, `language_matrix/capabilities.py:494-499` and `:525-546`: schema loading does not reject non-fragment `$ref`, unlike `tools/validate_fixture.py:34-56`. With `jsonschema==4.10.3`, an altered contract schema containing an external `$ref` could trigger remote/file resolution. Current schemas contain no `$ref`, so no current exploit is claimed.
  - Low, `language_matrix/capabilities.py:568-608`: `get_granted_permissions` validates a live request object rather than a plain-JSON snapshot and does not reject duplicate supervisor grants. A custom dict/list subclass could theoretically change its iterated contents between validation and return. It is not used by `execute_capability_request`, so this is a hardening gap, not a demonstrated execution bypass.
  - Limitation, `language_matrix/capabilities.py:475`: execution only calls structural output-schema validation, not `validate_lesson`. A schema-valid but semantically invalid/untrusted lesson can be returned as `ready`. This is documented as structural-only behavior, so it should be recorded as a consumer obligation/limitation rather than a P03 defect.
  - Limitation, `integration_example.py:46-48`: `_lesson_handler` ignores request input and returns the sample lesson. It is explicitly fixture-only, so this is not a production integration claim.

Remaining task:
- Write `docs/evidence/runtime-independent-review-20261020.md` with the findings, exact line references, exploit/impact caveats, explicit limitations, and a statement that no commands/tests were executed.

Recommendation: the next agent should open the owned evidence file, finalize the above as review findings or an explicit “no actionable findings” conclusion where appropriate, and avoid production/test edits or acceptance claims.
