"""Engine and semantic validation tests for lesson-v1."""
import copy
import json
from pathlib import Path
import unittest

from language_matrix import generate_lesson, validate_lesson

ROOT = Path(__file__).resolve().parents[1]


class LessonEngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = json.loads((ROOT / "fixtures" / "lessons.json").read_text(encoding="utf-8"))
        cls.sample = json.loads((ROOT / "docs" / "contracts" / "sample-lesson.json").read_text(encoding="utf-8"))

    def lesson(self, index=0):
        return copy.deepcopy(self.fixtures[index])

    def listening(self, audio=True, verified=False):
        lesson = self.lesson()
        exercise = lesson["exercises"][0]
        exercise["kind"] = "listening_choice"
        if audio:
            lesson["units"][0]["audio_assets"] = [{
                "asset_id": "a1",
                "voice_id": "v1",
                "verification": {
                    "status": "verified" if verified else "unverified",
                    "reviewer": "rev" if verified else None,
                    "notes": "Provisional asset metadata."
                }
            }]
        return lesson

    def test_fixture_coverage_and_offline_defaults(self):
        units = [unit for lesson in self.fixtures for unit in lesson["units"]]
        self.assertEqual(25, len(units))
        ids = {lesson["lesson_id"] for lesson in self.fixtures}
        self.assertEqual(
            {"nasalisation-1", "liaison-1", "aspiration-1", "tensification-1", "palatalisation-1"},
            ids,
        )
        for lesson in self.fixtures:
            self.assertEqual("unverified", lesson["verification"]["status"])
            self.assertIsNone(lesson["verification"]["reviewer"])
            validate_lesson(lesson)
        self.assertEqual(ids, {generate_lesson(name)["lesson_id"] for name in ids})

    def test_default_generation_is_deterministic_and_defensive(self):
        first = generate_lesson()
        second = generate_lesson()
        self.assertEqual(first, second)
        first["units"][0]["english"] = "changed"
        self.assertNotEqual(first["units"][0]["english"], generate_lesson()["units"][0]["english"])
        self.assertEqual("nasalisation-1", generate_lesson("nasalisation")["lesson_id"])
        self.assertEqual("nasalisation-1", generate_lesson(0)["lesson_id"])

    def test_structure_and_unknown_fields_fail(self):
        broken = self.lesson()
        del broken["units"][0]["phonology"]
        with self.assertRaises(ValueError):
            validate_lesson(broken)
        hostile = self.lesson()
        hostile["widgets"].append({"type": "teaching_unit", "ref_id": "n1", "html": "<b>x</b>"})
        with self.assertRaises(ValueError):
            validate_lesson(hostile)

    def test_duplicate_unit_and_exercise_ids_fail(self):
        lesson = self.lesson()
        lesson["units"].append(copy.deepcopy(lesson["units"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate unit id"):
            validate_lesson(lesson)
        lesson = self.lesson()
        lesson["exercises"].append(copy.deepcopy(lesson["exercises"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate exercise id"):
            validate_lesson(lesson)

    def test_exercise_references_and_answer_bounds_fail(self):
        lesson = self.lesson()
        lesson["exercises"][0]["unit_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "unknown unit"):
            validate_lesson(lesson)
        lesson = self.lesson()
        lesson["exercises"][0]["correct_option"] = len(lesson["exercises"][0]["options"])
        with self.assertRaisesRegex(ValueError, "answer index"):
            validate_lesson(lesson)

    def test_widget_references_must_match_type(self):
        for widget in (
            {"type": "teaching_unit", "ref_id": "missing"},
            {"type": "comparison", "ref_id": "missing"},
            {"type": "audio", "ref_id": "missing"},
            {"type": "exercise", "ref_id": "missing"},
        ):
            lesson = self.lesson()
            lesson["widgets"].append(widget)
            with self.subTest(widget=widget["type"]), self.assertRaisesRegex(ValueError, "unknown"):
                validate_lesson(lesson)

    def test_listening_requires_audio_and_trusted_availability(self):
        with self.assertRaisesRegex(ValueError, "no referenced audio"):
            validate_lesson(self.listening(audio=False))
        with self.assertRaisesRegex(ValueError, "no available audio"):
            validate_lesson(self.listening())
        validate_lesson(self.listening(), available_audio={"a1": True})
        with self.assertRaisesRegex(ValueError, "no available audio"):
            validate_lesson(self.listening(), available_audio={"a1": False})
        with self.assertRaisesRegex(ValueError, "no available audio"):
            validate_lesson(self.listening(), available_audio=[])

    def test_listening_can_use_trusted_local_audio_metadata(self):
        lesson = self.listening(verified=True)
        self.assertEqual("a1", validate_lesson(lesson, trusted_reviewers=("rev",))["units"][0]["audio_assets"][0]["asset_id"])
        with self.assertRaisesRegex(ValueError, "trusted reviewer"):
            validate_lesson(lesson)
        with self.assertRaisesRegex(ValueError, "trusted reviewer"):
            validate_lesson(lesson, trusted_reviewers=("someone-else",))

    def test_audio_availability_rejects_string_substring_matches(self):
        for metadata in ('xx-a1-xx', b'a1', 123):
            with self.subTest(metadata=metadata), self.assertRaisesRegex(ValueError, 'no available audio'):
                validate_lesson(self.listening(), available_audio=metadata)
        validate_lesson(self.listening(), available_audio=lambda asset_id: asset_id == 'a1')
        with self.assertRaisesRegex(ValueError, 'no available audio'):
            validate_lesson(self.listening(), available_audio=lambda asset_id: False)

    def test_generation_trust_is_separate_from_selector_input(self):
        reviewed = self.lesson()
        reviewed['verification'].update(status='verified', reviewer='mallory')
        for request in ({'trusted_reviewers': ['mallory']}, {'available_audio': {'a1': True}}):
            with self.subTest(request=request), self.assertRaises(ValueError):
                generate_lesson(request, provider=lambda _: reviewed)
        result = generate_lesson({}, provider=lambda _: reviewed, trusted_reviewers=['mallory'])
        self.assertEqual('verified', result['verification']['status'])
        validate_lesson(generate_lesson({}, provider=lambda _: self.listening(), available_audio={'a1': True}),
                        available_audio={'a1': True})

    def test_trust_and_index_inputs_fail_with_value_error(self):
        for reviewers in (123, {'reviewer': 'rev'}, [123]):
            with self.subTest(reviewers=reviewers), self.assertRaises(ValueError):
                validate_lesson(self.lesson(), trusted_reviewers=reviewers)
        for index in (1.9, True, '1'):
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, 'index must be an integer'):
                generate_lesson({'index': index})

    def test_reviewed_and_verified_claims_need_trusted_provenance(self):
        lesson = self.lesson()
        lesson["verification"].update(status="reviewed", reviewer="rev")
        with self.assertRaisesRegex(ValueError, "trusted reviewer"):
            validate_lesson(lesson)
        validate_lesson(lesson, trusted_reviewers=["rev"])
        lesson["verification"].update(status="verified", reviewer="mallory")
        with self.assertRaisesRegex(ValueError, "trusted reviewer"):
            validate_lesson(lesson, trusted_reviewers=["rev"])
        asset = self.listening(verified=True)
        asset["units"][0]["audio_assets"][0]["verification"]["reviewer"] = "mallory"
        with self.assertRaisesRegex(ValueError, "audio asset a1"):
            validate_lesson(asset, trusted_reviewers=("rev",))

    def test_unverified_content_and_plain_strings_are_preserved(self):
        lesson = self.lesson()
        hostile = "<script>alert('inert')</script> & 안녕"
        lesson["units"][0]["english"] = hostile
        result = validate_lesson(lesson)
        self.assertEqual(hostile, result["units"][0]["english"])
        self.assertEqual("unverified", result["verification"]["status"])
        self.assertIsNone(result["verification"]["reviewer"])

    def test_provider_results_are_validated(self):
        valid = self.lesson()
        self.assertEqual(valid, generate_lesson({"lesson_id": "fixture"}, provider=lambda _: valid))
        self.assertEqual(valid, generate_lesson({}, provider=lambda _: json.dumps(valid)))
        with self.assertRaises(ValueError):
            generate_lesson({}, provider=lambda _: [valid])
        with self.assertRaises(ValueError):
            generate_lesson({}, provider=lambda _: "{not json")
        with self.assertRaises(ValueError):
            generate_lesson({}, provider=lambda _: "not json")
        broken = self.lesson()
        del broken["title"]
        with self.assertRaisesRegex(ValueError, "invalid lesson structure"):
            generate_lesson({}, provider=lambda _: broken)
        duplicate = self.lesson()
        duplicate["units"].append(copy.deepcopy(duplicate["units"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate unit id"):
            generate_lesson({}, provider=lambda _: duplicate)
        with self.assertRaisesRegex(ValueError, "provider failed"):
            generate_lesson({}, provider=lambda _: (_ for _ in ()).throw(RuntimeError("down")))

    def test_provider_cannot_bypass_listening_or_review_checks(self):
        listening = self.listening()
        with self.assertRaisesRegex(ValueError, "no available audio"):
            generate_lesson({}, provider=lambda _: listening)
        reviewed = self.lesson()
        reviewed["verification"].update(status="verified", reviewer="model")
        with self.assertRaisesRegex(ValueError, "trusted reviewer"):
            generate_lesson({}, provider=lambda _: reviewed)

    def test_contract_sample_remains_valid_and_unverified(self):
        result = validate_lesson(self.sample)
        self.assertEqual("unverified", result["verification"]["status"])
        self.assertIsNone(result["verification"]["reviewer"])


if __name__ == "__main__":
    unittest.main()
