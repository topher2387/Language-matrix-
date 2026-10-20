"""Integration examples: validation previews and fixture-only lesson execution."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from integration_example import (
    example_batch_processing,
    example_lesson_execution,
    example_worker_integration,
)
from language_matrix.capabilities import validate_output_schema

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_LESSON = ROOT / "docs" / "contracts" / "sample-lesson.json"


class IntegrationTest(unittest.TestCase):
    def test_single_capability_is_explicitly_blocked(self):
        result = example_worker_integration()
        self.assertEqual(result['status'], 'blocked')
        self.assertFalse(result['executed'])
        self.assertTrue(any('schema file not found' in e for e in result['errors']))
        self.assertNotIn('result', result)

    def test_batch_preserves_refusal_for_each_reserved_contract(self):
        results = example_batch_processing()
        self.assertEqual(len(results), 2)
        self.assertEqual([r['capability'] for r in results], ['phonology.check', 'tts.synthesize'])
        for result in results:
            self.assertEqual(result['status'], 'blocked')
            self.assertFalse(result['executed'])
            self.assertTrue(result['errors'])
            self.assertNotIn('result', result)

    def test_lesson_execution_is_ready_with_unverified_fixture_output(self):
        result = example_lesson_execution()
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['states'], ['pending', 'ready'])
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['output'], json.loads(SAMPLE_LESSON.read_text(encoding='utf-8')))
        self.assertEqual(result['output']['verification']['status'], 'unverified')
        self.assertEqual(result['output']['units'][0]['audio_assets'], [])

    def test_lesson_output_is_schema_valid(self):
        result = example_lesson_execution()
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(validate_output_schema(result['output'], 'lesson.v1'), [])

    def test_no_grants_denies_before_any_attempt(self):
        result = example_lesson_execution(granted_permissions=())
        self.assertEqual(result['status'], 'failure')
        self.assertEqual(result['attempts'], 0)
        self.assertNotIn('output', result)
        self.assertTrue(result['errors'])

    def test_pre_cancelled_execution_refuses_before_any_attempt(self):
        result = example_lesson_execution(cancelled=lambda: True)
        self.assertEqual(result['status'], 'failure')
        self.assertEqual(result['attempts'], 0)
        self.assertNotIn('output', result)
        self.assertTrue(result['errors'])

    def test_cli_runs_from_another_cwd_with_honest_demo_json(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, str(ROOT / 'integration_example.py')],
                cwd=directory,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload['demo'])
        self.assertTrue(payload['fixture_only'])
        self.assertEqual(payload['kind'], 'offline-fixture-demo')
        self.assertIn('fixture-only', payload['note'].lower())
        execution = payload['lesson_execution']
        self.assertEqual(execution['status'], 'ready')
        self.assertEqual(execution['states'], ['pending', 'ready'])
        self.assertEqual(execution['output']['verification']['status'], 'unverified')
        previews = payload['previews']
        self.assertEqual([p['capability'] for p in previews], ['phonology.check', 'tts.synthesize'])
        for preview in previews:
            self.assertEqual(preview['status'], 'blocked')
            self.assertFalse(preview['executed'])
            self.assertTrue(preview['errors'])
            self.assertNotIn('result', preview)


if __name__ == '__main__':
    unittest.main()
