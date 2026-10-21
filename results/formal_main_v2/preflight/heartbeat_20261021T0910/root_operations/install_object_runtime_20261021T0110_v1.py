from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';B='results/formal_main_v2/preflight/heartbeat_20261021T0910';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2358'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n,pin):
 p=R/n;assert h(p)==pin;return json.loads(p.read_bytes())
def safe(p):assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents])
m=rd(E+'/Object_single_error_production/publication_map.json','030d0b13560ca1580c258440b8b6e2f1aeaaaf478066f8cb259a3b407897de08')
i=rd(E+'/Object_single_error_production_independent/independent_review.json','bdf8af2bdfe21954047a6b6209f0a4f3beac73ecb260df4bff33b69b5fa58baa');assert i['status']=='passed_CPU_candidate_with_production_HOLD' and i['blockers']==[] and i['production_ready'] is False
inv=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');files=inv['files'];assert len(files)==173
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
sp=importlib.util.spec_from_file_location('publish_object_0110_ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
def frozen():
 for n,v in files.items():
  sha=v['sha256'] if isinstance(v,dict) else v
  for root in [R,S,R/'snapshots/formal_main_v2_run_564be0995e']:assert h(root/n)==sha
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert h(R/'results/experiment_supervisor/state.json')=='40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a';frozen()
 assert len(m['files'])==10 and len({v['destination'] for v in m['files']})==10
 refs=[]
 for row in m['files']:
  n=row['destination'];assert n.startswith('scripts/ops/formal_object_single_error_v1/') and n not in files and '..' not in Path(n).parts
  src=R/E/'Object_single_error_production'/Path(row['source']).name;safe(src);data=src.read_bytes();assert h(src)==row['sha256'] and len(data)==row['bytes']
  targets=[]
  for root in [R,P]:
   target=root/n;safe(target)
   assert not target.exists(),str(target)
   targets.append(target)
  refs.append((row,data,targets))
 for row,data,targets in refs:
  for target in targets:
   target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb') as f:f.write(data)
   assert h(target)==row['sha256']
 frozen();assert h(R/'results/experiment_supervisor/state.json')=='40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a'
 value={'status':'exact_CPU_reviewed_sources_published_runtime_HOLD','utc':datetime.now(timezone.utc).isoformat(),'source_map_sha256':'030d0b13560ca1580c258440b8b6e2f1aeaaaf478066f8cb259a3b407897de08','independent_source_review_sha256':'bdf8af2bdfe21954047a6b6209f0a4f3beac73ecb260df4bff33b69b5fa58baa','files':[{'path':row['destination'],'sha256':row['sha256'],'bytes':row['bytes'],'R_verified':True,'P_verified':True} for row,data,targets in refs],'frozen173_three_roots_unchanged':True,'actual_P_static_verification':False,'new_plan_created':False,'runtime_readiness':False,'production_admitted':False,'GPU_submission_authorized':False,'new_GPU_jobs':[],'state_unchanged':True,'final_release':False}
 out=R/B/'Object_production_publication.json'
 with out.open('x') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 print(json.dumps({'status':value['status'],'files':10,'receipt':str(out.relative_to(R)),'sha256':h(out)}))
