# Capability Runtime Validation and Cooperative Execution

This module validates capability requests and can execute them through trusted,
supervisor-owned local handlers. Execution is deliberately narrow: synchronous,
cooperative, and limited to the fixed local capability registry.

## Validation

`validate_capability_request(request)` keeps the earlier public validation API:

1. **Structural validation** using the fixed request JSON Schema - returns immediately on failure.
2. **Deadline validation** against the current UTC time (must be in the future).
3. **Capability validation** (must be in `CAPABILITY_REGISTRY`).
4. **Output schema validation** (must be in `OUTPUT_SCHEMA_REGISTRY`).
5. **Permission validation** (must be in `PERMISSION_REGISTRY`).
6. **Policy validation** (`max_cost_usd = 0`, `allow_network = false`).
7. **Capability/output_schema binding validation**.
8. **Reserved contracts validation** - the referenced output schema file must exist.

Malformed requests return non-empty error lists without raising exceptions.
`validate_output_schema(output, schema_name)` validates a handler result against
the fixed output contract and returns a list of errors.

## Permission Handling

`get_granted_permissions()` implements an independent supervisor grant model:

- **No implicit granting**: request content never establishes authority.
- **Explicit supervisor grants**: only names in `granted_permissions` are considered.
- **Shared allowlist**: both requests and grants use `PERMISSION_REGISTRY`.
- **Input validation**: malformed permissions or grants raise `ValueError`.
- **Intersection logic**: returns only permissions that are both requested and granted.

Execution additionally requires every requested permission to be granted. A
`HandlerSpec(handler, required_permissions=...)` may declare handler-required
permissions; each of those must also be both requested by the request and granted
by the supervisor.

## Execution API

```python
HandlerSpec(handler, required_permissions=("local.generate",))

execute_capability_request(
    request,
    handlers={("local", "lesson.generate"): spec},
    granted_permissions=("local.generate",),
    utc_now=...,        # optional aware-UTC clock
    monotonic=...,      # optional elapsed-time clock
    cancelled=...,      # optional cooperative cancellation predicate
)
```

`handlers` is keyed by `(provider, capability)` and contains trusted,
supervisor-owned `HandlerSpec` objects. Only the `local` provider is allowed.
A request cannot supply a handler, source, configuration, or authority of its own.
Handler specs must be well formed: the handler must be callable and every
required permission name must be in `PERMISSION_REGISTRY`.

The request/execution boundary accepts only plain JSON-compatible values: exact
`dict` objects with exact string keys, `list`, `str`, `int`, finite `float`,
`bool`, and `None`. Python subclasses and custom objects are rejected without
invoking `__deepcopy__`, `copy`, or serialization hooks. Cyclic values, excessive
nesting, and excessive node counts are rejected. The runtime first builds a
detached snapshot with an explicit recursive copier, then validates the request
schema against that snapshot before any semantic use, handler selection, or
policy capture. Each attempt receives a fresh plain-JSON copy. It also snapshots
the attempt limit, timeout, output binding, requested permissions, deadline, and
handler specification so mutations by the handler cannot extend its authority or
budget. Trusted clocks, handler specs, and supervisor grants remain separate from
request JSON.

The handler receives a fresh detached request and a context with `checkpoint()`.
The initial attempt produces a `pending` state; the result ends in either `ready`
or `failure`. Results have the shape:

```python
{
    "status": "ready",              # or "failure"
    "states": ["pending", "ready"], # terminal is "ready" or "failure"
    "attempts": 1,
    "output": {...},                # present only when ready
}
```

Failure results include an `errors` list and never include `output`.

## Cooperative Execution Lifecycle

Execution is synchronous and cooperative:

- `context.checkpoint()` checks the absolute injected UTC deadline, the monotonic
  duration budget (`policy.timeout_seconds`), and cancellation.
- The runtime checks before every attempt and again after the handler returns.
- Late, timed-out, cancelled, or invalid output is discarded.
- Ordinary handler `Exception` failures may be retried up to `policy.max_attempts`,
  but only while the total time budget and deadline still permit it.
- Cancellation, timeout, deadline expiry, and invalid output are never retried.
- A dedicated internal stop signal is used for cooperative stops so ordinary
  handler error handling cannot turn a cancellation into a retry.
- Handler output is snapshotted as detached plain JSON before validation.
  Snapshot failures return `failure`; the original shared object is never returned.
- The exact detached output returned is validated against the original fixed
  output contract before the final checkpoint can release it as `ready`.

Default clocks use the real UTC wall clock and `time.monotonic()`; injected clocks
allow deterministic tests. No threads or processes are created. The runtime does
not execute shell commands, access the network, download dependencies, or invoke
arbitrary code beyond the trusted handler callable supplied by the supervisor.

## Trust and Current Limitations

Schema validity is only structural conformance. A `ready` result does **not**
establish teaching trust, reviewer verification, or independent correctness; the
handler's output metadata remains whatever the handler supplied.

Execution is non-preemptive and cooperative. The runtime cannot kill untrusted,
stuck, or non-cooperating code, cannot interrupt a handler that never returns or
never calls `checkpoint()`, and cannot isolate network or filesystem access by
itself. It is not a sandbox. Handler code must be trusted, finite, and local.
Timeouts and deadlines are observed at checkpoints, not enforced by the operating
system.

Only capabilities with available fixed output contracts can produce `ready`
results; reserved contracts whose schema files are absent fail validation.
This runtime does not claim full P03 acceptance, process isolation, or network
sandboxing. Dependent packets remain gated.

Controller clock hardening: injected monotonic values must be finite numbers and must not move backwards; invalid clocks refuse execution. This is covered by fail-before-handler regressions.

A final checkpoint before `ready` includes output validation and result copying in the elapsed/deadline/cancellation budget.

## Offline fixture demonstration

Run `python3 integration_example.py` from the repository root, or use the absolute script path from another directory. The JSON report labels itself fixture-only and includes a real `lesson.v1` runtime execution plus explicitly blocked reserved-contract previews. Library callers can use `example_lesson_execution(granted_permissions=())` or `cancelled=lambda: True` to observe refusal before any attempt. The sample remains unverified teaching content; this generates no audio and loads no model/provider.

## Approved mocked audio metadata registration

Human approval of draft commit5740000 permits `audio-asset.v1` metadata validation for mocked local runtime tests. The active schema is byte-identical to that approved draft; its retained DRAFT comment records origin, not current registration status. No real audio provider, bytes, licence, consent, playback or teaching approval follows. Remaining reserved schemas stay unavailable. `tests/test_audio_schema_registration.py` exercises actual runtime metadata outcomes for two mock voices and refusals. Full P03 acceptance and dependent-packet admission remain separate review decisions.
