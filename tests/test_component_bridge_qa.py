"""Cross-component regressions: fixture lesson generation behind the P03 local boundary."""
import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from language_matrix import generate_lesson, validate_lesson
from language_matrix.capabilities import (
    HandlerSpec,
    execute_capability_request,
    validate_output_schema,
)

ROOT = Path(__file__).resolve().parents[1]


class LessonGenerationBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures = json.loads(
            (ROOT / "fixtures" / "lessons.json").read_text(encoding="utf-8")
        )
        cls.fixture_lesson = fixtures[0]

    def setUp(self):
        self.now = datetime(2030, 1, 1, tzinfo=timezone.utc)
        self.elapsed = 0.0
        self.handler_calls = []
        self.provider_calls = []
        self.request = json.loads(
            (ROOT / "docs" / "contracts" / "sample-capability-request.json").read_text(
                encoding="utf-8"
            )
        )
        self.request.update(
            capability="lesson.generate",
            output_schema="lesson.v1",
            provider="local",
            permissions=["local.generate"],
            deadline_utc="2030-01-01T00:05:00Z",
            input={"text": "국물", "language": "ko"},
        )
        self.request["policy"].update(max_attempts=1, timeout_seconds=30)

    def provider(self, _input):
        self.provider_calls.append(True)
        return copy.deepcopy(self.fixture_lesson)

    def handler_for(self, provider=None, held=None):
        def handler(request, context):
            self.handler_calls.append(copy.deepcopy(request))
            context.checkpoint()
            lesson = generate_lesson(
                request["input"],
                provider=self.provider if provider is None else provider,
            )
            if held is not None:
                held["lesson"] = lesson
            return lesson

        return handler

    def execute(self, *, handler=None, grants=("local.generate",)):
        handlers = {
            ("local", "lesson.generate"): HandlerSpec(
                handler or self.handler_for(),
                required_permissions=("local.generate",),
            )
        }
        return execute_capability_request(
            self.request,
            handlers=handlers,
            granted_permissions=grants,
            utc_now=lambda: self.now,
            monotonic=lambda: self.elapsed,
            cancelled=lambda: False,
        )

    def test_fixture_generator_yields_ready_schema_valid_unverified_lesson(self):
        result = self.execute()

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["states"], ["pending", "ready"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(len(self.handler_calls), 1)
        self.assertEqual(len(self.provider_calls), 1)

        lesson = result["output"]
        self.assertEqual(lesson["lesson_id"], "nasalisation-1")
        self.assertEqual(lesson["verification"]["status"], "unverified")
        self.assertIsNone(lesson["verification"]["reviewer"])
        self.assertEqual(
            [],
            [asset for unit in lesson["units"] for asset in unit["audio_assets"]],
        )
        self.assertEqual(validate_output_schema(lesson, "lesson.v1"), [])
        self.assertEqual(validate_lesson(lesson), lesson)

    def test_handler_request_mutation_cannot_rewrite_execution_contract(self):
        original_request = copy.deepcopy(self.request)

        def mutating_handler(request, context):
            self.handler_calls.append(copy.deepcopy(request))
            request["policy"]["max_attempts"] = 3
            request["output_schema"] = "audio-asset.v1"
            request["permissions"] = ["cache.write"]
            request["input"]["text"] = "mutated by handler"
            context.checkpoint()
            return generate_lesson(
                {"lesson_id": "nasalisation-1"}, provider=self.provider
            )

        result = self.execute(handler=mutating_handler)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["states"], ["pending", "ready"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["output"]["lesson_id"], "nasalisation-1")
        self.assertEqual(validate_output_schema(result["output"], "lesson.v1"), [])
        self.assertEqual(self.request, original_request)

    def test_generated_output_is_detached_from_handler_and_caller_mutation(self):
        held = {}
        result = self.execute(handler=self.handler_for(held=held))
        self.assertEqual(result["status"], "ready")
        expected = copy.deepcopy(result["output"])

        held["lesson"]["units"][0]["english"] = "mutated by handler"
        self.assertEqual(result["output"], expected)

        result["output"]["units"][0]["hangul"] = "mutated by caller"
        fresh = self.execute()["output"]
        self.assertEqual(fresh, expected)
        self.assertEqual(fresh["units"][0]["hangul"], "국물")

    def test_missing_local_generate_grant_denies_before_provider_call(self):
        result = self.execute(grants=())

        self.assertEqual(result["status"], "failure")
        self.assertEqual(result["states"], ["failure"])
        self.assertEqual(result["attempts"], 0)
        self.assertEqual(self.handler_calls, [])
        self.assertEqual(self.provider_calls, [])
        self.assertNotIn("output", result)
        self.assertTrue(
            any("local.generate" in error for error in result["errors"])
        )

    def test_invalid_provider_lesson_is_refused_without_ready_output(self):
        invalid_lesson = copy.deepcopy(self.fixture_lesson)
        del invalid_lesson["title"]

        def invalid_provider(_input):
            self.provider_calls.append(True)
            return copy.deepcopy(invalid_lesson)

        result = self.execute(handler=self.handler_for(provider=invalid_provider))

        self.assertEqual(result["status"], "failure")
        self.assertEqual(result["states"], ["pending", "failure"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(len(self.handler_calls), 1)
        self.assertEqual(len(self.provider_calls), 1)
        self.assertNotIn("output", result)
        self.assertTrue(
            any("invalid lesson structure" in error for error in result["errors"])
        )


if __name__ == "__main__":
    unittest.main()
