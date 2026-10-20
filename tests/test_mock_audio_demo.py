"""Controller repaired tests exercising actual CLI runtime outcomes."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class MockAudioDemoTest(unittest.TestCase):
    def run_cli(self, *args):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, str(ROOT/'tools/mock_audio_runtime.py'), *args], cwd=folder, capture_output=True, text=True, timeout=20)
        return result, json.loads(result.stdout)

    def test_two_voices_real_runtime_cross_cwd(self):
        result, payload = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertTrue(payload['fixture_only'])
        self.assertTrue(payload['no_audio_bytes'])
        self.assertEqual(payload['provider_calls'], ['voice-one','voice-two'])
        self.assertEqual(len(payload['executions']), 2)
        for voice, execution in zip(payload['provider_calls'], payload['executions']):
            self.assertEqual(execution['states'], ['pending','ready'])
            self.assertEqual(execution['attempts'], 1)
            self.assertEqual(execution['output']['voice_id'], voice)
            self.assertEqual(execution['output']['content_hash'], '0'*64)
            self.assertEqual(execution['output']['verification']['status'], 'unverified')
            self.assertEqual(execution['output']['license_info']['status'], 'unknown')

    def test_refusals_before_provider(self):
        for flag in ['--no-grants','--cancelled']:
            with self.subTest(flag=flag):
                result, payload = self.run_cli(flag)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(payload['provider_calls'], [])
                for execution in payload['executions']:
                    self.assertEqual(execution['status'], 'failure')
                    self.assertEqual(execution['attempts'], 0)
                    self.assertNotIn('output', execution)

    def test_invalid_metadata_discarded(self):
        result, payload = self.run_cli('--invalid-output')
        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload['provider_calls'], ['voice-one','voice-two'])
        for execution in payload['executions']:
            self.assertEqual(execution['states'], ['pending','failure'])
            self.assertEqual(execution['attempts'], 1)
            self.assertNotIn('output', execution)

    def test_unknown_arguments_rejected(self):
        result = subprocess.run([sys.executable, str(ROOT/'tools/mock_audio_runtime.py'), '--unknown'], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
