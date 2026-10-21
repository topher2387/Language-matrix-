import json,time,urllib.request,sys,pathlib,subprocess
D=pathlib.Path(__file__).parent
(D/'results').mkdir(exist_ok=True)
label=sys.argv[1]
def call(messages,**kw):
 body=dict(model='glm-4.7-flash-local',messages=messages,max_tokens=16384,temperature=0,seed=42,**kw)
 t=time.monotonic();req=urllib.request.Request('http://127.0.0.1:11436/v1/chat/completions',json.dumps(body).encode(),{'Content-Type':'application/json','Authorization':'Bearer local-only'})
 with urllib.request.urlopen(req,timeout=900) as r: x=json.load(r)
 x['wall_seconds']=round(time.monotonic()-t,3);return x
out={'label':label,'results':{}}
def save(): (D/'results'/f'{label}.json').write_text(json.dumps(out,indent=2))
msg=[{'role':'user','content':'Write only a Python function merge_ranges(ranges) in one fenced python block. Input list of integer (start,end) inclusive intervals. Reject reversed intervals with ValueError. Return sorted merged tuples; merge overlaps and adjacent intervals. Do not mutate input.'}]
x=call(msg);out['results']['coding']=x;save()
s=x['choices'][0]['message'].get('content','');code=s.split('```python')[-1].split('```')[0] if '```python' in s else s
try:
 ns={};exec(code,ns);f=ns['merge_ranges'];a=[(5,7),(1,2),(3,4),(10,10)];assert f(a)==[(1,7),(10,10)] and a==[(5,7),(1,2),(3,4),(10,10)];assert f([])==[];assert f([(1,1),(1,1)])==[(1,1)]
 try:f([(3,1)])
 except ValueError:pass
 else:raise AssertionError('reversed accepted')
 out['coding_pass']=True
except Exception as e:out['coding_pass']=False;out['coding_error']=repr(e)
save()
tools=[{'type':'function','function':{'name':'add','description':'Add two integers','parameters':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b']}}}]
m=[{'role':'user','content':'Use the add tool to add 17 and 25. Then report its returned result.'}]
x=call(m,tools=tools);out['results']['tool_call']=x;save()
try:
 am=x['choices'][0]['message'];tc=am['tool_calls'][0];assert tc['function']['name']=='add';args=json.loads(tc['function']['arguments']);assert args=={'a':17,'b':25};m += [am,{'role':'tool','tool_call_id':tc['id'],'content':'42'}];y=call(m,tools=tools);out['results']['tool_result']=y;out['tool_pass']='42' in y['choices'][0]['message'].get('content','')
except Exception as e:out['tool_pass']=False;out['tool_error']=repr(e)
save()
print(json.dumps({'label':label,'coding_pass':out['coding_pass'],'tool_pass':out['tool_pass'],'metrics':{k:{'wall':v['wall_seconds'],'timings':v.get('timings'),'finish':v['choices'][0]['finish_reason']} for k,v in out['results'].items()}}),flush=True)
