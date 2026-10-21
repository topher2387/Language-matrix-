#!/usr/bin/env python3
"""Bounded A/D diagnostic after the existing matrix; never interrupts another owner."""
import datetime,json,os,pathlib,signal,subprocess,time,urllib.request,threading
D=pathlib.Path(__file__).resolve().parents[1]; O=pathlib.Path(__file__).resolve().parent
URL='http://127.0.0.1:11438'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def get(path,body=None):
 req=urllib.request.Request(URL+path,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Bearer local-only','Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=90) as r:return json.load(r)
def stop(p):
 if p and p.poll() is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=20)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def save(): (O/'heldout-results.json').write_text(json.dumps(result,indent=2)+'\n')
result={'created':now(),'status':'waiting_for_original_matrix','cases':[]};save()
# No model request, GPU allocation, or changes to the original service during this wait.
limit=time.monotonic()+12000
while True:
 run=pathlib.Path((D/'active-run.txt').read_text().strip()); state=json.loads((run/'status.json').read_text())
 if state.get('status')=='all_cases_attempted_requires_independent_review':break
 if time.monotonic()>limit:result['status']='BLOCKED: original matrix not finished within two hours';save();raise SystemExit(0)
 time.sleep(15)
# Require the original owner to exit as well, even after its final status write.
for _ in range(20):
 active=subprocess.run(['systemctl','--user','is-active','language-matrix-reap50-125k-matrix.service'],capture_output=True,text=True).stdout.strip()
 if active!='active':break
 time.sleep(3)
else:result['status']='BLOCKED: original service still owns runtime';save();raise SystemExit(0)
result['status']='running_bounded_heldout_A_D';result['original_run']=str(run);save()
# No training/profile leakage: all tasks below are held-out diagnostic questions, not profiling input.
tasks=[
 ('python', 'Python: what is list(dict.fromkeys([3,1,3,2,1]))? Return only JSON {"answer": [...]}.',[3,1,2]),
 ('debugging','Find the bug in def f(xs): return sorted(xs).reverse(). Give the result of f([2,1]) as JSON {"answer": null} if None, otherwise the actual result.',None),
 ('navigation','Repository map: app/main.py imports core.engine; core/engine.py imports core.parser; core/parser.py defines parse(). Which file should be inspected first for a parse() bug? Return only JSON {"answer":"path"}.','core/parser.py'),
 ('tool','Call lookup_symbol with name="parse".',None),
]
server=None
try:
 for mode in ['baseline-no-cache','baseline-cache']:
  row={'placement':'A_default_no_expert_cache' if mode.endswith('no-cache') else 'D_existing_adaptive_SLRU_512MiB','started':now(),'trials':[]};result['cases'].append(row);save()
  log=(O/(mode+'.log')).open('w');began=time.monotonic()
  server=subprocess.Popen([str(D/'start-reap50.sh'),mode],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  deadline=time.monotonic()+240
  while True:
   if server.poll() is not None:raise RuntimeError('Benchmark launcher refused or failed; no fallback')
   try:
    if get('/health').get('status')=='ok':break
   except Exception:pass
   if time.monotonic()>deadline:raise TimeoutError('load readiness exceeded 240 seconds')
   time.sleep(2)
  row['load_seconds']=time.monotonic()-began
  done=threading.Event();samples=[]
  def sample():
   while not done.is_set():
    try:
     gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3).stdout.strip()
     proc=pathlib.Path('/proc')/str(server.pid);stat=(proc/'stat').read_text().split();mem={line.split(':')[0]:line.split(':')[1].strip() for line in (proc/'status').read_text().splitlines() if line.startswith(('VmRSS:','VmSwap:'))}
     samples.append({'monotonic':time.monotonic(),'gpu_used_free_util':gpu,'cpu_ticks':int(stat[13])+int(stat[14]),'process_memory':mem})
    except Exception:pass
    done.wait(2)
  thread=threading.Thread(target=sample,daemon=True);thread.start()
  try:
   for name,prompt,expected in tasks:
    body={'model':'nemotron-bolt-reap50-local','messages':[{'role':'user','content':prompt}],'temperature':0,'seed':42,'max_tokens':160,'cache_prompt':False}
    if name=='tool':body.update(tools=[{'type':'function','function':{'name':'lookup_symbol','description':'Look up symbol in an offline repository index','parameters':{'type':'object','properties':{'name':{'type':'string'}},'required':['name']}}}],tool_choice='required')
    started=time.monotonic();res=get('/v1/chat/completions',body);elapsed=time.monotonic()-started
    msg=res['choices'][0]['message'];ok=False
    try:
     if name=='tool':
      call=msg['tool_calls'][0]['function'];ok=call['name']=='lookup_symbol' and json.loads(call['arguments'])=={'name':'parse'}
     else:
      content=msg['content'].strip()
      if content.startswith('```'):content='\n'.join(content.splitlines()[1:-1])
      ok=json.loads(content)['answer']==expected
    except Exception:pass
    row['trials'].append({'task':name,'wall_seconds':elapsed,'correct':ok,'response':res});save()
  finally:done.set();thread.join(timeout=5);row['resources']=samples
  stop(server);server=None;log.close();row['finished']=now();save()
 result['status']='complete_requires_independent_review';save()
except Exception as e:result['status']='BLOCKED';result['error']=repr(e);save()
finally:stop(server)

if result["status"]=="complete_requires_independent_review":
 subprocess.run(["systemctl","--user","start","language-matrix-bolt-final.service"],check=True)
