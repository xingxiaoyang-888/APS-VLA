from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0349';M='.local/k64_seed23_bridges_20261020T1949/static_plan_publication_candidate.json';PIN='d447aebff71f88bea0f568def97a5106936a7c107062062e7386758f8d6a30ca'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_bytes())
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('planpub1949ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);s=rd(state);assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 assert h(R/M)==PIN;m=rd(R/M);assert m['not_submitted'] is True and m['kind']=='k64_seed23_exact_two_development_plans_CPU_candidate' and len(m['pairs'])==2
 intent=[]
 for name,pair in zip(['spatial','object'],m['pairs']):
  assert pair['suite']=='libero_'+name and pair['methods']==['A64_seed23','B64_seed23'] and len(pair['files'])==5 and pair['not_an_authorization'] is True
  prefix='results/formal_main_v2/execution/'+name+'64seed23_source_control_v1_20261020T1949/'
  assert {v['path'].removeprefix(prefix) for v in pair['files']}=={'scientific_plan.json','plan_arguments.json','execution_contract.json','effective_plan.json','source_provenance.json'}
  for v in pair['files']:
   assert v['source'].startswith('.local/k64_seed23_bridges_20261020T1949/'+name+'/static_candidate/') and v['path'].startswith(prefix)
   src=R/v['source'];assert src.resolve()==src and src.stat().st_size==v['bytes'] and h(src)==v['sha256'];d=rd(src)
   if Path(v['path']).name in ('scientific_plan.json','effective_plan.json'):
    i=d['invocation'];assert i['stage']=='development' and i['suite']==pair['suite'] and i['method_ids']==pair['methods'] and i['resume'] is False and i['prior_job_ids']==[] and i['stop_after'] is None
   for base in [R,P]:
    dst=base/v['path'];assert dst.resolve()==dst and not any(q.is_symlink() for q in [src,*src.parents,dst,*dst.parents]);assert not dst.exists() or dst.read_bytes()==src.read_bytes();intent.append((base,v))
 out=[]
 for base,v in intent:
  dst=base/v['path'];dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():dst.open('xb').write((R/v['source']).read_bytes())
  assert h(dst)==v['sha256'];out.append({'destination':str(dst),'source':v['source'],'sha256':v['sha256'],'bytes':v['bytes']})
 assert len(out)==20 and h(state)==before
 p=R/B/'k64_static_plan_publication.json'
 with p.open('x') as f:json.dump({'status':'exact_two_CPU_candidate_plans_published_not_authorized','manifest':{'path':M,'sha256':PIN},'destinations':out,'P_publication_scope':'All five exact JSON inputs per pair copied for original action-wrapper reference verification; map minimum publish_P flags retained unchanged. No invocation or readiness/auth/Slurm submitted.','state_unchanged':True,'new_jobs':0,'GPU_admission':False,'independent_and_actual_P_action_wrapper_gate_pending':True},f,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps({'status':'two_plans_R_P_exact_source_dependencies_only','files':20,'receipt_sha256':h(p)}))
