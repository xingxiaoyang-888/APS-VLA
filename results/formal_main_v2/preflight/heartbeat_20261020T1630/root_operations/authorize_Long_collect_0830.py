from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
B='results/formal_main_v2/preflight/heartbeat_20261020T1630';E='results/formal_main_v2/engineering/supervision_delivery_0830'
O='results/formal_main_v2/execution/long_collect_action_v1_0830';D='.local/long_collection_prepare_0830/a2';I='.local/long_collect_independent_0830'
sys.dont_write_bytecode=True;sys.path.insert(0,str(S/'src'))
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return json.loads((R/rel).read_bytes())
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return ref(rel)
def publish(rel):
 q=P/rel;q.parent.mkdir(parents=True,exist_ok=True)
 if q.exists():assert h(q)==h(R/rel)
 else:
  with q.open('xb') as f:f.write((R/rel).read_bytes())
 assert h(q)==h(R/rel)
def mod(rel,pin,name,base=R):
 p=base/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','rootauth0830ctl')
g=mod('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','rootauth0830gateway')
rootrel=B+'/Long_collect_root_runtime_review.json'
root=checked(rootrel,'f034996648ce3f739fe22fc3bd2af81f3be5ab5335c9c7754f21f63481ac8411')
ind=checked(I+'/independent_readiness.json','e4f6635642d93585c4ba7c60a35af03e9ea4260405a0bdb732fe2eef5aabd242')
plan=checked(O+'/effective_plan.json','1ce34d9ecf18e36d2c0043e2fdfd42ca327344d286fb35704fdfe70e8b5ed8ac')
science=checked(O+'/scientific_plan.json','1c50e85dfea3042cb7cee74cf5482e2325e4036e0bc7a74187d0061983790ee0')
action=checked(O+'/execution_contract.json','06ca8c538a323e14ad8197a80e9cc5c39d303976adbd8959630e535b11b1acc0')
for q in [root,ind]:
 assert q['status']=='passed' and q['production_chain_complete'] and q['CPU_only'] and not q['actual_collect_GPU_completed']
 assert q['effective_plan']==ref(O+'/effective_plan.json') and q['scientific_plan']==ref(O+'/scientific_plan.json') and q['plan_sha256']==plan['plan_sha256']
 assert q['runtime_sources']==action['files'] and q['actual_P_original_collector_prepare_only_passed'] and q['actual_P_original_wrapper_passed']
 assert q['old600_reuse_or_rerun_authorized'] is False and q['full_components_authorized'] is False and q['final_values_read'] is False
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);state=json.loads(sp.read_bytes());old=copy.deepcopy(state);ctl=state['autonomous_training_v1']
 assert state['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert not any(j.get('suite')=='libero_10' and (j.get('mode') in ['collect','full','components'] or j.get('stage') in ['collect','full','components']) for j in state['registered_jobs'])
 owner=json.loads((R/'results/formal_main_v2/autonomous_training/run_v1/owner.json').read_bytes())
 assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538'
 with Path(owner['lock']).open('rb') as stream:
  held=False
  try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(stream,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 obs=c.Slurm(timeout=45).observe(state['registered_jobs']);cap=c.capacity(state['registered_jobs'],obs,'3034538')
 assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])+1<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert not (P/plan['output_relative']).exists() and not (R/plan['invocation_relative']).exists() and not (P/plan['invocation_relative']).exists()
 im=checked(I+'/manifest.json','ee882b34f9d816fd9b165b1fa7f3863d7e639c21f831becfdc640ebe40e4d73f');copies=[]
 for q in im['files']+[dict(path=I+'/manifest.json',sha256=h(R/I/'manifest.json'),bytes=(R/I/'manifest.json').stat().st_size)]:
  p=R/q['path'];assert p.resolve().is_relative_to((R/I).resolve()) and p.is_file() and not p.is_symlink() and h(p)==q['sha256'] and p.stat().st_size==q['bytes']
  target=E+'/Long_collect_independent/'+p.relative_to(R/I).as_posix();dest=R/target;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(p.read_bytes())
  copies.append(dict(source=q,archive=ref(target)))
 delivery=save(B+'/Long_collect_independent_delivery.json',dict(copies=copies,source_manifest=ref(I+'/manifest.json'),GPU_execution=False))
 irel=O+'/independent_runtime_review.json'
 with (R/irel).open('xb') as stream:stream.write((R/I/'independent_readiness.json').read_bytes())
 publish(irel);publish(rootrel)
 ready=checked(D+'/runtime_readiness_draft.json','2f9d55368a95bbc3e742886f3c90bf55164caf18456ade70a8d65c00e518abae')
 ready.update(status='passed',reviewed_by='root',raw_consumer_ready=True,production_chain_complete=True,active=True,root_review=ref(rootrel),independent_review=ref(irel),CPU_readiness_only=True,actual_GPU_collect_verified=False)
 ready.pop('pending_runtime_publication_roles')
 ready['runtime_publication_files'].update({rootrel:h(R/rootrel),irel:h(R/irel)})
 readyref=save(O+'/runtime_readiness.json',ready)
 for name,pin in ready['runtime_publication_files'].items():assert h(R/name)==pin;publish(name)
 publish(readyref['path'])
 prepared={**plan['invocation'],'registered_utc':datetime.now(timezone.utc).isoformat(),'plan_sha256':plan['plan_sha256'],'runtime_readiness':readyref}
 prepref=save(O+'/prepared_invocation.json',prepared)
 # Actual new parent verifies the true P copies and distinct genuine readiness receipts.
 wrapper=mod('scripts/ops/formal_action_deployment_v1/wrapper.py','d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33','rootactualouter0830',base=P)
 verified=wrapper.verify(prepared,project=P);assert verified['original_plan']==science and verified['effective_plan']==plan
 auth=checked(D+'/submission_authorization_draft.json','fea805444a618aae370c311777278aab869360a5ef82498ea64f3c7706c8da0d')
 auth.update(status='approved_for_exactly_one_registered_downstream_submission',prepared_invocation=prepref,runtime_readiness=readyref)
 reservation=checked(D+'/reservation_root_record_draft.json','3f44d7fe6bc6f207e4731d119842f615c881305a941d8c9dab875eb4772c5956')
 reservation.update(status='approved_for_exact_downstream_request',authorization_intent_sha256=g.intent_sha(auth),created_utc=datetime.now(timezone.utc).isoformat())
 auth['root_reservation']=save(O+'/root_reservation.json',reservation)
 ar=save(O+'/submission_authorization.json',auth)
 a,e,pl,sc,pr=g.validate_authorization(R,ar)
 bundle=g.FrozenPlan(R,a,e,pl,sc,pr).prepare(state)
 assert bundle['plan']==plan and bundle['invocation']==prepared
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 proof=save(B+'/Long_collect_slot_activation.json',dict(schema='formal_main_v2',kind='root_exact_Long_collect_admission',status='passed_ready_and_reserved_not_yet_submitted',utc=datetime.now(timezone.utc).isoformat(),authorization=ar,reservation=auth['root_reservation'],runtime_readiness=readyref,root_review=ref(rootrel),independent_review=ref(irel),independent_delivery=delivery,actual_P_outer_wrapper_passed=True,original_plan_rebuilt_exactly=True,controller_owner=owner,lifecycle_lease_held=True,scheduler=obs,capacity=cap,occupied_before=len(cap['occupied']),reserved_after=1,capacity_limit=8,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,pending_submission=None,new_GPU_submissions=[],planned_dense_development_trajectories=10,planned_observations=30,new_scientific_success_trials=0,final_release=False,global_freeze=False,full_or_component_timing=False,state_before_sha256=before))
 ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=auth['root_reservation'];ctl.setdefault('root_reservation_activation_history',[]).append(proof)
 assert state['registered_jobs']==old['registered_jobs'] and state['current_round_cost']==old['current_round_cost'] and ctl['blocked_pairs']==old['autonomous_training_v1']['blocked_pairs']
 doc='# 正式Long固定测速观测采集登记\n\n2026-10-20，formal_main_v2。已在任何采集结果前固定输入并完成root及独立CPU链路检查，仅准入一次Dense采集；尚未把计划观测计为已采集。\n\n'
 doc+='来源为原Long开发面板的全部10任务，每任务选择source_state_index最小的一条初态，依任务0—9为 **0、4、7、3、6、2、3、6、8、2**。只用对应官方Dense512基座生成轨迹；环境seed0、runtime seed17、等待10步、chunk8、最大520控制步。每个实际动作前记录原始观测，首、中floor((N−1)/2)、末三个时刻，N须至少3；异常或不足跨度即失败，不按成功与否换轨迹、补帧或替换观测。计划10轨迹/30观测，已有100开发初态范围不变。\n\n'
 doc+='此次只采集统一测速输入，不重评旧600，不增加成功率分母，也不报告推理延迟。使用已GPU验收的动作语义与同一Dense身份，完整输入和173科学文件不变。未来头/教师缓存不参与部署。真实采集完成后须用原始轨迹、面板、动作收据及全部Slurm成本通过双审。\n\n'
 doc+='完整O2A及独立分项计时保留原规则：同checkpoint、同L40与运行环境；原始观测/指令就绪至CPU动作chunk就绪，含预处理、视觉编码、DIE、packing、VLA与后处理，排除模型加载、磁盘读取和模拟器步进。每部署实例预热50次、共同30观测重复20轮、固定随机平衡方法顺序，全部尖峰保留；仍需88身份和四套件开发冻结。此次采集不开放full/components或最终封存初态。\n\n'
 doc+=f'[唯一授权](../{ar["path"]})、[容量及双审收据](../{proof["path"]})、[固定选择规则](../{E}/Long_collect_author_candidate/collection_selection_registration.json)。权重留服务器，非权重结果在服务器控制库回存并同步GitHub。\n'
 with (R/'docs/正式Long固定测速观测采集登记.md').open('x') as stream:stream.write(doc)
 c.atomic_json(sp,state,before)
 print(json.dumps(dict(status='ready_reserved_not_submitted',authorization=ar,receipt=proof,occupied_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=1,GPU_hours=seconds/3600)))
