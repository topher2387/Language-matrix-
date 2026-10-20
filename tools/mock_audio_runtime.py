#!/usr/bin/env python3
"""Two mocked local metadata requests; no audio generation or playback."""
import argparse
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from language_matrix.capabilities import HandlerSpec, execute_capability_request


def run_demo(*, no_grants=False, cancelled=False, invalid_output=False):
    sample = json.loads((ROOT / 'docs/proposals/audio-asset-v1.proposed.sample.json').read_text())
    provider_calls = []

    def handler(request, context):
        context.checkpoint()
        voice = request['input']['voice_id']
        provider_calls.append(voice)
        output = copy.deepcopy(sample)
        output.update(voice_id=voice, asset_id='mock-' + voice)
        if invalid_output:
            output['content_hash'] = 'invalid'
        return output

    executions = []
    for voice in ('voice-one', 'voice-two'):
        request = {
            'schema_version': '1.0', 'request_id': 'mock-' + uuid.uuid4().hex,
            'capability': 'tts.synthesize', 'provider': 'local',
            'input': {'text': '안녕하세요.', 'language': 'ko', 'voice_id': voice},
            'policy': {'max_cost_usd': 0, 'allow_network': False, 'max_attempts': 1, 'timeout_seconds': 30},
            'rationale': 'Mock metadata only; no real audio or teaching approval.',
            'output_schema': 'audio-asset.v1', 'permissions': ['local.generate'],
            'deadline_utc': (datetime.now(timezone.utc) + timedelta(minutes=5)).strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        executions.append(execute_capability_request(
            request, handlers={('local', 'tts.synthesize'): HandlerSpec(handler, required_permissions=('local.generate',))},
            granted_permissions=() if no_grants else ('local.generate',), cancelled=lambda: cancelled,
        ))
    return {'fixture_only': True, 'no_audio_bytes': True, 'provider_calls': provider_calls, 'executions': executions}


def main():
    parser = argparse.ArgumentParser(description='Mock audio runtime; metadata only')
    parser.add_argument('--no-grants', action='store_true')
    parser.add_argument('--cancelled', action='store_true')
    parser.add_argument('--invalid-output', action='store_true')
    args = parser.parse_args()
    try:
        result = run_demo(no_grants=args.no_grants, cancelled=args.cancelled, invalid_output=args.invalid_output)
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if all(item['status'] == 'ready' for item in result['executions']) else 1


if __name__ == '__main__':
    sys.exit(main())
