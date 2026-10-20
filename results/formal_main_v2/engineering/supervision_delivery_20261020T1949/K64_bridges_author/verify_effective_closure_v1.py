import sys,json,hashlib,datetime
from pathlib import Path
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
cache={}
def h(p):
 p=Path(p);assert p.suffix.lower() not in ('.pt','.pth','.bin','.safetensors','.pkl','.pickle','.ckpt','.init','.pruned_init');assert not any(x.lower() in ('checkpoints','weights') for x in p.parts)
 if str(p) not in cache:
  q=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):q.update(b)
  cache[str(p)]=q.hexdigest()
 return cache[str(p)]
mp=D/'static_plan_publication_candidate.json';assert h(mp)=='d447aebff71f88bea0f568def97a5106936a7c107062062e7386758f8d6a30ca';rows=[]
for pair in json.loads(mp.read_text())['pairs']:
 ep=R/pair['effective_plan']['path'];assert h(ep)==pair['effective_plan']['sha256'];plan=json.loads(ep.read_text());inv=plan['invocation'];groups={'P_watched':inv['watched_files'],'P_support':{str(P/p):v for p,v in inv['support_files'].items()},'R_source_proof':{str(R/p):v for p,v in inv['root_evidence_sha256'].items()}}
 contract=json.loads((R/inv['action_execution_contract']['path']).read_text());groups['P_runtime_dependencies']={str(P/p):v for p,v in contract['runtime_contract']['dependencies'].items()}
 for files in groups.values():
  for name,pin in files.items():assert h(name)==pin,(name,pin,h(name))
 for item in pair['files']:
  for base in [R,P]:assert h(base/item['path'])==item['sha256']
 rows.append({'suite':pair['suite'],'effective_plan':pair['effective_plan'],'counts':{k:len(v) for k,v in groups.items()},'all_hashes_matched':True,'action_wrapper_admission':'pending exact root and independent readiness; base scientific verification is not runtime admission'})
o={'status':'passed_exact_effective_closure_bytes','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pairs':rows,'all_checked_paths':cache,'unique_nonweight_files':len(cache),'GPU_runs':0,'Slurm_calls':0,'weights_or_final_state_payloads_read':False,'scientific_trials':0}
p=D/'effective_closure_check.json';p.write_text(json.dumps(o,sort_keys=True,indent=2)+'\n');print(json.dumps({'path':p.relative_to(R).as_posix(),'sha256':h(p),'unique_nonweight_files':len(cache)}))
