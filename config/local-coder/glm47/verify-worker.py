import importlib.util,random,json,pathlib,subprocess,time
D=pathlib.Path(__file__).parent;(D/'results').mkdir(exist_ok=True);W=D/'worker-benchmark';r=subprocess.run(['python3','-B','-m','unittest','-v'],cwd=W,capture_output=True,text=True,timeout=30)
spec=importlib.util.spec_from_file_location('worker_ranges',W/'ranges.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rng=random.Random(20261020);n=0
for _ in range(500):
 a=[]
 for j in range(rng.randrange(20)):
  x,y=sorted([rng.randrange(-30,31),rng.randrange(-30,31)]);a.append((x,y))
 original=a.copy();points=sorted({v for x,y in a for v in range(x,y+1)});expected=[]
 for v in points:
  if expected and expected[-1][1]+1==v:expected[-1]=(expected[-1][0],v)
  else:expected.append((v,v))
 assert m.merge_ranges(a)==expected,(a,expected,m.merge_ranges(a));assert a==original;n+=1
out={'unit_exit_code':r.returncode,'unit_output':r.stdout+r.stderr,'independent_random_cases':n,'pass':r.returncode==0};(D/'results/worker-verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
