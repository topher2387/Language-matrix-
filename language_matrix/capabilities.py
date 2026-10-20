"""
Capability request validation and execution runtime for P03.

This module implements structural validation, deadline checks,
permission validation, and output schema validation for capability requests.
"""
import json
import math
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Callable, Dict, List, Tuple
from jsonschema import Draft202012Validator
from pathlib import Path

# Registry of supported capabilities and their output schemas
CAPABILITY_REGISTRY = MappingProxyType({
    "lesson.generate": ("lesson.v1",),
    "phonology.check": ("phonology-report.v1",),
    "tts.synthesize": ("audio-asset.v1",),
    "asr.transcribe": ("transcript.v1",),
    "image.generate": ("image-asset.v1",)
})

# Registry of supported permissions
PERMISSION_REGISTRY = {
    "cache.read",
    "cache.write",
    "local.generate"
}

# Output schema registry (only lesson.v1 is currently defined)
OUTPUT_SCHEMA_REGISTRY = {
    "lesson.v1": "lesson-v1.schema.json",
    "phonology-report.v1": "phonology-report-v1.schema.json",
    "audio-asset.v1": "audio-asset-v1.schema.json",
    "transcript.v1": "transcript-v1.schema.json",
    "image-asset.v1": "image-asset-v1.schema.json"
}

# Schema validator for capability requests
CAPABILITY_REQUEST_SCHEMA = None
SCHEMA_ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'contracts'


@dataclass(frozen=True)
class HandlerSpec:
    """Supervisor-owned description of a trusted local handler."""

    handler: Callable[..., Any]
    required_permissions: Tuple[str, ...] = ()


class _CooperativeStop(BaseException):
    """Internal stop signal that ordinary ``except Exception`` cannot swallow."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


_JSON_MAX_DEPTH = 64
_JSON_MAX_NODES = 100000


def _json_snapshot(value: Any) -> Any:
    """Copy plain JSON data without invoking copy/serialization hooks."""
    return _json_snapshot_value(value, 0, [0], set())


def _json_snapshot_value(value: Any, depth: int, nodes: List[int], active: set) -> Any:
    nodes[0] += 1
    if nodes[0] > _JSON_MAX_NODES:
        raise ValueError("JSON value exceeds node limit")
    if depth > _JSON_MAX_DEPTH:
        raise ValueError("JSON value exceeds nesting depth limit")

    if value is None or type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is int:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("JSON number must be finite")
        return value
    if type(value) is list:
        identity = id(value)
        if identity in active:
            raise ValueError("JSON value contains a cycle")
        active.add(identity)
        try:
            return [
                _json_snapshot_value(item, depth + 1, nodes, active)
                for item in value
            ]
        finally:
            active.remove(identity)
    if type(value) is dict:
        identity = id(value)
        if identity in active:
            raise ValueError("JSON value contains a cycle")
        active.add(identity)
        try:
            snapshot = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise ValueError("JSON object keys must be strings")
                snapshot[key] = _json_snapshot_value(item, depth + 1, nodes, active)
            return snapshot
        finally:
            active.remove(identity)

    raise ValueError(f"Unsupported JSON value type: {type(value).__name__}")


def _structural_errors(request: Any) -> List[str]:
    """Return JSON Schema errors, before any semantic field is used."""
    if request is None:
        return ["Request cannot be null"]

    try:
        validator = _get_validator()
        schema_errors = list(validator.iter_errors(request))
    except Exception as exc:
        return [f"Schema validation failed: {str(exc)}"]

    return [f"Schema validation failed: {error.message}" for error in schema_errors]


def _semantic_errors(request: Dict[str, Any], now: datetime) -> List[str]:
    """Validate semantic fields of a structurally valid request."""
    errors = []

    # 1. Deadline validation (must be in the future)
    if "deadline_utc" in request:
        try:
            deadline = datetime.strptime(request["deadline_utc"], "%Y-%m-%dT%H:%M:%SZ")
            deadline = deadline.replace(tzinfo=timezone.utc)
            if deadline <= now:
                errors.append("Deadline has expired")
        except (ValueError, TypeError):
            errors.append("Invalid deadline format")

    # 2. Capability validation (must be in registry)
    if "capability" in request:
        capability = request["capability"]
        if not isinstance(capability, str):
            errors.append("Capability must be a string")
        elif capability not in CAPABILITY_REGISTRY:
            errors.append(f"Unknown capability: {capability}")

    # 3. Output schema validation
    if "output_schema" in request:
        output_schema = request["output_schema"]
        if not isinstance(output_schema, str):
            errors.append("Output schema must be a string")
        elif output_schema not in OUTPUT_SCHEMA_REGISTRY:
            errors.append(f"Unknown output schema: {output_schema}")

    # 4. Permission validation (must be in registry)
    if "permissions" in request:
        permissions = request["permissions"]
        if not isinstance(permissions, list):
            errors.append("Permissions must be an array")
        else:
            for perm in permissions:
                if not isinstance(perm, str) or perm not in PERMISSION_REGISTRY:
                    errors.append(f"Unknown permission: {perm}")

    # 5. Policy validation
    if "policy" in request:
        policy = request["policy"]
        if not isinstance(policy, dict):
            errors.append("Policy must be an object")
        else:
            if "max_cost_usd" in policy and policy["max_cost_usd"] != 0:
                errors.append("Policy must have max_cost_usd = 0")
            if "allow_network" in policy and policy["allow_network"] is not False:
                errors.append("Policy must have allow_network = false")

    # 6. Capability/output_schema binding validation
    if "capability" in request and "output_schema" in request:
        capability = request["capability"]
        output_schema = request["output_schema"]
        if capability in CAPABILITY_REGISTRY:
            supported_schemas = CAPABILITY_REGISTRY[capability]
            if output_schema not in supported_schemas:
                errors.append(
                    f"Capability {capability} does not support output schema {output_schema}"
                )

    # 7. Reserved contracts validation - check if actual schema files exist
    if "output_schema" in request:
        output_schema = request["output_schema"]
        if output_schema in OUTPUT_SCHEMA_REGISTRY:
            try:
                schema_file = OUTPUT_SCHEMA_REGISTRY[output_schema]
                schema_path = SCHEMA_ROOT / schema_file
                if not schema_path.exists():
                    errors.append(
                        f"Output schema file not found for {output_schema}: {schema_file}"
                    )
            except Exception:
                errors.append(f"Failed to validate schema file for {output_schema}")

    return errors


def _default_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _default_monotonic() -> float:
    return time.monotonic()


def _aware_utc(value: Any) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("Clock must return a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Clock must return a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def _monotonic_value(value: Any) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Monotonic clock must return a finite number")
    return value


def _failure(states: List[str], attempts: int, errors: List[str]) -> Dict[str, Any]:
    states.append("failure")
    return {
        "status": "failure",
        "states": states,
        "attempts": attempts,
        "errors": errors,
    }


def _normalize_permission_names(value: Any) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(
        value, (list, tuple, set, frozenset)
    ):
        raise ValueError("Permissions must be a collection of permission names")
    names = tuple(value)
    if not all(isinstance(name, str) and name in PERMISSION_REGISTRY for name in names):
        raise ValueError("Invalid permission names")
    if len(set(names)) != len(names):
        raise ValueError("Duplicate permission names")
    return names


class _ExecutionContext:
    """Cooperative checkpointing context passed to a trusted handler."""

    def __init__(
        self,
        *,
        deadline: datetime,
        started_monotonic: float,
        timeout_seconds: float,
        utc_now: Callable[[], datetime],
        monotonic: Callable[[], float],
        cancelled: Callable[[], bool],
    ):
        self._deadline = deadline
        self._started_monotonic = started_monotonic
        self._last_monotonic = started_monotonic
        self._timeout_seconds = timeout_seconds
        self._utc_now = utc_now
        self._monotonic = monotonic
        self._cancelled = cancelled

    def _stop_reason(self) -> str:
        try:
            if bool(self._cancelled()):
                return "Execution was cancelled"
        except Exception as exc:
            return f"Cancellation check failed: {exc}"

        try:
            if _aware_utc(self._utc_now()) >= self._deadline:
                return "Deadline has expired"
        except Exception as exc:
            return f"Deadline check failed: {exc}"

        try:
            current = _monotonic_value(self._monotonic())
            if current < self._last_monotonic:
                return "Monotonic clock moved backwards"
            self._last_monotonic = current
            elapsed = current - self._started_monotonic
            if elapsed >= self._timeout_seconds:
                return "Execution time budget exhausted"
        except Exception as exc:
            return f"Time budget check failed: {exc}"

        return ""

    def checkpoint(self) -> None:
        reason = self._stop_reason()
        if reason:
            raise _CooperativeStop(reason)


def execute_capability_request(
    request: Dict[str, Any],
    *,
    handlers: Mapping[Tuple[str, str], HandlerSpec],
    granted_permissions: Tuple[str, ...] = (),
    utc_now: Callable[[], datetime] = None,
    monotonic: Callable[[], float] = None,
    cancelled: Callable[[], bool] = None,
) -> Dict[str, Any]:
    """
    Execute a validated capability request with a trusted local handler.

    Execution is synchronous and cooperative. It does not create threads or
    processes, and it cannot preempt or isolate handler code.
    """
    utc_now = _default_utc_now if utc_now is None else utc_now
    monotonic = _default_monotonic if monotonic is None else monotonic
    cancelled = (lambda: False) if cancelled is None else cancelled

    states: List[str] = []

    # Snapshot plain JSON first, then schema-validate the detached snapshot.
    # No request field selects a handler and no copy hook is ever invoked.
    try:
        request_snapshot = _json_snapshot(request)
    except ValueError as exc:
        return _failure(states, 0, [f"Request is not plain JSON: {exc}"])

    structural = _structural_errors(request_snapshot)
    if structural:
        return _failure(states, 0, structural)

    if not (
        callable(utc_now) and callable(monotonic) and callable(cancelled)
    ):
        return _failure(states, 0, ["Invalid execution clock or cancellation callable"])

    try:
        grants = _normalize_permission_names(granted_permissions)
    except ValueError as exc:
        return _failure(states, 0, [str(exc)])

    try:
        now = _aware_utc(utc_now())
    except Exception as exc:
        return _failure(states, 0, [f"Invalid UTC clock: {exc}"])

    semantic = _semantic_errors(request_snapshot, now)
    if semantic:
        return _failure(states, 0, semantic)

    provider = request_snapshot["provider"]
    capability = request_snapshot["capability"]
    output_schema = request_snapshot["output_schema"]
    requested = tuple(request_snapshot["permissions"])
    deadline_text = request_snapshot["deadline_utc"]
    max_attempts = request_snapshot["policy"]["max_attempts"]
    timeout_seconds = request_snapshot["policy"]["timeout_seconds"]

    if provider != "local":
        return _failure(states, 0, [f"Provider is not allowed: {provider}"])

    if not isinstance(handlers, Mapping):
        return _failure(states, 0, ["Handler registry must be a mapping"])

    try:
        spec = handlers.get((provider, capability))
    except Exception as exc:
        return _failure(states, 0, [f"Handler lookup failed: {exc}"])

    if not isinstance(spec, HandlerSpec):
        return _failure(states, 0, [f"No trusted handler for {provider}/{capability}"])

    if not callable(spec.handler):
        return _failure(states, 0, ["Handler spec is not callable"])

    try:
        required = _normalize_permission_names(spec.required_permissions)
    except ValueError as exc:
        return _failure(states, 0, [f"Malformed handler spec: {exc}"])

    granted_set = set(grants)
    requested_set = set(requested)

    missing_grants = [name for name in requested if name not in granted_set]
    if missing_grants:
        return _failure(
            states,
            0,
            [f"Requested permission not granted: {name}" for name in missing_grants],
        )

    for name in required:
        if name not in requested_set:
            return _failure(
                states, 0, [f"Handler-required permission not requested: {name}"]
            )
        if name not in granted_set:
            return _failure(
                states, 0, [f"Handler-required permission not granted: {name}"]
            )

    try:
        deadline = datetime.strptime(deadline_text, "%Y-%m-%dT%H:%M:%SZ")
        deadline = deadline.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return _failure(states, 0, ["Invalid deadline format"])

    if now >= deadline:
        return _failure(states, 0, ["Deadline has expired"])

    try:
        started_monotonic = _monotonic_value(monotonic())
    except Exception as exc:
        return _failure(states, 0, [f"Invalid monotonic clock: {exc}"])

    context = _ExecutionContext(
        deadline=deadline,
        started_monotonic=started_monotonic,
        timeout_seconds=timeout_seconds,
        utc_now=utc_now,
        monotonic=monotonic,
        cancelled=cancelled,
    )

    states.append("pending")
    attempts = 0
    last_error = "Handler failed"

    while attempts < max_attempts:
        try:
            context.checkpoint()
        except _CooperativeStop as stop:
            return _failure(states, attempts, [stop.reason])

        attempts += 1
        try:
            attempt_request = _json_snapshot(request_snapshot)
        except ValueError as exc:
            return _failure(states, attempts, [f"Request cannot be snapshotted: {exc}"])
        try:
            output = spec.handler(attempt_request, context)
        except _CooperativeStop as stop:
            return _failure(states, attempts, [stop.reason])
        except Exception as exc:
            last_error = f"Handler failed: {exc}"
            try:
                context.checkpoint()
            except _CooperativeStop as stop:
                return _failure(states, attempts, [stop.reason])
            if attempts >= max_attempts:
                return _failure(states, attempts, [last_error])
            continue

        try:
            context.checkpoint()
        except _CooperativeStop as stop:
            return _failure(states, attempts, [stop.reason])

        try:
            result_output = _json_snapshot(output)
        except ValueError as exc:
            return _failure(states, attempts, [f"Handler output is not plain JSON: {exc}"])

        output_errors = validate_output_schema(result_output, output_schema)
        if output_errors:
            return _failure(states, attempts, output_errors)

        try:
            context.checkpoint()
        except _CooperativeStop as stop:
            return _failure(states, attempts, [stop.reason])

        states.append("ready")
        return {
            "status": "ready",
            "states": states,
            "attempts": attempts,
            "output": result_output,
        }

    return _failure(states, attempts, [last_error])

def _load_schema(schema_file: str) -> Dict[str, Any]:
    """Load a JSON schema from the contracts directory."""
    schema_path = SCHEMA_ROOT / schema_file
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file {schema_file} not found")

    # Load the raw schema content first
    raw_schema = json.loads(schema_path.read_text())

    # Recursively walk through the schema to check for external references
    _check_schema_refs(raw_schema)

    return raw_schema


def _check_schema_refs(obj: Any, path: str = "$") -> None:
    """Recursively check schema for external $ref references and reject them."""
    if isinstance(obj, dict):
        # Check for $ref key (only in schema objects)
        if '$ref' in obj:
            ref_value = obj['$ref']
            if not isinstance(ref_value, str):
                raise ValueError(f"Invalid $ref value at {path}: non-string reference")
            # Check if it's an external reference (URL, file path, or relative path)
            if ref_value.startswith(('http://', 'https://')):
                raise ValueError(f"External URL $ref not allowed at {path}: {ref_value}")
            elif ref_value.startswith(('/', './', '../')):
                raise ValueError(f"External file/relative $ref not allowed at {path}: {ref_value}")
            elif not ref_value.startswith('#'):
                # If it doesn't start with #, it's likely an external reference
                raise ValueError(f"External $ref not allowed at {path}: {ref_value}")

        if '$dynamicRef' in obj:
            dynamic_ref_value = obj['$dynamicRef']
            if not isinstance(dynamic_ref_value, str):
                raise ValueError(f"Invalid $dynamicRef value at {path}: non-string reference")
            # Check if it's an external reference (URL, file path, or relative path)
            if dynamic_ref_value.startswith(('http://', 'https://')):
                raise ValueError(f"External URL $dynamicRef not allowed at {path}: {dynamic_ref_value}")
            elif dynamic_ref_value.startswith(('/', './', '../')):
                raise ValueError(f"External file/relative $dynamicRef not allowed at {path}: {dynamic_ref_value}")
            elif not dynamic_ref_value.startswith('#'):
                # If it doesn't start with #, it's likely an external reference
                raise ValueError(f"External $dynamicRef not allowed at {path}: {dynamic_ref_value}")

        # Schema keywords that should be traversed as schemas (not as containers)
        schema_map_keywords = {
            'properties', '$defs', 'definitions', 'patternProperties',
            'dependentSchemas'
        }

        schema_array_keywords = {
            'allOf', 'anyOf', 'oneOf', 'prefixItems'
        }

        schema_single_keywords = {
            'items', 'additionalProperties', 'unevaluatedProperties', 'unevaluatedItems',
            'contains', 'propertyNames', 'not', 'if', 'then', 'else', 'additionalItems',
            'contentSchema'
        }

        # For each key in the object, determine how to traverse it
        for key, value in obj.items():
            if key in schema_map_keywords:
                # These are map keywords that should be traversed as schemas (values are schemas)
                if isinstance(value, dict):
                    for map_key, map_value in value.items():
                        _check_schema_refs(map_value, f"{path}/{key}/{map_key}")
            elif key in schema_array_keywords:
                # These are array keywords that should be traversed as schemas (items are schemas)
                if isinstance(value, list):
                    for i, item in enumerate(value):
                        _check_schema_refs(item, f"{path}/{key}[{i}]")
            elif key in schema_single_keywords:
                # These are single-value keywords that should be traversed as schemas
                _check_schema_refs(value, f"{path}/{key}")
            # Skip annotation/data payload keywords that should not be traversed as schemas
            elif key in {'const', 'enum', 'default', 'examples', 'title', 'description',
                       'deprecated', 'readOnly', 'writeOnly', 'contentMediaType',
                       'contentEncoding', 'format', 'discriminator', 'id', '$id', 'anchor'}:
                # These are annotation/data payload keywords, not schema objects - do nothing
                continue
            else:
                # For unknown keywords, we don't traverse them as schemas
                # This prevents false positives like literal $ref in property names
                pass

    elif isinstance(obj, list):
        # Recursively check list items
        for i, item in enumerate(obj):
            _check_schema_refs(item, f"{path}[{i}]")

def _get_validator() -> Draft202012Validator:
    """Get or create the capability request validator."""
    global CAPABILITY_REQUEST_SCHEMA
    if CAPABILITY_REQUEST_SCHEMA is None:
        schema = _load_schema("capability-request-v1.schema.json")
        CAPABILITY_REQUEST_SCHEMA = Draft202012Validator(schema)
    return CAPABILITY_REQUEST_SCHEMA

def validate_capability_request(request: Dict[str, Any]) -> List[str]:
    """
    Validate a capability request according to P03 requirements.

    Returns list of validation errors. Empty list means valid request.
    """
    try:
        request_snapshot = _json_snapshot(request)
    except ValueError as exc:
        return [f"Request is not plain JSON: {exc}"]

    structural = _structural_errors(request_snapshot)
    if structural:
        return structural
    return _semantic_errors(request_snapshot, datetime.now(timezone.utc))

def validate_output_schema(output: Dict[str, Any], schema_name: str) -> List[str]:
    """
    Validate output against the specified schema.

    Returns list of validation errors. Empty list means valid output.
    """
    errors = []

    if schema_name not in OUTPUT_SCHEMA_REGISTRY:
        return [f"Unknown output schema: {schema_name}"]

    # Load the appropriate schema
    try:
        schema_file = OUTPUT_SCHEMA_REGISTRY[schema_name]
        schema = _load_schema(schema_file)
        validator = Draft202012Validator(schema)
        schema_errors = list(validator.iter_errors(output))

        for error in schema_errors:
            errors.append(f"Output validation failed: {error.message}")
    except Exception as e:
        errors.append(f"Failed to validate output against {schema_name}: {str(e)}")

    return errors

def is_request_expired(request: Dict[str, Any]) -> bool:
    """
    Check if a request has expired based on its deadline.

    Returns True if expired, False otherwise.
    """
    if not isinstance(request, dict) or not isinstance(request.get("deadline_utc"), str):
        return True  # No deadline means expired

    try:
        deadline = datetime.strptime(request["deadline_utc"], "%Y-%m-%dT%H:%M:%SZ")
        # Make the deadline timezone-aware to match current_time
        deadline = deadline.replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        return deadline <= current_time
    except (ValueError, TypeError):
        return True  # Invalid date format is considered expired

def get_granted_permissions(request: Dict[str, Any], *, granted_permissions: List[str] = ()) -> List[str]:
    """
    Get the list of granted permissions for a request.

    For now, this returns only requested permissions that are also explicitly granted
    by supervisor. No request field can establish authority.

    Args:
        request: The capability request dictionary
        granted_permissions: Permissions explicitly granted by supervisor

    Returns:
        List of permissions that are both requested and granted, preserving order from request

    Raises:
        ValueError: If request has malformed permissions field
    """
    if not isinstance(request, dict):
        raise ValueError("Request must be an object")
    if not isinstance(granted_permissions, (list, tuple, set, frozenset)):
        raise ValueError("Supervisor grants must be a collection of permission names")
    if not all(isinstance(p, str) and p in PERMISSION_REGISTRY for p in granted_permissions):
        raise ValueError("Invalid supervisor permission grants")
    # Validate request structure first
    if "permissions" not in request:
        return []

    # Validate that permissions field is a list
    if not isinstance(request["permissions"], list):
        raise ValueError("Malformed permissions field: must be a list")

    # Check for invalid permission names in request
    requested_perms = request["permissions"]

    # Validate that all requested permissions are valid
    if not all(isinstance(p, str) and p in PERMISSION_REGISTRY for p in requested_perms):
        raise ValueError("Malformed permissions field: contains invalid permission names")

    # Return intersection of requested and granted permissions, preserving order from request
    granted_set = set(granted_permissions)
    return [p for p in requested_perms if p in granted_set]

def get_supported_capabilities() -> Dict[str, List[str]]:
    """
    Get the registry of supported capabilities and their output schemas.
    """
    return {capability: list(schemas) for capability, schemas in CAPABILITY_REGISTRY.items()}

def get_supported_permissions() -> set:
    """
    Get the registry of supported permissions.
    """
    return PERMISSION_REGISTRY.copy()
