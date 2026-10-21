"""Sequential local-only benchmark. Owns only the servers it launches."""
import datetime,json,os,pathlib,signal,subprocess,time,urllib.request
D=pathlib.Path(__file__).parent;run=D/'runs'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');run.mkdir(parents=True);state={'run':str(run),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':[]};(D/'active-run.txt').write_text(str(run)+'\n')
def save(): (run/'status.json').write_text(json.dumps(state,indent=2)+'\n')
def stop(p):
 if p is None:return
 if p.poll() is None:
  os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=30)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def job(cmd,log,timeout):
 with log.open('w') as f:
  p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:return p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:stop(p);return 124
server=None
try:
 for case in json.loads((D/'benchmark-matrix.json').read_text())['cases']:
  name=case['name'];label=run.name+'-'+name;out=run/name;out.mkdir();row={'case':name,'status':'loading','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};state['cases'].append(row);save();began=time.monotonic()
  with (out/'server.log').open('w') as log:
   server=subprocess.Popen([str(D/'start-reap50.sh'),name],stdout=log,stderr=subprocess.STDOUT,start_new_session=True);row['server_pid']=server.pid;save()
   ready=False
   for _ in range(300):
    if server.poll() is not None:break
    try:
     with urllib.request.urlopen('http://127.0.0.1:11438/health',timeout=2) as r:ready=json.load(r).get('status')=='ok'
     if ready:break
    except Exception:pass
    time.sleep(2)
   row['load_seconds']=round(time.monotonic()-began,3)
   if not ready:row['status']='load_failed';row['server_exit']=server.poll();stop(server);server=None;save();continue
   req=urllib.request.Request('http://127.0.0.1:11438/props',headers={'Authorization':'Bearer local-only'})
   with urllib.request.urlopen(req,timeout=10) as r:props=json.load(r)
   (out/'props.json').write_text(json.dumps(props,indent=2));row['resolved_context']=props['default_generation_settings']['n_ctx'];row['status']='large_prompt_first_and_warm_trials';save()
   row['status']='compatibility_code_and_tools';save()
   row['compatibility_exit']=job(['/usr/bin/python3',str(D/'benchmark.py'),label+'-compatibility'],out/'compatibility.log',300)
   evidence=D/'results'/(label+'-compatibility.json')
   checked=json.loads(evidence.read_text()) if evidence.exists() else {}
   if row['compatibility_exit']!=0 or not checked.get('coding_pass') or not checked.get('tool_pass'):
    row['status']='compatibility_failed_no_large_test';stop(server);server=None;row['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();continue
   # Preserve matched fresh-process first-prefill measurement after the compatibility probe.
   stop(server);server=None;began=time.monotonic()
   server=subprocess.Popen([str(D/'start-reap50.sh'),name],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
   ready=False
   for _ in range(300):
    if server.poll() is not None:break
    try:
     with urllib.request.urlopen('http://127.0.0.1:11438/health',timeout=2) as r:ready=json.load(r).get('status')=='ok'
     if ready:break
    except Exception:pass
    time.sleep(2)
   row['fresh_large_load_seconds']=round(time.monotonic()-began,3)
   if not ready:
    row['status']='fresh_large_load_failed';stop(server);server=None;save();continue
   row['status']='large_prompt_first_and_warm_trials';save()
   row['large_prompt_exit']=job(['/usr/bin/python3',str(D/'benchmark-large.py'),label],out/'large-prompt.log',15000)
   if server.poll() is None:
    row['status']='code_and_tools';save();row['smoke_exit']=job(['/usr/bin/python3',str(D/'benchmark.py'),label],out/'code-tools.log',1800)
   else:row['smoke_exit']=None
   row['status']='finished_requires_review' if row.get('large_prompt_exit')==0 and row.get('smoke_exit')==0 else 'failed_or_incomplete'
   stop(server);server=None;row['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
 state['status']='all_cases_attempted_requires_independent_review';state['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
finally:stop(server)
