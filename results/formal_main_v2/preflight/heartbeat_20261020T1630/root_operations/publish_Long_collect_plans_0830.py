from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1630';D='.local/long_collection_prepare_0830/a2';O='results/formal_main_v2/execution/long_collect_action_v1_0830'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
p=R/D/'publication_map.json';assert h(p)=='391b030df7fdda0030ed3054bd9e7139ef41886bdb1444f1c1a06bf407b4c1cf'
mapping=json.loads(p.read_bytes())['files']
new={'scientific_plan.json':'1c50e85dfea3042cb7cee74cf5482e2325e4036e0bc7a74187d0061983790ee0','execution_contract.json':'06ca8c538a323e14ad8197a80e9cc5c39d303976adbd8959630e535b11b1acc0','effective_plan.json':'1ce34d9ecf18e36d2c0043e2fdfd42ca327344d286fb35704fdfe70e8b5ed8ac'}
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('publishplans0830',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);s=json.loads(state.read_bytes())
 assert s['pending_submission'] is None
 assert not any(j.get('suite')=='libero_10' and (j.get('mode') in ['collect','full','components'] or j.get('stage') in ['collect','full','components']) for j in s['registered_jobs'])
 missing=[]
 for row in mapping:
  rel=row['canonical_path'];p=R/row['candidate_path'];assert h(p)==row['sha256'] and p.stat().st_size==row['bytes']
  for base in [R,P]:
   dest=base/rel
   if dest.exists():assert h(dest)==row['sha256'] and dest.stat().st_size==row['bytes']
   else:
    assert Path(rel).parent==Path(O) and Path(rel).name in new and new[Path(rel).name]==row['sha256']
    assert row['candidate_path']==D+'/'+Path(rel).name;missing.append((p,dest))
 assert len(missing)==6
 plan=json.loads((R/D/'effective_plan.json').read_bytes())
 assert not (P/plan['output_relative']).exists() and not (R/plan['invocation_relative']).exists() and not (P/plan['invocation_relative']).exists()
 for src,dest in missing:
  with dest.open('xb') as f:f.write(src.read_bytes())
 assert h(state)==before
 proof=dict(schema='formal_main_v2',kind='root_publish_exact_collection_plan_dependencies',status='published_static_inputs_not_execution_authorization',utc=datetime.now(timezone.utc).isoformat(),publication_map=ref(D+'/publication_map.json'),copied=[dict(source=str(a.relative_to(R)),target=str(b),sha256=h(b)) for a,b in missing],all_declared_existing_R_P_inputs_verified=True,state_unchanged=True,new_GPU_submissions=0,full_and_final_not_authorized=True)
 q=R/B/'Long_collect_plan_publication.json'
 with q.open('x') as f:json.dump(proof,f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps(dict(receipt=ref(q.relative_to(R).as_posix()),status=proof['status'])))
