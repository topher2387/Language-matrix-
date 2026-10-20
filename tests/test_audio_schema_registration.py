"""Approved metadata contract in mocked local runtime; never real audio."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest
from language_matrix.capabilities import HandlerSpec, execute_capability_request, validate_output_schema

ROOT = Path(__file__).resolve().parents[1]

class AudioRegistrationTest(unittest.TestCase):
    def setUp(self):
        self.sample = json.loads((ROOT/'docs/proposals/audio-asset-v1.proposed.sample.json').read_text())
        self.request = json.loads((ROOT/'docs/contracts/sample-capability-request.json').read_text())
        self.request.update(capability='tts.synthesize', output_schema='audio-asset.v1', permissions=['local.generate'], deadline_utc=(datetime.now(timezone.utc)+timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ'))
        self.request['policy'].update(max_attempts=1, timeout_seconds=30)
        self.calls = []

    def execute(self, output=None, grants=('local.generate',), cancelled=lambda: False):
        def handler(request, context):
            context.checkpoint()
            self.calls.append(request['input'].get('voice_id'))
            result = copy.deepcopy(self.sample if output is None else output)
            result['voice_id'] = request['input'].get('voice_id', 'voice-example')
            return result
        return execute_capability_request(self.request, handlers={('local','tts.synthesize'): HandlerSpec(handler, required_permissions=('local.generate',))}, granted_permissions=grants, cancelled=cancelled)

    def test_registered_schema_matches_approved_draft_exactly(self):
        self.assertEqual((ROOT/'docs/contracts/audio-asset-v1.schema.json').read_bytes(), (ROOT/'docs/proposals/audio-asset-v1.proposed.schema.json').read_bytes())
        self.assertEqual(validate_output_schema(self.sample, 'audio-asset.v1'), [])

    def test_two_mock_voices_follow_pending_ready_without_trust_upgrade(self):
        for voice in ('voice-one','voice-two'):
            self.request['input']['voice_id'] = voice
            result = self.execute()
            self.assertEqual(result['states'], ['pending','ready'])
            self.assertEqual(result['output']['voice_id'], voice)
            self.assertEqual(result['output']['verification']['status'], 'unverified')
            self.assertEqual(result['output']['license_info']['status'], 'unknown')
        self.assertEqual(self.calls, ['voice-one','voice-two'])

    def test_no_grant_refuses_before_provider(self):
        result = self.execute(grants=())
        self.assertEqual(result['attempts'], 0)
        self.assertNotIn('output', result)
        self.assertEqual(self.calls, [])

    def test_pre_cancel_refuses_before_provider(self):
        result = self.execute(cancelled=lambda: True)
        self.assertEqual(result['attempts'], 0)
        self.assertNotIn('output', result)
        self.assertEqual(self.calls, [])

    def test_malformed_audio_output_fails_without_release(self):
        invalid = copy.deepcopy(self.sample)
        invalid['content_hash'] = 'invalid'
        result = self.execute(output=invalid)
        self.assertEqual(result['states'], ['pending','failure'])
        self.assertNotIn('output', result)
