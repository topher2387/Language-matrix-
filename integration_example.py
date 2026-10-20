"""Offline fixture demonstrations; not teaching verification or P03 acceptance."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from language_matrix.capabilities import (
    HandlerSpec,
    execute_capability_request,
    validate_capability_request,
)

ROOT = Path(__file__).resolve().parent
SAMPLE_LESSON = ROOT / "docs" / "contracts" / "sample-lesson.json"


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


def _sample_lesson():
    return json.loads(SAMPLE_LESSON.read_text(encoding="utf-8"))


def _lesson_handler(request, context):
    context.checkpoint()
    return _sample_lesson()


def _lesson_request():
    lesson = _sample_lesson()
    return {
        "schema_version": "1.0",
        "request_id": "example-lesson-execution",
        "capability": "lesson.generate",
        "provider": "local",
        "input": {"text": lesson["units"][0]["hangul"], "language": "ko"},
        "policy": {"max_cost_usd": 0, "allow_network": False,
                   "max_attempts": 1, "timeout_seconds": 30},
        "rationale": "Fixture-only demonstration of trusted local lesson.v1 execution",
        "output_schema": "lesson.v1",
        "permissions": ["local.generate"],
        "deadline_utc": (datetime.now(timezone.utc) + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def example_lesson_execution(*, granted_permissions=("local.generate",), cancelled=lambda: False):
    handlers = {
        ("local", "lesson.generate"): HandlerSpec(
            _lesson_handler, required_permissions=("local.generate",)
        )
    }
    return execute_capability_request(
        _lesson_request(),
        handlers=handlers,
        granted_permissions=granted_permissions,
        cancelled=cancelled,
    )


if __name__ == "__main__":
    print(json.dumps({
        "kind": "offline-fixture-demo",
        "demo": True,
        "fixture_only": True,
        "note": "Fixture-only demonstration using the unverified sample lesson; "
                "no provider or model was loaded, and no teaching or audio "
                "verification is claimed.",
        "lesson_execution": example_lesson_execution(),
        "previews": example_batch_processing(),
    }, ensure_ascii=False, indent=2))
