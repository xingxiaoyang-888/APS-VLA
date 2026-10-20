from pathlib import Path
import json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
D=R/'.local/nonLong_development_plans_20261020T1418/revision02/attempt01'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('publishplans20261020T1418',cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==raw
 else:
  with p.open('xb') as f:f.write(raw)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 before=h(R/'results/experiment_supervisor/state.json')
 p=D/'candidate_review.json';assert h(p)=='9ff986667610aac9d0bdbc2aabd4c080d6ad1c400639d070b1b992b1e7157b9e'
 v=json.loads(p.read_bytes());assert v['source173_unchanged'] and v['total_planned_trials']==600 and not v['production_files_changed']
 rows=[]
 for x in v['plans']:
  assert x['group_key'] in ['libero_spatial_k256_seed23','libero_spatial_k256_seed41','libero_object_k256_seed41']
  assert x['original_P_scientific_wrapper_verify_passed'] and not x['new_P_wrapper_verify_passed'] and not x['exact_runtime_readiness_created']
  for k,n in [('scientific_plan','scientific_plan.json'),('execution_contract','execution_contract.json'),('effective_plan','effective_plan.json')]:
   rr=x[k];assert rr['path']=='results/formal_main_v2/execution/nonLong_action_v1_20261020T1418/'+x['group_key']+'/'+n
   src=D/x['group_key']/n;assert h(src)==rr['sha256'];raw=src.read_bytes();put(R/rr['path'],raw);put(P/rr['path'],raw);rows.append(rr)
 assert h(R/'results/experiment_supervisor/state.json')==before
 out=B+'/nonLong_static_plan_publication.json';put(R/out,(json.dumps(dict(status='published_exact_candidate_metadata_only',files=rows,state_unchanged=True,GPU_submissions=[],final_release=False),sort_keys=True,indent=2)+'\n').encode())
 put(R/B/'root_operations/publish_static_20261020T1418.py',Path(__file__).read_bytes())
 print(json.dumps(dict(path=out,sha256=h(R/out),published=len(rows))))
