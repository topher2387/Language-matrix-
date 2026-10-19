"""Bounded local identity, tool-call and timing probe; no development work."""
import json
from pathlib import Path
import time
import urllib.request

BASE = 'qwen3-coder:30b-a3b-q4_K_M'
MODEL = 'qwen3-coder-supervised:8k'
ROOT = Path('/home/topher/Language-matrix-coder')

def request(path, data=None):
    payload = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request('http://127.0.0.1:11434' + path, data=payload,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as response:
        return json.load(response)

def timing(response):
    duration = response.get('eval_duration', 0) / 1e9
    return {'tokens': response.get('eval_count'), 'generation_seconds': duration,
            'tokens_per_second': response.get('eval_count', 0) / duration if duration else None,
            'prompt_tokens': response.get('prompt_eval_count'),
            'prompt_seconds': response.get('prompt_eval_duration', 0) / 1e9,
            'load_seconds': response.get('load_duration', 0) / 1e9}

report = {'base': BASE, 'runtime_alias': MODEL, 'passed': False}
try:
    tags = request('/api/tags')['models']
    report['identity'] = next(m for m in tags if m['name'] == BASE)
    show = request('/api/show', {'model': MODEL})
    report['details'] = show['details']
    report['capabilities'] = show.get('capabilities')
    report['parameters'] = show.get('parameters')
    assert report['details']['quantization_level'] == 'Q4_K_M', report['details']
    assert 'tools' in report['capabilities'], report['capabilities']
    started = time.monotonic()
    messages = [{'role': 'user', 'content': 'Call report_ready with status ready. Do not answer with text.'}]
    tool = {'type': 'function', 'function': {'name': 'report_ready',
            'description': 'Synthetic readiness probe with no side effects.',
            'parameters': {'type': 'object', 'properties': {'status': {'type': 'string', 'enum': ['ready']}},
                           'required': ['status'], 'additionalProperties': False}}}
    result = request('/api/chat', {'model': MODEL, 'messages': messages, 'tools': [tool],
                     'stream': False, 'keep_alive': '30m',
                     'options': {'temperature': 0, 'num_predict': 96}})
    report['tool_response'] = result['message']
    report['timing'] = timing(result)
    report['wall_seconds'] = time.monotonic() - started
    call = result['message']['tool_calls'][0]['function']
    assert call['name'] == 'report_ready' and call['arguments'] == {'status': 'ready'}, call
    messages += [result['message'], {'role': 'tool', 'tool_name': 'report_ready', 'content': 'READY_CONFIRMED'},
                 {'role': 'user', 'content': 'The test is complete. Reply exactly READY_CONFIRMED as plain text. Do not call more tools.'}]
    followup = request('/api/chat', {'model': MODEL, 'messages': messages, 'stream': False,
                       'tools': [tool], 'keep_alive': '30m', 'options': {'temperature': 0, 'num_predict': 64}})
    report['roundtrip_response'] = followup['message']
    report['roundtrip_timing'] = timing(followup)
    assert followup['message']['content'].strip() == 'READY_CONFIRMED', followup['message']
    report['placement'] = request('/api/ps')
    report['passed'] = True
except Exception as error:
    report['error'] = repr(error)
finally:
    (ROOT / 'smoke-evidence.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['passed'] else 1)
