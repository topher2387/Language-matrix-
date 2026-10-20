"""Controller acceptance checks independent of the export worker's tests."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from language_matrix import validate_lesson
from tools import export_runtime_lesson as exporter

ROOT = Path(__file__).resolve().parents[1]

class ExportAcceptanceTest(unittest.TestCase):
    def cli(self, *args):
        with tempfile.TemporaryDirectory() as folder:
            return subprocess.run([sys.executable, str(ROOT / 'tools/export_runtime_lesson.py'), *args], cwd=folder, capture_output=True, text=True, timeout=15)

    def test_actual_generator_is_invoked(self):
        with patch.object(exporter, 'generate_lesson', wraps=exporter.generate_lesson) as generator:
            result = exporter.export_lesson()
        self.assertEqual(generator.call_count, 1)
        self.assertEqual(result['lesson_id'], 'nasalisation-1')
        self.assertEqual(result['verification']['status'], 'unverified')
        self.assertEqual(validate_lesson(result), result)

    def test_selector_rejects_unknown_or_authority_payload(self):
        for selector in ('unknown-selector', {'permissions': ['local.generate']}, 99, True):
            with self.subTest(selector=selector), self.assertRaises(ValueError):
                exporter.export_lesson(selector)

    def test_cli_cross_cwd_schema_valid_success(self):
        result = self.cli('--lesson-id', 'nasalisation-1')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        lesson = json.loads(result.stdout)
        self.assertEqual(validate_lesson(lesson), lesson)
        self.assertEqual(lesson['lesson_id'], 'nasalisation-1')

    def test_cli_refusals_emit_no_output(self):
        for args in [('--no-grants',), ('--cancelled',), ('--lesson-id', 'unknown-selector'), ('--unknown-argument',)]:
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
                self.assertTrue(result.stderr.strip())
                if args[0] in ('--no-grants', '--cancelled'):
                    self.assertNotIn('unrecognized arguments', result.stderr)

    def test_refusal_prevents_generator_call(self):
        for kwargs in ({'granted_permissions': ()}, {'cancelled': lambda: True}):
            with self.subTest(kwargs=kwargs), patch.object(exporter, 'generate_lesson') as generator:
                with self.assertRaises(ValueError):
                    exporter.export_lesson(**kwargs)
                generator.assert_not_called()

    def test_distinct_request_ids_across_exports(self):
        with patch.object(exporter, 'execute_capability_request', wraps=exporter.execute_capability_request) as execute:
            exporter.export_lesson()
            exporter.export_lesson()
        ids = [call.args[0]['request_id'] for call in execute.call_args_list]
        self.assertEqual(len(set(ids)), 2)
        self.assertTrue(all(0 < len(value) <= 64 for value in ids))

    def test_missing_default_refuses_before_generator(self):
        with patch.object(exporter.lessons, '_fixtures', return_value=[{'lesson_id': 'liaison-1'}]), patch.object(exporter, 'generate_lesson') as generator:
            with self.assertRaises(ValueError):
                exporter.export_lesson()
            generator.assert_not_called()
