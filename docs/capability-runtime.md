# Capability Runtime Validation

This module implements structural validation, deadline checks, 
permission validation, and output schema validation for capability requests.

## Key Features

1. **Immediate Structural Schema Validation**: All capability requests are validated against the JSON schema immediately before any semantic field validation occurs.

2. **Malformed Request Handling**: Requests with malformed structures (arrays, numbers, etc.) return non-empty error lists without exceptions.

3. **Capability/Output Schema Binding**: Validates that capabilities support their specified output schemas.

4. **Reserved Contract Validation**: Checks that reserved contracts have actual schema files available.

5. **Zero-Cost Policy Enforcement**: Ensures all policies have `max_cost_usd = 0` and `allow_network = false`.

## Permission Handling

The `get_granted_permissions()` function implements a secure permission model:

- **No Implicit Granting**: Permissions are never automatically granted based on request content
- **Explicit Supervisor Grants**: Only permissions explicitly granted by supervisor are returned
- **Request Field Isolation**: No request field can establish authority or override supervisor grants
- **Input Validation**: Malformed permissions fields raise `ValueError`
- **Intersection Logic**: Returns only permissions that are both requested and explicitly granted

## Validation Order

1. **Structural validation** using JSON Schema - returns immediately on failure
2. **Deadline validation** (must be in the future)
3. **Capability validation** (must be in registry)
4. **Output schema validation**
5. **Permission validation** (must be in registry and explicitly granted)
6. **Policy validation** (zero-cost, no network access)
7. **Capability/output_schema binding validation**
8. **Reserved contracts validation** - check if actual schema files exist

## Error Handling

- All validation errors are returned as a list of strings
- Empty list indicates valid request
- Malformed requests return non-empty error lists without exceptions
- Structural schema errors are returned immediately before semantic field use

## Current limitations

This module validates requests; it is not an execution runtime. Checking policy fields does not itself isolate network access or enforce spending during execution. `get_granted_permissions` defaults to no authority and intersects requested permissions with an independently supplied supervisor collection; malformed grants raise ValueError. Validation itself does not require those grants or execute anything. Handler execution, cancellation, bounded retries/timeouts and validation of actual handler results remain unfinished. Integration examples are validation-only previews: reserved contracts return blocked, executed=false and errors, with no fabricated result. P03 is not accepted; dependent packets remain gated.

Qwen authored the request validation and independent-grants changes. Controller added malformed-authority/deadline regressions, hardened those helpers and corrected the misleading integration examples.
