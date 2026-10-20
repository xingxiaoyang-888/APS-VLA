from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1644'
PACKAGES=[('.local/Goal64s41_independent_20261020T1644','090d03a9405db48491acd7535c121d903dfe6484586be385df7fb599ebda2c53','Goal64s41_training_independent'),('.local/object_bridge_independent_20261020T1644','cda41447efd3fd0a995e2f8672972b80d2645c950b222f8a9e5de98b79a85c33','Object_source_bridge_independent'),('.local/goal_t0_forensic_20261020T1644','1213710aebda4ce16e3727328ce8d46de8b00bd94c3dca4401ca6e90d05401b2','Goal_t0_forensic')]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def put(p,b):
 assert p.is_relative_to(R) and not any(x.is_symlink() for x in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('archiveEvidence1644',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);copies=[];packages=[]
 for private,pin,label in PACKAGES:
  root=R/private;m=root/'delivery_manifest.json';assert h(m)==pin
  data=json.loads(m.read_bytes());raw=data['files'];rows=raw if isinstance(raw,list) else [dict(path=(root/n).relative_to(R).as_posix(),**v) for n,v in raw.items()]
  paths=set()
  for row in rows:
   q=R/row['path'];assert q.is_relative_to(root) and h(q)==row['sha256'] and q.stat().st_size==row['bytes'];paths.add(q)
  assert len(paths)==len(rows) and {p for p in root.rglob('*') if p.is_file()}==paths|{m}
  for q in sorted(paths|{m}):
   assert q.is_file() and not any(p.is_symlink() for p in [q,*q.parents]) and q.stat().st_size<100*(1<<20)
   assert q.suffix not in ('.pt','.pth','.ckpt','.bin','.safetensors','.pyc','.init','.npz','.npy','.h5','.hdf5')
   dst=R/E/label/q.relative_to(root);put(dst,q.read_bytes());assert h(dst)==h(q);copies.append(dict(source=ref(q),archive=ref(dst)))
  for row in data.get('external_execution_logs',[]):assert h(R/row['path'])==row['sha256'] and (R/row['path']).stat().st_size==row['bytes']
  packages.append(dict(private_manifest=ref(m),archive_manifest=ref(R/E/label/'delivery_manifest.json'),files=len(paths)+1))
 assert h(state)==before
 out=R/B/'evidence_delivery_initial.json';put(out,enc(dict(schema='formal_main_v2',status='exact_complete_nonweight_packages_archived',packages=packages,copies=copies,files=len(copies),bytes=sum(x['source']['bytes'] for x in copies),root_state_unchanged=True,new_GPU_jobs=0,Goal_original200_HOLD=True,Object_production_bridge_admitted=False,sealed_values_read=False)))
 print(json.dumps(dict(receipt=ref(out),files=len(copies))),flush=True)
