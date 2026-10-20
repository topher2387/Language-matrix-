"""Provider-neutral lesson generation with structural and semantic validation."""
from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from pathlib import Path

from jsonschema import Draft202012Validator

_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _ROOT / "docs" / "contracts" / "lesson-v1.schema.json"
_FIXTURES_PATH = _ROOT / "fixtures" / "lessons.json"
_VALIDATOR = None
_FIXTURES = None

AUDIO_WIDGET_TYPES = {"teaching_unit", "comparison", "audio"}


def _validator():
    global _VALIDATOR
    if _VALIDATOR is None:
        schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        _VALIDATOR = Draft202012Validator(schema)
    return _VALIDATOR


def _fixtures():
    global _FIXTURES
    if _FIXTURES is None:
        data = json.loads(_FIXTURES_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not data:
            raise ValueError("fixture file must contain a non-empty array of lessons")
        _FIXTURES = data
    return _FIXTURES


def _request(value):
    if value is None:
        return {}
    if isinstance(value, str):
        return {"lesson_id": value}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"index": value}
    if isinstance(value, Mapping):
        return dict(value)
    raise ValueError("input must be a lesson selector object, string, integer, or null")


def _select_fixture(lessons, request):
    if "index" in request:
        index = request["index"]
        # Ensure index is an actual integer, not bool, float or numeric string
        if not isinstance(index, int) or isinstance(index, bool):
            raise ValueError("index must be an integer")
        if not 0 <= index < len(lessons):
            raise ValueError("index is outside the fixture lesson range")
        return lessons[index]
    for key in ("lesson_id", "case", "topic", "subject"):
        if key in request and str(request[key]).strip():
            wanted = str(request[key]).strip().lower()
            for lesson in lessons:
                if lesson["lesson_id"] == wanted:
                    return lesson
            for lesson in lessons:
                if wanted in lesson["lesson_id"] or wanted in lesson["title"].lower():
                    return lesson
            for lesson in lessons:
                if any(wanted in unit["english"].lower() or wanted in unit["hangul"]
                       for unit in lesson["units"]):
                    return lesson
    return lessons[0]


def _reviewers(value):
    if value is None:
        return set()
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set, frozenset)):
        raise ValueError("trusted_reviewers must be a string, list, tuple, or set")
    # Validate that all items are strings
    for item in value:
        if not isinstance(item, str):
            raise ValueError("trusted_reviewers must contain only strings")
    return {str(item).strip() for item in value if str(item).strip()}


def _review_is_trusted(verification, trusted):
    if verification["status"] not in ("reviewed", "verified"):
        return True
    reviewer = verification.get("reviewer")
    return isinstance(reviewer, str) and reviewer.strip() in trusted


def _audio_is_available(asset_id, metadata):
    if metadata is None:
        return False
    if callable(metadata):
        return metadata(asset_id) is True
    if isinstance(metadata, Mapping):
        if asset_id not in metadata:
            return False
        value = metadata[asset_id]
        if isinstance(value, Mapping):
            return value.get("available") is True
        return value is True
    # For strings/bytes, fail closed - treat as no available audio (substring matching is forbidden)
    if isinstance(metadata, (str, bytes)):
        return False
    try:
        return asset_id in metadata
    except TypeError:
        return False


def _trusted_audio_ids(lesson, trusted):
    ids = set()
    for unit in lesson["units"]:
        for asset in unit["audio_assets"]:
            verification = asset["verification"]
            if verification["status"] in ("reviewed", "verified") and _review_is_trusted(verification, trusted):
                ids.add(asset["asset_id"])
    return ids


def _semantic_errors(lesson, trusted, available_audio):
    errors = []
    if not _review_is_trusted(lesson["verification"], trusted):
        errors.append("lesson reviewed/verified status lacks a trusted reviewer")
    units = {}
    for unit in lesson["units"]:
        unit_id = unit["unit_id"]
        if unit_id in units:
            errors.append(f"duplicate unit id: {unit_id}")
        units[unit_id] = unit
        for asset in unit["audio_assets"]:
            if not _review_is_trusted(asset["verification"], trusted):
                errors.append(
                    f"audio asset {asset['asset_id']} reviewed/verified status lacks a trusted reviewer"
                )
    audio_metadata = available_audio
    if audio_metadata is None:
        audio_metadata = _trusted_audio_ids(lesson, trusted)
    exercise_ids = set()
    for exercise in lesson["exercises"]:
        exercise_id = exercise["exercise_id"]
        if exercise_id in exercise_ids:
            errors.append(f"duplicate exercise id: {exercise_id}")
        exercise_ids.add(exercise_id)
        unit = units.get(exercise["unit_id"])
        if unit is None:
            errors.append(f"exercise {exercise_id} references unknown unit {exercise['unit_id']}")
        if not 0 <= exercise["correct_option"] < len(exercise["options"]):
            errors.append(f"exercise {exercise_id} answer index is outside its options")
        if exercise["kind"] == "listening_choice" and unit is not None:
            assets = unit["audio_assets"]
            if not assets:
                errors.append(f"listening exercise {exercise_id} has no referenced audio")
            elif not any(_audio_is_available(asset["asset_id"], audio_metadata) for asset in assets):
                errors.append(f"listening exercise {exercise_id} has no available audio")
    for widget in lesson["widgets"]:
        widget_type = widget["type"]
        ref_id = widget["ref_id"]
        if widget_type in AUDIO_WIDGET_TYPES and ref_id not in units:
            errors.append(f"{widget_type} widget references unknown unit {ref_id}")
        elif widget_type == "exercise" and ref_id not in exercise_ids:
            errors.append(f"exercise widget references unknown exercise {ref_id}")
    return errors


def validate_lesson(data, trusted_reviewers=(), *, available_audio=None):
    """Validate a lesson-v1 object and return a defensive copy."""
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            raise ValueError("lesson is not valid JSON") from exc
    if not isinstance(data, Mapping):
        raise ValueError("lesson must be a JSON object")
    structural = sorted(_validator().iter_errors(data), key=lambda error: [str(part) for part in error.path])
    if structural:
        detail = "; ".join(
            f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}"
            for error in structural[:5]
        )
        raise ValueError(f"invalid lesson structure: {detail}")
    semantic = _semantic_errors(data, _reviewers(trusted_reviewers), available_audio)
    if semantic:
        raise ValueError("invalid lesson: " + "; ".join(semantic))
    return copy.deepcopy(dict(data))


def generate_lesson(input=None, provider=None, *, trusted_reviewers=(), available_audio=None):
    """Generate and validate a lesson from fixtures or an injected provider."""
    request = _request(input)
    # Reject selector keys that would set trust authority - fail closed
    if "trusted_reviewers" in request:
        raise ValueError("trusted_reviewers must be passed as a keyword argument, not in selector object")
    if "available_audio" in request:
        raise ValueError("available_audio must be passed as a keyword argument, not in selector object")
    
    if provider is not None:
        try:
            data = provider(input)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"provider failed: {exc}") from exc
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError as exc:
                raise ValueError("provider returned invalid JSON") from exc
    else:
        data = _select_fixture(_fixtures(), request)
    return validate_lesson(data, trusted_reviewers, available_audio=available_audio)
