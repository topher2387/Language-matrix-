import pathlib,subprocess,time,json,urllib.request,datetime
D=pathlib.Path(__file__).parent
status={'status':'waiting_for_existing_matrix_and_heldout','created':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save(): (D/'queue-status.json').write_text(json.dumps(status,indent=2)+'\n')
save();deadline=time.monotonic()+16000
while time.monotonic()<deadline:
 services=['language-matrix-reap50-125k-matrix.service','language-matrix-reap50-125k-heldout.service']
 if all(subprocess.run(['systemctl','--user','is-active',s],capture_output=True,text=True).stdout.strip()!='active' for s in services):break
 time.sleep(15)
else:status['status']='BLOCKED: preceding tests did not finish within bounded wait';save();raise SystemExit()
try:
 # Refuse to interrupt newly started interactive work. /slots is a read-only owner check.
 idle_verified=False
 for _ in range(90):
  req=urllib.request.Request('http://127.0.0.1:11438/slots',headers={'Authorization':'Bearer local-only'})
  try:
   with urllib.request.urlopen(req,timeout=5) as r:slots=json.load(r)
   if any(slot.get('is_processing',False) for slot in slots):raise RuntimeError('interactive model is busy; no interruption')
   idle_verified=True;break
  except urllib.error.HTTPError as e:
   if e.code!=503:raise
   time.sleep(2)
  except urllib.error.URLError:
   # A stopped server has no interactive requests to interrupt.
   service=subprocess.run(['systemctl','--user','is-active','language-matrix-bolt-final.service'],capture_output=True,text=True).stdout.strip()
   if service not in ('active','activating'):idle_verified=True;break
   time.sleep(2)
 if not idle_verified:raise RuntimeError('cannot verify readiness/idle within180seconds')
 subprocess.run(['systemctl','--user','stop','language-matrix-bolt-final.service'],check=True)
 status['status']='running_experimental_draft_matrix';save()
 code=subprocess.run(['/usr/bin/python3',str(D/'run-matrix.py')],timeout=31000).returncode
 status.update(status='finished_requires_independent_review',exit_code=code);save()
finally:
 # Restore only the requested trimmed interactive server, never a coding assignment.
 subprocess.run(['systemctl','--user','start','language-matrix-bolt-final.service'])
