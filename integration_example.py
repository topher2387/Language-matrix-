"""Offline validation previews, not capability execution or P03 acceptance."""
import json
from datetime import datetime, timedelta, timezone
from language_matrix.capabilities import validate_capability_request


def _preview(capability, output_schema, request_id):
    request = {
        "schema_version": "1.0", "request_id": request_id,
        "capability": capability, "provider": "local",
        "input": {"text": "안녕하세요.", "language": "ko"},
        "policy": {"max_cost_usd": 0, "allow_network": False,
                   "max_attempts": 1, "timeout_seconds": 30},
        "rationale": "Preview validation without invoking a handler",
        "output_schema": output_schema, "permissions": ["cache.read"],
        "deadline_utc": (datetime.now(timezone.utc) + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    errors = validate_capability_request(request)
    return {"request_id": request_id, "capability": capability,
            "output_schema": output_schema, "status": "blocked",
            "executed": False, "errors": errors or ["Execution runtime unavailable"]}


def example_worker_integration():
    return _preview("phonology.check", "phonology-report.v1", "example-request-123")


def example_batch_processing():
    return [_preview("phonology.check", "phonology-report.v1", "batch-request-1"),
            _preview("tts.synthesize", "audio-asset.v1", "batch-request-2")]


if __name__ == "__main__":
    print(json.dumps(example_batch_processing(), ensure_ascii=False, indent=2))
