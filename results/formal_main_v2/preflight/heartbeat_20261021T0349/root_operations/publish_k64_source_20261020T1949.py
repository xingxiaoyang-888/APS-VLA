from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B='results/formal_main_v2/preflight/heartbeat_20261021T0349'
M='.local/k64_seed23_bridges_20261020T1949/source_publication_manifest_v2.json';PIN='ec56fca197dcbb6de668761081852be973aba6ab61673edf4c961d29390973aa'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def record(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('k64pub1949ctl',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 st=R/'results/experiment_supervisor/state.json';before=h(st);s=read(st);assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0
 assert h(R/M)==PIN;m=read(R/M);assert len(m['pairs'])==2 and m['status']=='revision02_source_only_publication_candidate_not_runtime_authority'
 frozen=read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json')['files'];assert len(frozen)==173
 for n,pin in frozen.items():assert h(R/n)==h(P/'snapshots/formal_main_v2_run_564be0995e'/n)==pin
 intent=[]
 for name,pair in zip(['spatial','object'],m['pairs']):
  assert pair['suite']=='libero_'+name and pair['method_ids']==['A64_seed23','B64_seed23'] and pair['package_R_only'] is True and pair['manifest_R_and_P'] is True
  assert {Path(v['path']).name for v in pair['files']}=={'control.py','bridge_v2.py','policy_v1.json','README.md'} and len(pair['files'])==4
  for v in pair['files']:
   assert Path(v['path']).parent.as_posix()=='scripts/ops/formal_'+name+'64s23_source_bridge_v1';intent.append((R,v))
  v=pair['manifest'];assert v['path']=='results/formal_main_v2/execution/'+name+'64seed23_source_control_v1_20261020T1949/development.json';intent.extend([(R,v),(P,v)])
 for base,v in intent:
  assert v['source'].startswith('.local/k64_seed23_bridges_20261020T1949/') and '..' not in Path(v['source']).parts and '..' not in Path(v['path']).parts
  src=R/v['source'];dst=base/v['path'];assert src.resolve()==src and dst.resolve()==dst and not any(x.is_symlink() for x in [src,*src.parents,dst,*dst.parents])
  assert h(src)==v['sha256'] and src.stat().st_size==v['bytes'] and v['path'] not in frozen
  if dst.exists():assert dst.read_bytes()==src.read_bytes()
  if src.suffix=='.py':compile(src.read_bytes(),str(src),'exec')
 record(R/B/'k64_candidate_publication_intent.json',{'status':'CPU_source_dependencies_only','manifest':{'path':M,'sha256':PIN},'state_before':before,'destinations':[str(base/v['path']) for base,v in intent],'GPU_authority':False,'runtime_admission':False})
 result=[]
 for base,v in intent:
  dst=base/v['path'];existed=dst.exists();dst.parent.mkdir(parents=True,exist_ok=True)
  if not existed:dst.open('xb').write((R/v['source']).read_bytes())
  assert h(dst)==v['sha256'];result.append({'destination':str(dst),'source':v['source'],'sha256':v['sha256'],'bytes':v['bytes'],'already_exact':existed})
 assert h(st)==before
 record(R/B/'k64_candidate_publication.json',{'status':'published_exact_new_CPU_source_dependencies','manifest':{'path':M,'sha256':PIN},'destinations':result,'original173_unchanged':True,'state_unchanged':True,'new_jobs':0,'training_changed':False,'GPU_authority':False,'canonical_actual_planner_and_P_wrapper_verify_pending':True,'independent_admission_pending':True})
 print(json.dumps({'status':'source_dependencies_published_only','files':len(result),'runtime_admitted':False,'state_unchanged':True}))
