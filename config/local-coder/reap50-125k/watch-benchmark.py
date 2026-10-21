#!/usr/bin/env python3
"""Read-only terminal dashboard; never issues model inference requests."""
import pathlib,json,time,re,subprocess,argparse
D=pathlib.Path('/home/topher/Language-matrix-coder/reap50-125k-setup')
def tail(p,n=100):
 try:
  with p.open('rb') as f:f.seek(0,2);f.seek(max(0,f.tell()-65536));s=f.read().decode(errors='replace')
  return s.splitlines()[-n:]
 except OSError:return []
def number(v,d=1):return 'pending' if v is None else f'{v:.{d}f}'
def render():
 run=pathlib.Path((D/'active-run.txt').read_text().strip());state=json.loads((run/'status.json').read_text());cases=state.get('cases',[]);c=cases[-1] if cases else {};name=c.get('case','starting');folder=run/name
 rp=D/'results'/(run.name+'-'+name)/'trials.json';trials=json.loads(rp.read_text()) if rp.exists() else [];phases=['FIRST full prompt','WARM full prompt 1/3','WARM full prompt 2/3','WARM full prompt 3/3','PREFIX reuse 1/3','PREFIX reuse 2/3','PREFIX reuse 3/3'];phase=phases[len(trials)] if len(trials)<7 else 'Large-prompt trials finished'
 rows=['TRIMMED REAP50 BOLT | LIVE BENCHMARK | '+time.strftime('%H:%M:%S %Z'),'='*105,'Configuration: '+name+'    Context: '+str(c.get('resolved_context','loading')),'Trial: '+phase+'    Runner: '+c.get('status','starting')]
 try:rows+=['VRAM used / free / GPU utilization: '+subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.free,utilization.gpu','--format=csv,noheader'],text=True,timeout=3).strip()]
 except Exception:pass
 lines=tail(folder/'server.log');events=[z for z in lines if any(k in z for k in ['prompt processing','n_gen =','eval time =','stop processing:'])];last=events[-1] if events else ''
 rows+=['','CURRENT ACTIVITY']
 if 'prompt processing' in last:
  m=re.search(r'n_tokens\s*=\s*(\d+), progress\s*=\s*([\d.]+).*?/\s*([\d.]+) tokens per second',last)
  rows+=['PROCESSING INPUT — no answer tokens are being generated yet.']
  if m:rows+=[f'Input processed: {int(m[1]):,} tokens | progress: {float(m[2])*100:.0f}% | INPUT speed: {float(m[3]):.2f} tokens/sec']
 elif 'n_gen =' in last:
  m=re.search(r'n_gen\s*=\s*(\d+), tg\s*=\s*([\d.]+)',last);rows+=['GENERATING OUTPUT']
  if m:rows+=[f'Answer tokens so far: {m[1]} | OUTPUT speed: {float(m[2]):.2f} tokens/sec']
 else:rows+=['Between updates / starting next phase. Completed measurements are below.']
 if trials:
  r=trials[-1];t=r.get('timings',{});rows+=['',f"LAST COMPLETED OUTPUT: {t.get('predicted_n','?')} tokens in {number(t.get('predicted_ms',0)/1000,3)} sec | OUTPUT speed: {number(t.get('predicted_per_second'),2)} tokens/sec",'Short marker answers can finish in <1 second; this line keeps that measurement visible.']
 rows+=['','COMPLETED TRIALS — INPUT AND OUTPUT ARE DIFFERENT MEASUREMENTS',f"{'Trial':<25} {'Input tok/s':>11} {'Input sec':>11} {'Output tok/s':>12} {'Out tokens':>11} {'Wall sec':>10} {'Recall':>8}"]
 for r in trials:
  t=r.get('timings',{});rows.append(f"{r['phase']:<25} {number(t.get('prompt_per_second'),2):>11} {number(t.get('prompt_ms',0)/1000):>11} {number(t.get('predicted_per_second'),2):>12} {str(t.get('predicted_n','?')):>11} {number(r.get('wall_seconds')):>10} {str(r.get('markers_pass')):>8}")
 if not trials:rows+=['Waiting for first complete answer.']
 rows+=['','Baseline-no-cache intentionally leaves expert-cache VRAM unused. Further cache tuning follows this matrix.','Cached-prefix trials measure skipped input separately from warm full prompt processing.','','MATRIX:']+[f"  {x['case']}: {x['status']}" for x in cases]
 rows+=['','Read-only local monitor; refresh 3 sec. Closing it does not stop the benchmark.'];return '\n'.join(rows)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--once',action='store_true');a=ap.parse_args()
 while True:
  try:print(('' if a.once else '\033[2J\033[H')+render(),flush=True)
  except KeyboardInterrupt:break
  except Exception as e:print('Waiting for live status:',e,flush=True)
  if a.once:break
  time.sleep(3)
