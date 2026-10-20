from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';D='scripts/ops/formal_object256s23_source_bridge_v1'
M='.local/object_bridge_production_20261020T1644/revision03/source_publication_manifest.json';MSHA='bedb0c936461dad237dfca1683db2a0dcd5875eeb81a4de5300ebb1e59eb3831'
CSHA='09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel):return json.loads((R/rel).read_bytes())
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def put(p,raw):
 assert p.is_relative_to(R) and not any(x.is_symlink() for x in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
def save(p,x):put(p,(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+chr(10)).encode())
def module(name,rel,pin):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
assert h(R/M)==MSHA;m=rd(M);ar=m['author_CPU_report'];assert h(R/ar['path'])==ar['sha256']=='e9ab6afe555231c300809288a1d3daf3f31a9996b3523ba049f264bb4800a822';a=rd(ar['path'])
assert a['checks']==764 and a['negative_cases']==38 and a['actual_FrozenPlan_rebuild'] and a['actual_terminal_science_context_rebuild'] and a['GPU_runs']==a['Slurm_calls']==0
assert a['all_pair_GPU_seconds']==58917 and a['failed_GPU_seconds_retained']==84 and m['scientific_admission'] is False
assert {x['destination'] for x in m['files']}=={D+'/'+n for n in ['control.py','bridge_v2.py','policy_v1.json','README.md']} and len(m['files'])==4
inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';assert h(R/inventory)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926';iv=rd(inventory);assert len(iv['files'])==173
c=module('pubObject1644ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);raw=state.read_bytes();s=json.loads(raw)
 assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None
 assert s['formal_main_progress']['root_and_independent_completed_arms']==68 and not s['formal_main_progress']['test_opened']
 for base in [R,Path(iv['source_root_server'])]:
  for rel,pin in iv['files'].items():assert h(base/rel)==pin
 copied=[]
 for row in m['files']:
  src=R/row['source'];dst=R/row['destination'];assert src.is_relative_to(R/'.local/object_bridge_production_20261020T1644/revision03/package') and h(src)==row['sha256'] and src.stat().st_size==row['bytes']
  put(dst,src.read_bytes());copied.append(dict(source=ref(src),published=ref(dst)))
 control=module('pubObject1644control',D+'/control.py',CSHA);descriptor=control.descriptor();g=control.gateway_module();assert g.source_files(R)==descriptor['files']
 assert descriptor['scope']['method_ids']==['A256_seed23','B256_seed23'] and descriptor['scope']['trials']==200 and descriptor['all_pair_GPU_seconds']==58917
 assert h(state)==before
 for base in [R,Path(iv['source_root_server'])]:
  for rel,pin in iv['files'].items():assert h(base/rel)==pin
 snapshot=R/B/'Object_source_root_state_snapshot.json';put(snapshot,raw)
 out=R/B/'Object_source_publication.json';save(out,dict(schema='formal_main_v2',status='source_only_published_pending_canonical_root_independent_readiness',utc=datetime.now(timezone.utc).isoformat(),manifest=dict(path=M,sha256=MSHA),author_CPU_review=ar,copies=copied,root_state_snapshot=ref(snapshot),source_descriptor=descriptor,full173_unchanged_in_R_and_S=True,state_unchanged=True,root_and_independent_readiness_passed=False,scientific_admission=False,new_GPU_jobs=0,final_sealed=True))
 print(json.dumps(dict(receipt=ref(out),root_state_snapshot=ref(snapshot),source_only=True,canonical_control_sha256=CSHA,new_GPU=0)),flush=True)
