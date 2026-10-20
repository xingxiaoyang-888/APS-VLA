from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';D='results/formal_main_v2/execution/object256seed23_source_control_v1_20261020T1644'
BUNDLE='.local/object_bridge_production_20261020T1644/production_candidates01/plan_bundle.json';PIN='52368d3b96e72ec4deb601949a7133579327818a6a7e963ca4657892bb36dfad'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def mod(n,pin,label):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(label,p);m=importlib.util.module_from_spec(sp);sys.modules[label]=m;sp.loader.exec_module(m);return m
def put(n,b):
 p=R/n;assert p.is_relative_to(R) and '..' not in p.parts and not any(z.is_symlink() for z in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
assert h(R/BUNDLE)==PIN;data=rd(BUNDLE);assert data['status']=='canonical_control_CPU_checked_static_plans_unpublished' and data['expected_trials']==200 and data['unique_development_initial_states']==100
ctrl=mod('scripts/ops/formal_object256s23_source_bridge_v1/control.py','09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f','publishObjectPlan1644control');g=ctrl.gateway_module()
c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'publishObjectPlan1644controller')
assert data['explicit_source_control']==ctrl.descriptor() and data['gateway_files']==ctrl.closure()
ind='.local/object_bridge_production_independent_20261020T1644/canonical/gateway_independent_CPU_review.json';assert h(R/ind)=='e5199302d6d18cd2ea097fe4a5a7a0f0631cac1f49dccc87b5dc2c93374b02aa'
iv=rd(ind);assert iv['status']=='passed_CPU_review' and not iv['blockers'] and all(iv['files'].get(k)==v for k,v in ctrl.closure().items())
rows=data['canonical_files'];assert len(rows)==4 and {x['destination'] for x in rows}=={D+'/'+n for n in ['scientific_plan.json','effective_plan.json','execution_contract.json','plan_arguments.json']}
for x in rows:
 assert x['source'].startswith('.local/object_bridge_production_20261020T1644/production_candidates01/') and h(R/x['source'])==x['sha256'] and (R/x['source']).stat().st_size==x['bytes']
science=json.loads((R/rows[0]['source']).read_bytes());effective=rd('.local/object_bridge_production_20261020T1644/production_candidates01/effective_plan.json')
ctrl.scope_invocation(science['invocation']);ctrl.scope_invocation(effective['invocation']);assert effective['plan_sha256']==data['plan_sha256']
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=rd(g.STATE);before=h(R/g.STATE);assert state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0
 assert state['formal_main_progress']['root_and_independent_completed_arms']==68 and not state['formal_main_progress']['global_release_created']
 assert not (R/science['invocation_relative']).exists() and not (ctrl.P/science['invocation_relative']).exists() and not Path(science['invocation']['run_root']).exists()
 assert not any(j.get('stage_key')==science['invocation']['stage_key'] for j in state['registered_jobs'])
 for x in rows:put(x['destination'],(R/x['source']).read_bytes())
 assert h(R/g.STATE)==before
 result=dict(schema='formal_main_v2',status='source_bound_static_metadata_published_no_GPU_or_admission',utc=datetime.now(timezone.utc).isoformat(),bundle=ref(BUNDLE),canonical_gateway_CPU=ref(ind),files=[ref(x['destination']) for x in rows],explicit_source_control=ctrl.descriptor(),state_sha256=before,state_unchanged=True,expected_trials=200,unique_development_initial_states=100,final_sealed=True,new_GPU_submissions=[],runtime_readiness_created=False)
 out=B+'/Object_static_plan_publication.json';put(out,(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode().replace(b'\\n',b'\n') if False else (json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+chr(10)).encode())
 print(json.dumps(dict(receipt=ref(out),published_files=4,new_GPU=0)),flush=True)
