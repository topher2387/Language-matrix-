import json
import time
import urllib.request
from pathlib import Path

root = Path('/home/topher/Language-matrix-coder')
def call(path, data=None):
    req = urllib.request.Request('http://127.0.0.1:4097' + path,
        data=None if data is None else json.dumps(data).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as response:
        content = response.read()
        return json.loads(content) if content else None

report = {'passed': False}
try:
    session = call('/session', {'title': 'Local recovery: cancellation and response test'})['id']
    report['session'] = session
    payload = {'agent': 'supervised-coder', 'model': {'providerID': 'ollama-local', 'modelID': 'qwen3-coder-supervised:32k'},
               'parts': [{'type': 'text', 'text': 'Reply RECOVERY_OK only. Do not use tools or change files.'}]}
    call(f'/session/{session}/prompt_async', payload)
    time.sleep(1)
    started = time.monotonic()
    report['abort_accepted'] = call(f'/session/{session}/abort', {})
    report['abort_seconds'] = time.monotonic() - started
    report['status_after_abort'] = call('/session/status')
    (root / 'recovery-evidence.json').write_text(json.dumps(report, indent=2))
    call(f'/session/{session}/prompt_async', payload)
    end = time.monotonic() + 240
    while time.monotonic() < end:
        messages = call(f'/session/{session}/message')
        completed = [m for m in messages if m['info']['role'] == 'assistant' and m['info'].get('time', {}).get('completed')]
        if completed:
            last = completed[-1]
            text = ''.join(p.get('text', '') for p in last.get('parts', []) if p.get('type') == 'text')
            if 'RECOVERY_OK' in text:
                report['reply'] = text
                report['response_seconds'] = time.monotonic() - started
                report['health'] = call('/global/health')
                report['passed'] = report['abort_accepted'] is True and report['health']['healthy'] is True
                break
        time.sleep(2)
    if not report['passed']:
        report['error'] = 'No verified response within bounded recovery test'
except Exception as error:
    report['error'] = repr(error)
finally:
    (root / 'recovery-evidence.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
raise SystemExit(0 if report['passed'] else 1)
