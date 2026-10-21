import json,pathlib,subprocess,hashlib,shutil,datetime
D=pathlib.Path(__file__).parent
manifest=json.loads((D/'manifest.json').read_text());status={}
def save(): (D/'download-status.json').write_text(json.dumps(status,indent=2)+'\n')
for m in reversed(manifest):
 p=pathlib.Path(m['path']);part=p.with_name(p.name+'.part');p.parent.mkdir(parents=True,exist_ok=True)
 remaining=m['bytes']-(part.stat().st_size if part.exists() else 0)
 if not p.exists():
  if shutil.disk_usage(p.parent).free < remaining+4*2**30:raise RuntimeError('Insufficient space with4GiBreserve: '+str(p.parent))
  status[m['filename']]={'status':'downloading','expected_bytes':m['bytes'],'path':str(p),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};save()
  subprocess.run(['curl','--fail','--location','--retry','5','--retry-delay','5','--continue-at','-','--limit-rate','12M','--output',str(part),m['url']],check=True)
 else:part=p
 if part.stat().st_size!=m['bytes']:raise RuntimeError('Wrong byte count: '+str(part))
 h=hashlib.sha256()
 with part.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 if h.hexdigest()!=m['sha256']:raise RuntimeError('Checksum mismatch: '+str(part))
 if part!=p:part.rename(p)
 status[m['filename']]={'status':'verified','bytes':m['bytes'],'sha256':h.hexdigest(),'path':str(p),'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};save()
(D/'download-completed.txt').write_text(datetime.datetime.now(datetime.timezone.utc).isoformat()+'\n')
