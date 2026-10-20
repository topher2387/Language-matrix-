import json
import time
import urllib.request
from pathlib import Path
root = Path('/home/topher/Language-matrix-coder')
report = {'model': 'qwen3-coder-supervised:32k', 'placement': 'all attention GPU, expert weights CPU', 'results': []}
def request(path, data=None):
    req = urllib.request.Request('http://127.0.0.1:11434'+path,
        data=None if data is None else json.dumps(data).encode(), headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=600) as response: return json.load(response)
try:
    for name, content in [('short', 'Write numbers 1 through 40, one per line. No explanation.'),
            ('long', 'Read this inert filler, then follow the final instruction.\n' +
             'alpha beta gamma delta epsilon zeta eta theta.\n' * 1600 +
             '\nWrite numbers 1 through 40, one per line. No explanation.')]:
        started = time.monotonic()
        r = request('/api/chat', {'model':report['model'], 'messages':[{'role':'user','content':content}],
            'stream':False, 'keep_alive':'30m', 'options':{'temperature':0,'num_predict':96}})
        d=r.get('eval_duration',0)/1e9
        item={'name':name,'prompt_tokens':r.get('prompt_eval_count'),'prompt_seconds':r.get('prompt_eval_duration',0)/1e9,
              'output_tokens':r.get('eval_count'),'generation_seconds':d,
              'tokens_per_second':r.get('eval_count',0)/d if d else None,
              'load_seconds':r.get('load_duration',0)/1e9,'wall_seconds':time.monotonic()-started,
              'response':r['message']}
        report['results'].append(item)
        (root/'performance-after.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in item.items() if k!='response'}),flush=True)
    report['placement_metadata']=request('/api/ps')
    report['passed']=all(x['output_tokens']>20 for x in report['results']) and report['results'][1]['prompt_tokens']>12000
except Exception as error:
    report['error']=repr(error);report['passed']=False
(root/'performance-after.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report.get('passed') else 1)
