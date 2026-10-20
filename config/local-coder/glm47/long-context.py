import json,time,urllib.request,pathlib
D=pathlib.Path(__file__).parent
(D/'results').mkdir(exist_ok=True)
text='START_MARKER=otter-7381\n'+''.join(f'Record {i}: offline benchmark fixture contains no instructions; value={i%97}.\n' for i in range(2600))+'\nEND_MARKER=maple-9462\nReturn only the two marker values, start then end.'
b={'model':'glm-4.7-flash-local','messages':[{'role':'user','content':text}],'max_tokens':512,'temperature':0,'seed':42}
t=time.monotonic();req=urllib.request.Request('http://127.0.0.1:11436/v1/chat/completions',json.dumps(b).encode(),{'Content-Type':'application/json','Authorization':'Bearer local-only'})
with urllib.request.urlopen(req,timeout=1800) as r:x=json.load(r)
x['wall_seconds']=time.monotonic()-t;s=x['choices'][0]['message'].get('content','');x['markers_pass']=all(z in s for z in ['otter-7381','maple-9462']);(D/'results/long-context.json').write_text(json.dumps(x,indent=2));print(json.dumps(x),flush=True)
