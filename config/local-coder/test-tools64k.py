import json,urllib.request
from pathlib import Path
p=Path('/home/topher/Language-matrix-coder/qwen80-setup');model='qwen3-coder-next-supervised:64k'
def api(path,data=None):
 r=urllib.request.Request('http://127.0.0.1:11434'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
 return json.load(urllib.request.urlopen(r,timeout=600))
# Model emits a structured call; the controller supplies only a fixed arithmetic result.
d={'model':model,'stream':False,'keep_alive':'10m','options':{'num_ctx':65536,'num_predict':128,'temperature':0},'messages':[{'role':'user','content':'Use the add tool to add 17 and 25. Do not calculate without the tool.'}],'tools':[{'type':'function','function':{'name':'add','description':'Add two integers','parameters':{'type':'object','properties':{'a':{'type':'integer'},'b':{'type':'integer'}},'required':['a','b']}}}]}
r=api('/api/chat',d);(p/'context64k-tool-call-test.json').write_text(json.dumps(r,indent=2));calls=r.get('message',{}).get('tool_calls',[]);assert len(calls)==1 and calls[0]['function']['name']=='add' and calls[0]['function']['arguments']=={'a':17,'b':25},'Unexpected tool call'
d['messages']+=[r['message'],{'role':'tool','tool_name':'add','content':'42'}];r2=api('/api/chat',d);(p/'context64k-tool-result-test.json').write_text(json.dumps(r2,indent=2));assert '42' in r2['message'].get('content',''),'Missing tool result in answer'
(p/'context64k-loaded-model.json').write_text(json.dumps(api('/api/ps'),indent=2));print('TOOL_ROUNDTRIP_PASS',flush=True)
