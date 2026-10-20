import urllib.request,urllib.error,json,time,pathlib
p=pathlib.Path(__file__).parent
for i in range(55):
 try:
  urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:11435/health',headers={'Authorization':'Bearer local-only'}),timeout=2);break
 except Exception:time.sleep(1)
def api(d):
 t=time.monotonic();r=json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:11435/v1/chat/completions',data=json.dumps(d).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer local-only'}),timeout=600));r['wall_seconds']=time.monotonic()-t;return r
d={'model':'north-mini-code-supervised:250k','max_tokens':1024,'temperature':0,'messages':[{'role':'user','content':'Write a Python function unique_preserve_order(items) returning unique hashable items in first occurrence order. Include a short explanation.'}]}
r=api(d);(p/'generation-smoke.json').write_text(json.dumps(r,indent=2));print('GENERATION',json.dumps(r),flush=True)
d.update(max_tokens=1024,messages=[{'role':'user','content':'Use the add tool to add 17 and 25. Do not calculate without the tool.'}],tools=[{'type':'function','function':{'name':'add','description':'Add two integers','parameters':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b']}}}]);r=api(d);(p/'tool-call-smoke.json').write_text(json.dumps(r,indent=2));msg=r['choices'][0]['message'];calls=msg.get('tool_calls',[]);assert len(calls)==1 and calls[0]['function']['name']=='add' and json.loads(calls[0]['function']['arguments'])=={'a':17,'b':25},msg
d['messages'] += [msg,{'role':'tool','tool_call_id':calls[0]['id'],'content':'42'}];r2=api(d);(p/'tool-result-smoke.json').write_text(json.dumps(r2,indent=2));assert '42' in r2['choices'][0]['message'].get('content',''),r2;print('TOOL_ROUNDTRIP_PASS',flush=True)
