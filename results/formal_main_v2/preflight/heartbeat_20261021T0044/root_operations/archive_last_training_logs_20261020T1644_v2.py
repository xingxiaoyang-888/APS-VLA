from pathlib import Path
import hashlib,importlib.util,json,sys,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def put(p,b):
 assert p.is_relative_to(R) and not any(z.is_symlink() for z in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n'.replace('\\n','\n')).encode()
def save(n,v):put(R/n,(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+chr(10)).encode());return ref(R/n)
def mod(n,pin,name):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','archiveLast1644ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 m=mod('scripts/ops/nonweight_archive.py','f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2','archiveLast1644codec')
 old=R/'results/formal_main_v2/nonweight_archives/v1/snapshots/Goal64seed41_20261020T1530.json';assert h(old)=='caf74020b7a320bf41fb975ec8a8dcd10b54d9dc800ac51c28cd61d027ee341c'
 raw=[{k:x[k] for k in ['path','sha256','bytes']} for x in json.loads(old.read_bytes())['files']];previous=json.loads(old.read_bytes());previous_request=previous['request'];assert h(R/previous_request['path'])==previous_request['sha256'];provenance=[previous_request]
 for n,pin,pair in [('results/formal_main_v2/pulls/20261020T170126Z_1fd1cd88b439/receipt.json','f0633ec7db1a6f09aa92afb332d452e91f81c9d69c6c356bf27df45bdb338036','libero_goal/k64/seed23'),('results/formal_main_v2/pulls/20261020T175321Z_d93105850084/receipt.json','892b66bae4074e0a88712113233ea10da4c05e39cb8a8f9c014e2d34f9ff1b06','libero_object/k64/seed23')]:
  pp=R/n;assert h(pp)==pin;pull=json.loads(pp.read_bytes());assert pull['status']=='verified_nonweight_snapshot';provenance.append(ref(pp))
  rows=[x for x in pull['files'] if x['relative'].startswith('results/formal_main_v2/'+pair+'/training/') and x['bytes']>20*(1<<20)];assert len(rows)==3
  for row in rows:
   q=R/row['relative'];rr=ref(q);assert q.suffix=='.jsonl' and rr['sha256']==row['sha256'] and rr['bytes']==row['bytes'];raw.append(rr)
 assert len(raw)==9 and len({x['path'] for x in raw})==9
 request=save(B+'/last_training_lossless_archive_request_v2.json',dict(schema=m.SCHEMA,kind='archive_request',files=raw,provenance=provenance));snap='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json';result=m.pack(R,request['path'],snap);assert result['status']=='packed_verified' and result['original_bytes']==sum(x['bytes'] for x in raw)
 ip=R/'.gitignore';original=ip.read_text();added=['/'+x['path'] for x in raw if '/'+x['path'] not in original.splitlines()]
 if added:ip.write_text(original+chr(10)+'# Lossless raw training evidence, root verified 20261020T1644.'+chr(10)+chr(10).join(added)+chr(10))
 out=save(B+'/last_training_lossless_archive.json',dict(status='packed_verified_originals_retained',snapshot=ref(R/snap),request=request,raw=raw,result=result,all_costs_already_ledgered=True,new_GPU_jobs=0))
 assert h(R/'results/experiment_supervisor/state.json')==before
 print(json.dumps(dict(lossless=out,snapshot=ref(R/snap),raw_files=9,original_bytes=result['original_bytes'])),flush=True)
