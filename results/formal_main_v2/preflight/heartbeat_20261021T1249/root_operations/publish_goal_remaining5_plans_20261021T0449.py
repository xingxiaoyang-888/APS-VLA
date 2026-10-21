from pathlib import Path
import json,hashlib,fcntl,os,sys,importlib.util,datetime,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T1249'
E=R/'results/formal_main_v2/engineering/supervision_delivery_20261021T0449'
STATE=R/'results/experiment_supervisor/state.json';STATE_SHA='d795f666c630ba196f9eba8aae8d5cbed879e10fd596fc95d37c745f281948ba'
D=R/'.local/goal_remaining5_plans_20261021T0449/v2';INDEX=D/'candidate_index.json';PIN='638ec6f36339aa3a43a78266a60c58427aa40f22979f442cd740432962a28d3f'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def direct(p):
 assert p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]),str(p)
 return p
def write(p,raw):
 direct(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 assert p.read_bytes()==raw
def ref(p):return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def module(path,pin,name):
 assert sha(path)==pin
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
assert sha(INDEX)==PIN
index=json.loads(INDEX.read_bytes());keys=['libero_goal_k256_seed23','libero_goal_k256_seed41','libero_goal_k64_seed17','libero_goal_k64_seed23','libero_goal_k64_seed41']
assert index['scope']==keys and len(index['publication_map'])==40 and not index['production_admitted']
allowed={'results/formal_main_v2/execution/goal_remaining5_v1/'+k+'/'+n for k in keys for n in ['effective_plan.json','execution_contract.json','execution_manifest.json','invocation_template.json','scientific_plan.json','source_provenance.json','specification.json']}
allowed_configs={'configs/experiments/formal_main_v2/'+k+'.json' for k in keys}
seen=set();prepared=[]
for row in index['publication_map']:
 rel=row['destination'];assert rel not in seen and rel in allowed|allowed_configs;seen.add(rel)
 roots=['P'] if rel in allowed_configs else ['R','P'];assert row['install_roots']==roots
 source=direct(R/row['source'])
 if rel in allowed_configs:assert source==R/rel
 else:assert source==D/'publication'/rel
 raw=source.read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
 for root in roots:
  dest=direct((R if root=='R' else P)/rel);assert not dest.exists(),'target already exists '+str(dest)
  prepared.append((dest,raw,root,row))
assert seen==allowed|allowed_configs and len(prepared)==75
for k in keys:
 x='results/formal_main_v2/execution/goal_remaining5_v1/'+k
 for root in [R,P]:assert not (root/x/'attempt01').exists()
 assert not (R/index['pairs'][k]['planned_invocation_path']).exists()
assert sha(D/'CPU_report_v3.json')=='cf7994f31d84e41737818ab96823cad48152ad40bb233694de275f9042d95128'
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 assert sha(STATE)==STATE_SHA
 assert json.loads(STATE.read_bytes()).get('pending_submission') is None
 for dest,raw,root,row in prepared:assert not dest.exists()
 proposal={'kind':'Goal_remaining5_pure_metadata_publication','source_index':ref(INDEX),'state_sha256':STATE_SHA,'file_target_count':75,'publication_map':index['publication_map'],'new_GPU_submissions':0,'prepared_invocations_created':False,'scientific_results_changed':False}
 write(B/'Goal_remaining5_plan_publication_proposal.json',enc(proposal))
 for dest,raw,root,row in prepared:write(dest,raw)
 cpu=E/'Goal_plan_author_CPU'/'CPU_report_v3_original.json';write(cpu,(D/'CPU_report_v3.json').read_bytes())
 frozen_index=E/'Goal_plan_author_CPU'/'candidate_index_original.json';write(frozen_index,INDEX.read_bytes())
 assert sha(STATE)==STATE_SHA
 write(B/'Goal_remaining5_plan_publication_receipt.json',enc({**proposal,'status':'published_exact_metadata_only','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_original_rebuild_pending':True}))
b=module(D/'build_plans.py','3d84ce954a5d6b3d74cbe430518b12bdba93fe25bc17631bf743cc75698b6ffa','root_remaining5_builder')
b.verify_index(INDEX,PIN,canonical=True,state_override=json.loads(STATE.read_bytes()))
for dest,raw,root,row in prepared:assert dest.read_bytes()==raw
pr=module(D/'prepare_after_reviews_v2.py','a633636dc4cdd64f75d32de72dda5dea34804b1253d7658c21dce97091aa7736','root_remaining5_prepare')
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);assert sha(STATE)==STATE_SHA
 evidence=B/'Goal_remaining5_canonical_plan_root_rebuild.json'
 write(evidence,enc({'schema':'formal_main_v2','kind':'Goal_remaining5_root_canonical_original_plan_rebuild','status':'passed','reviewed_by':'root','pair_keys':keys,'source_index':ref(frozen_index),'source_state_sha256':STATE_SHA,'canonical_manifest_IO_no_projection':True,'actual_original_scientific_plan_rebuilds':5,'actual_original_effective_plan_rebuilds':5,'actual_original_invocation_templates_rebuilt':5,'original_builders':index['original_builders'],'source_identity_independent_baseline':{'path':'results/formal_main_v2/engineering/supervision_delivery_20261021T0449/Goal_identity_baseline/identity_baseline_original.json','sha256':'03e0c271f04ca728eece824926c3c9650dcb793d3bc24952070cb7e35a445a5b'},'actual_P_runtime_verified':False,'GPU_execution_authorized':False,'new_trials':0,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}))
 reviews=[]
 for k in keys:
  item=index['pairs'][k];review=pr.expected_review(item,index,'root')
  action=json.loads((R/item['execution_contract']['path']).read_bytes())
  review.update(runtime_sources=action['files'],blockers=[],review_evidence={'root_canonical_rebuild':ref(evidence),'author_CPU':ref(cpu),'identity_independent':{'path':'results/formal_main_v2/engineering/supervision_delivery_20261021T0449/Goal_identity_baseline/identity_baseline_original.json','sha256':'03e0c271f04ca728eece824926c3c9650dcb793d3bc24952070cb7e35a445a5b'}})
  path=R/('results/formal_main_v2/execution/goal_remaining5_v1/'+k+'/plan_root_review.json');write(path,enc(review));write(P/path.relative_to(R),enc(review));reviews.append(ref(path))
 assert sha(STATE)==STATE_SHA
 write(B/'Goal_remaining5_root_plan_review_index.json',enc({'status':'passed_original_preexecution_chain_only','reviews':reviews,'actual_P_runtime_verified':False,'GPU_execution_authorized':False,'new_trials':0}))
print(json.dumps({'status':'published_and_root_canonical_rebuilt','targets':75,'pair_count':5,'state_sha256':sha(STATE),'root_evidence':ref(evidence),'root_reviews':reviews,'GPU_execution_authorized':False},sort_keys=True))
