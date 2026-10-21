"""One first full prefill, three warm full prefills, three cached-prefix trials.
Run immediately after loading a fresh trimmed REAP50 Bolt server; no model calls precede it.
"""
import argparse,datetime,hashlib,json,pathlib,random,statistics,time,urllib.request,subprocess,threading

def post(base,path,body,timeout=120):
 req=urllib.request.Request(base+path,json.dumps(body).encode(),{'Content-Type':'application/json','Authorization':'Bearer local-only'})
 return urllib.request.urlopen(req,timeout=timeout)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('label');ap.add_argument('--base',default='http://127.0.0.1:11438');ap.add_argument('--target-input',type=int,default=108000);ap.add_argument('--warm-repeats',type=int,default=3);a=ap.parse_args()
 if not 1000<=a.target_input<=108000 or not 1<=a.warm_repeats<=5:raise ValueError('Keep input<=108000 and1..5repeats')
 if not a.label.replace('-','').isalnum():raise ValueError('Label must be alphanumeric/hyphens')
 D=pathlib.Path(__file__).parent/'results'/a.label;D.mkdir(parents=True,exist_ok=True)
 with urllib.request.urlopen(urllib.request.Request(a.base+'/props',headers={'Authorization':'Bearer local-only'})) as r:props=json.load(r)
 assert props['model_alias']=='nemotron-bolt-reap50-local','Wrong server/model'
 ctx=props['default_generation_settings']['n_ctx'];assert ctx>=125000,'Expected125Kcontext'
 rng=random.Random(20261020);lines=[f'Record {i:05d}: inventory={rng.randrange(10**8):08d}; offline fixture text for context timing only.\n' for i in range(8000)]
 start='START_MARKER=otter-7381\n';end='\nEND_MARKER=maple-9462\nReturn only the START_MARKER and END_MARKER values, in that order.'
 def content(n):return start+''.join(lines[:n])+end
 def count(n):
  with post(a.base,'/tokenize',{'content':content(n),'add_special':True}) as r:return len(json.load(r)['tokens'])
 lo,hi=0,len(lines)
 while lo<hi:
  mid=(lo+hi+1)//2
  if count(mid)<=a.target_input:lo=mid
  else:hi=mid-1
 prompt=content(lo);n=count(lo)
 if n<a.target_input-500:raise ValueError('Prompt generation failed to approach token target')
 meta={'label':a.label,'configured_context':ctx,'input_content_tokens':n,'input_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'prompt_records':lo,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'note':'First means fresh model process/context; OS filesystem pages may already be warm. Tokenization does not run model inference. No global OS cache flushing.'};(D/'metadata.json').write_text(json.dumps(meta,indent=2))
 samples=[];done=threading.Event()
 def sample():
  while not done.is_set():
   try:
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.free','--format=csv,noheader,nounits'],text=True,timeout=5).splitlines()[0]
    used,free=[int(v.strip()) for v in gpu.split(',')];mem={line.split(':')[0]:int(line.split()[1]) for line in pathlib.Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemAvailable:','SwapFree:'))};samples.append({'time':time.time(),'gpu_used_mib':used,'gpu_free_mib':free,**mem})
   except Exception as e:samples.append({'time':time.time(),'sampling_error':repr(e)})
   done.wait(2)
 thread=threading.Thread(target=sample,daemon=True);thread.start()
 results=[]
 phases=[('first_full_prefill',False)]+[(f'warm_full_prefill_{i+1}',False) for i in range(a.warm_repeats)]+[(f'warm_prefix_reuse_{i+1}',True) for i in range(a.warm_repeats)]
 for name,cache in phases:
  body={'model':'nemotron-bolt-reap50-local','messages':[{'role':'user','content':prompt}],'max_tokens':512,'temperature':0,'seed':42,'stream':True,'stream_options':{'include_usage':True},'cache_prompt':cache,'id_slot':0}
  began=time.monotonic();first=None;text='';timings={};usage={};finish=None
  try:
   with post(a.base,'/v1/chat/completions',body,timeout=7200) as r:
    for raw in r:
     if not raw.startswith(b'data:'):continue
     data=raw[5:].strip()
     if data==b'[DONE]':break
     x=json.loads(data)
     if x.get('error'):raise RuntimeError(str(x['error']))
     if x.get('timings'):timings=x['timings']
     if x.get('usage'):usage=x['usage']
     for choice in x.get('choices',[]):
      piece=choice.get('delta',{}).get('content') or ''
      if piece:
       if first is None:first=time.monotonic()-began
       text+=piece
      if choice.get('finish_reason'):finish=choice['finish_reason']
   row={'phase':name,'cache_prompt':cache,'wall_seconds':time.monotonic()-began,'time_to_first_content_seconds':first,'timings':timings,'usage':usage,'finish_reason':finish,'content':text,'markers_pass':all(v in text for v in ['otter-7381','maple-9462'])}
   row['unreused_prefill_confirmed']=timings.get('cache_n')==0 if not cache else None
   row['prefix_reuse_observed']=timings.get('cache_n',0)>0 if cache else None
  except Exception as e:
   row={'phase':name,'cache_prompt':cache,'wall_seconds':time.monotonic()-began,'error':repr(e)}
  results.append(row);(D/'trials.json').write_text(json.dumps(results,indent=2));print(json.dumps(row),flush=True)
  if row.get('error'):
   done.set();thread.join(timeout=6);(D/'resources.json').write_text(json.dumps(samples,indent=2));raise SystemExit(1)
 done.set();thread.join(timeout=6);(D/'resources.json').write_text(json.dumps(samples,indent=2))
 warm=[r['wall_seconds'] for r in results if r['phase'].startswith('warm_full')];cached=[r['wall_seconds'] for r in results if r['phase'].startswith('warm_prefix')]
 summary={'first_full_seconds':results[0]['wall_seconds'],'warm_full_median_seconds':statistics.median(warm),'warm_prefix_median_seconds':statistics.median(cached),'peak_gpu_used_mib':max((r.get('gpu_used_mib',0) for r in samples),default=None),'minimum_mem_available_kib':min((r['MemAvailable'] for r in samples if 'MemAvailable' in r),default=None),'all_markers_pass':all(r.get('markers_pass') for r in results),'all_unreused_prefills_confirmed':all(r['unreused_prefill_confirmed'] is True for r in results if not r['cache_prompt']),'note':'Cache reuse must be confirmed by timings; recurrent/SSM models may reprocess prefixes. Do not label missing telemetry or failed recall as a pass.'};(D/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
