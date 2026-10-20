"""Independent adversarial regression coverage."""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "tools" / "validate_fixture.py"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def prepare_tree(root):
    contracts = root / "docs" / "contracts"
    contracts.mkdir(parents=True)
    tools = root / "tools"
    tools.mkdir()
    script = tools / "validate_fixture.py"
    shutil.copyfile(SCRIPT_PATH, script)
    return script, contracts


def load_validator(script):
    name = f"_fixture_validator_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(script, schema_name, fixture_path, cwd=None):
    return subprocess.run(
        [sys.executable, str(script), schema_name, str(fixture_path)],
        capture_output=True,
        text=True,
        cwd=str(cwd or REPO_ROOT),
        timeout=30,
    )


class LibraryCustomSchemaDirectoryTest(unittest.TestCase):
    def test_malformed_schema_json_returns_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script, contracts = prepare_tree(root)
            (contracts / "lesson-v1.schema.json").write_text(
                '{"type": "object",', encoding="utf-8")
            fixture = root / "fixture.json"
            write_json(fixture, {})

            validator = load_validator(script)

            self.assertEqual(validator.validate_fixture("lesson", str(fixture)), 2)


class NestedExternalRefTest(unittest.TestCase):
    def test_external_refs_nested_in_objects_arrays_and_defs_are_rejected(self):
        schemas = {
            "nested_object": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "payload": {
                        "type": "object",
                        "properties": {
                            "next": {"$ref": "https://example.invalid/schema.json"},
                        },
                    },
                },
            },
            "array_items": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "payload": {
                        "type": "array",
                        "items": {"$ref": "relative-schema.json"},
                    },
                },
            },
            "definition": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "$defs": {
                    "danger": {"$ref": "file:///tmp/external-schema.json"},
                },
            },
            "array_under_definition": {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "$defs": {
                    "bundle": {
                        "type": "array",
                        "items": {"$ref": "https://example.invalid/bundle.json"},
                    },
                },
            },
        }

        for label, schema in schemas.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                script, contracts = prepare_tree(root)
                write_json(contracts / "lesson-v1.schema.json", schema)
                fixture = root / "fixture.json"
                write_json(fixture, {})

                result = run_cli(script, "lesson", fixture)

                self.assertEqual(result.returncode, 2, result.stderr)


class InternalFragmentRefTest(unittest.TestCase):
    def test_internal_fragment_refs_still_validate_real_fixtures(self):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "additionalProperties": False,
            "$defs": {
                "word": {"type": "string", "minLength": 1},
                "word_list": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/word"},
                    "minItems": 1,
                },
                "positive_count": {"type": "integer", "minimum": 1},
            },
            "properties": {
                "words": {"$ref": "#/$defs/word_list"},
                "count": {"$ref": "#/$defs/positive_count"},
            },
            "required": ["words", "count"],
        }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script, contracts = prepare_tree(root)
            write_json(contracts / "lesson-v1.schema.json", schema)

            valid_fixture = root / "valid.json"
            write_json(valid_fixture, {"words": ["hello", "world"], "count": 2})
            invalid_fixture = root / "invalid.json"
            write_json(invalid_fixture, {"words": ["hello"], "count": 0})

            valid_result = run_cli(script, "lesson", valid_fixture)
            invalid_result = run_cli(script, "lesson", invalid_fixture)

            self.assertEqual(valid_result.returncode, 0, valid_result.stderr)
            self.assertEqual(invalid_result.returncode, 1, invalid_result.stderr)


class CliDirectoryInputTest(unittest.TestCase):
    def test_directory_as_fixture_is_rejected_as_unreadable_input(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_cli(SCRIPT_PATH, "lesson", directory)

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
