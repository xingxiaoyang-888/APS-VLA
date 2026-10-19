
from pathlib import Path
import json,hashlib,sys,importlib.util
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261020T0227';D='results/formal_main_v2/execution/long_remaining16_action_v1_1827'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def ref(rel):return dict(path=rel,sha256=h(R/rel))
maprel='.local/long_action_outer_1827/publication_map.json';idxrel='.local/long_action_outer_1827/outer_index.json'
assert h(R/maprel)=='6fd6543dcb538335122ee369609e3ed68a2faaf9c1bdf33cca207890e9241f7f'
assert h(R/idxrel)=='e4c18587396f3f8cee3330bd01104a8db7ca3be38f6b28361e6f11cd425c5f22'
m=json.loads((R/maprel).read_text());idx=json.loads((R/idxrel).read_text());assert len(m['files'])==24 and len(idx['shards'])==8
ct=load('scripts/ops/formal_action_deployment_v1/contract.py','efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19','publish1827_contract')
byrel={v['canonical_path']:v for v in m['files']};assert len(byrel)==24
for row in m['files']:
 q=R/row['candidate']['path'];assert q.is_file() and not q.is_symlink() and h(q)==row['sha256']==row['candidate']['sha256'] and q.stat().st_size==row['bytes']
 assert row['canonical_path']==D+'/'+row['pair']+'/'+row['role']+'.json'
def candidate(rr):
 row=byrel[rr['path']];assert row['sha256']==rr['sha256'];return json.loads((R/row['candidate']['path']).read_text())
for sh in idx['shards']:
 sci=candidate(sh['scientific_plan']);eff=candidate(sh['effective_plan']);con=candidate(sh['action_execution_contract'])
 ct.validate_effective(sci,eff,scientific_plan_ref=sh['scientific_plan'],execution_contract_ref=sh['action_execution_contract'],execution_contract=con)
 assert not eff['invocation']['resume'] and not eff['invocation']['prior_job_ids'] and eff['invocation']['prior_review'] is None and con['transition'] is None
 assert eff['invocation']['suite']=='libero_10' and eff['invocation']['stage']=='development' and eff['invocation']['method_ids']==sh['method_ids']
 assert not (R/sh['invocation_relative']).exists() and not (P/sh['invocation_relative']).exists() and not Path(sh['run_root']).exists()
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','publish1827_controller')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);state=json.loads(sp.read_text());assert state['pending_submission'] is None
 for row in m['files']:
  for base in [R,P]:
   out=base/row['canonical_path'];assert not out.exists(),str(out)
 rows=[]
 for row in m['files']:
  raw=(R/row['candidate']['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
  for base in [R,P]:
   out=base/row['canonical_path'];out.parent.mkdir(parents=True,exist_ok=True)
   with out.open('xb') as f:f.write(raw)
   assert h(out)==row['sha256']
  rows.append(dict(source=row['candidate'],path=row['canonical_path'],sha256=row['sha256'],bytes=row['bytes'],R_present_exact=True,P_present_exact=True))
 assert before==h(sp)
 out=R/B/'Long_outer_candidate_publication.json'
 with out.open('x') as f:json.dump(dict(schema='formal_main_v2',status='published_exact_candidate_metadata_only',utc=datetime.now(timezone.utc).isoformat(),publication_map=ref(maprel),outer_index=ref(idxrel),files=rows,root_validate_effective_passed=8,state_unchanged=True,no_invocation_published=True,no_authorization_or_readiness=True,new_GPU_submissions=[]),f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(receipt=out.relative_to(R).as_posix(),sha256=h(out),files=len(rows),R_and_P=True,invocation_or_submission=False)))
