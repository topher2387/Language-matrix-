import urllib.request,json,time,pathlib
D=pathlib.Path(__file__).parent
(D/'results').mkdir(exist_ok=True)
for _ in range(90):
 try:
  with urllib.request.urlopen('http://127.0.0.1:11436/health',timeout=1) as r: assert json.load(r)['status']=='ok'
  break
 except Exception:time.sleep(1)
b={'model':'glm-4.7-flash-local','messages':[{'role':'user','content':'Use the add tool to add 17 and 25. Then report its returned result.'}],'tools':[{'type':'function','function':{'name':'add','description':'Add two integers','parameters':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b']}}}],'max_tokens':16384,'temperature':0,'seed':42}
out=[]
for i in range(2):
 t=time.monotonic();req=urllib.request.Request('http://127.0.0.1:11436/v1/chat/completions',json.dumps(b).encode(),{'Content-Type':'application/json','Authorization':'Bearer local-only'})
 with urllib.request.urlopen(req,timeout=180) as r:x=json.load(r)
 x['wall_seconds']=time.monotonic()-t;out.append(x);m=x['choices'][0]['message']
 if i==0:
  tc=m['tool_calls'][0];assert tc['function']['name']=='add' and json.loads(tc['function']['arguments'])=={'a':17,'b':25};b['messages'] += [m,{'role':'tool','tool_call_id':tc['id'],'content':'42'}]
 else:assert '42' in m.get('content','')
(D/'results/final-cpu42-tools.json').write_text(json.dumps({'pass':True,'results':out},indent=2));print([(x['wall_seconds'],x.get('timings')) for x in out])
