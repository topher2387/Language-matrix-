#!/usr/bin/env python3
"""CLI tool to export lesson-v1 JSON from existing generate_lesson fixture result."""

import argparse
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from language_matrix.lessons import generate_lesson, validate_lesson
from language_matrix.capabilities import (
    HandlerSpec,
    execute_capability_request,
)
from language_matrix import lessons


def _lesson_handler(request, context):
    """Handler for lesson.generate capability that returns a fixture lesson."""
    # Check if execution should be cancelled or deadline expired
    context.checkpoint()

    # Get the lesson_id from request input - read from "text" field
    lesson_text = None
    if isinstance(request.get("input"), dict):
        lesson_text = request["input"].get("text")

    # Generate the lesson using the existing generate_lesson function
    lesson = generate_lesson(lesson_text)
    return lesson


def export_lesson(lesson_input=None, *, granted_permissions=("local.generate",), cancelled=lambda: False):
    """
    Export a lesson-v1 JSON through trusted HandlerSpec runtime.

    Args:
        lesson_input: Lesson selector (string or None) - only accepts exact string IDs from fixtures/lessons.json
        granted_permissions: Permissions granted to the handler
        cancelled: Function that returns True if execution should be cancelled

    Returns:
        The validated lesson-v1 JSON as a dict

    Raises:
        ValueError: If lesson is invalid, unknown selector, or execution fails
    """
    # Validate lesson_input - only accept None or exact string IDs from fixtures/lessons.json
    if lesson_input is not None:
        if not isinstance(lesson_input, str):
            raise ValueError("Lesson input must be a string ID or None")

        # Load the fixture lessons to validate against
        fixtures = lessons._fixtures()
        valid_ids = {lesson["lesson_id"] for lesson in fixtures}

        if lesson_input not in valid_ids:
            raise ValueError(f"Unknown lesson ID: {lesson_input}")
    else:
        # For default case, we must validate that "nasalisation-1" exists in fixtures
        # to prevent silent fallbacks
        fixtures = lessons._fixtures()
        valid_ids = {lesson["lesson_id"] for lesson in fixtures}

        if "nasalisation-1" not in valid_ids:
            raise ValueError("Default lesson 'nasalisation-1' not found in fixtures")

    # Create the capability request for lesson generation
    handlers = {
        ("local", "lesson.generate"): HandlerSpec(
            _lesson_handler, required_permissions=("local.generate",)
        )
    }

    # Build the request with UTC deadline NOW+5 minutes and UUID request_id
    now = datetime.now(timezone.utc)
    deadline = now.replace(microsecond=0) + timedelta(minutes=5)
    deadline_str = deadline.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Generate a unique request ID for each export
    request_id = f"export-runtime-lesson-{uuid.uuid4()}"

    # If lesson_input is None, we'll use default behavior in the handler
    input_data = {}
    if lesson_input is not None:
        input_data["text"] = lesson_input
    else:
        input_data["text"] = "nasalisation-1"

    # Add language field as required by schema
    input_data["language"] = "ko"

    request = {
        "schema_version": "1.0",
        "request_id": request_id,
        "capability": "lesson.generate",
        "provider": "local",
        "input": input_data,
        "policy": {"max_cost_usd": 0, "allow_network": False,
                    "max_attempts": 1, "timeout_seconds": 30},
        "rationale": "Exporting lesson fixture through trusted runtime",
        "output_schema": "lesson.v1",
        "permissions": ["local.generate"],
        "deadline_utc": deadline_str,
    }

    # Execute the request
    result = execute_capability_request(
        request,
        handlers=handlers,
        granted_permissions=granted_permissions,
        cancelled=cancelled,
    )

    if result.get("status") != "ready":
        errors = "; ".join(result.get("errors", ["Unknown error"]))
        raise ValueError(f"Lesson generation failed: {errors}")

    # Validate the output
    output = result["output"]
    try:
        validated_lesson = validate_lesson(output, trusted_reviewers=())
        return validated_lesson
    except ValueError as exc:
        raise ValueError(f"Generated lesson failed validation: {exc}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Export lesson-v1 JSON through trusted runtime",
        prog="export_runtime_lesson"
    )

    parser.add_argument(
        "--lesson-id",
        help="Lesson ID to export (from fixtures/lessons.json)"
    )

    parser.add_argument(
        "--no-grants",
        action="store_true",
        help="Run without any granted permissions"
    )

    parser.add_argument(
        "--cancelled",
        action="store_true",
        help="Run with cancelled function that returns True immediately"
    )

    args = parser.parse_args()

    try:
        # Handle the lesson ID argument
        lesson_input = None
        if args.lesson_id is not None:
            lesson_input = args.lesson_id

        # Set up permissions and cancellation
        granted_permissions = () if args.no_grants else ("local.generate",)
        cancelled_func = lambda: args.cancelled

        # Export the lesson
        exported_lesson = export_lesson(
            lesson_input,
            granted_permissions=granted_permissions,
            cancelled=cancelled_func
        )

        # Output to stdout as JSON
        print(json.dumps(exported_lesson, ensure_ascii=False, indent=2))

    except ValueError as exc:
        # Write error to stderr and exit with non-zero code
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except SystemExit:
        # Re-raise SystemExit to allow argparse to handle it properly
        raise
    except Exception as exc:
        # Handle unexpected errors
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
