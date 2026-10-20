from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,sys,importlib.util,copy,os,uuid,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2330';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530';STATE='results/experiment_supervisor/state.json'
JOBS=['3050870','3050890','3050901','3050916']
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n,pin=None):
 p=R/n
 if pin:assert h(p)==pin,n
 return json.loads(p.read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n))
def raw(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+chr(10)).encode()
def new(n,data):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data)
 return ref(n)
def module(name,rel,pin):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=module('summary1530ctl','scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363')
g=module('summary1530gateway','scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a')
core=rd(B+'/completed_evidence_integration_1530.json','ca8c64984a37a75e88ae47cb5e641b10f2b238f4ded1f1b73a1a8db772482822')
postref=dict(path=E+'/integration_independent/postapply_review.json',sha256='f1d095207150b3ce1127b527732837ae4e85d544a4f29587a9b231a17e4c8c18');post=rd(postref['path'],postref['sha256'])
dispatch=rd(B+'/dispatch_root_report.json','82a65bd598a35cbaa49afeca1259c8b2ca39f20ca237fd282dd534c13546f8bf')
dindref=dict(path=E+'/dispatch_independent/independent_review.json',sha256='b56c5acec5972da37374c871a772d16eda633e35a0c37e25ffcbc2d259a46a7c');dind=rd(dindref['path'],dindref['sha256'])
probe=rd(E+'/Goal_probe_terminal/terminal_summary.json','b5a8b094d523bb671945109b5a44b63d63c1d5b1f6b35c140f4dfb89926eddf4')
assert post['status'].startswith('passed') and dind['status'].startswith('passed')
assert [x['job_id'] for x in dispatch['submissions']]==JOBS and dispatch['new_planned_trials']==800 and dispatch['new_completed_trials']==0
assert probe['external_queries']==12 and probe['policy_control_actions']==0 and not probe['original_mismatch_reproduced'] and probe['original200_HOLD_unchanged'] and not probe['sealed_values_read']
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/STATE;before_raw=sp.read_bytes();before=h(sp);s=json.loads(before_raw);old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert f['root_and_independent_completed_arms']==66 and f['root_and_independent_reviewed_arm_updates']==331000 and f['current_action_development_trial_count']==4400 and f['completed_development_trials']==5612 and f['current_action_development_unique_initial_states']==400
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert 'nonLong_development_submissions_1530' not in f and 'supervision_integrity_review_20261020T1530' not in f
 owner=rd('results/formal_main_v2/autonomous_training/run_v1/owner.json');assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538'
 with Path(owner['lock']).open('rb') as lf:
  held=False
  try:fcntl.flock(lf,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lf,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 for jid in cap['occupied']:
  j=next(j for j in s['registered_jobs'] if str(j['job_id'])==jid);g.check_observed_identity(j,obs['rows'][jid],obs['queue'].get(jid),c.TERMINAL)
 for e in dispatch['submissions']:
  js=[j for j in s['registered_jobs'] if str(j['job_id'])==e['job_id']];assert len(js)==1 and js[0]['method_ids']==e['method_ids'] and js[0]['suite']==e['suite'] and js[0]['mode']=='development'
  assert h(R/js[0]['invocation'])==h(P/js[0]['invocation'])==e['invocation']['sha256']
  assert e['job_id'] not in f['new_action_development_verified_by_job']
 assert obs['rows']['3050711']['status']=='COMPLETED' and obs['rows']['3050711']['exit_code']=='0:0' and obs['rows']['3050711']['elapsed_seconds']==354 and obs['rows']['3050711']['gpus']==1
 assert len({str(j['job_id']) for j in s['registered_jobs']})==len(s['registered_jobs'])
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 inv=rd(g.INVENTORY,g.INVENTORY_SHA);assert len(inv['files'])==173
 for n,pin in inv['files'].items():assert h(R/n)==h(g.S/n)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 entries=copy.deepcopy(dispatch['submissions'])
 for entry in entries:entry['observed_status']=obs['rows'][entry['job_id']]['status'];entry['terminal_review_status']='pending_original_raw_consumer_and_independent_review'
 summary=dict(schema='formal_main_v2',kind='root_supervision_after_completed_evidence_and_exact_dispatch',utc=now,state_before_sha256=before,
  root_independent_complete=66,total_training_arms=72,root_independent_updates=331000,new_training_arms_accepted=2,new_development_trials_accepted=600,
  current_action_development_trials=4400,raw_historical_and_current_accepted_development_trials=5612,explicit_legacy_equivalent_Long_trials=600,compatible_development_trials=5000,unique_initial_states=400,
  completed_evidence=ref(B+'/completed_evidence_integration_1530.json'),completed_evidence_post_independent_review=postref,dispatch=ref(B+'/dispatch_root_report.json'),dispatch_independent_review=dindref,
  new_development_job_ids=JOBS,new_development_trials_planned=800,new_dispatch_trials_accepted=0,new_engineering_job_ids=['3050711'],engineering_trials_in_scientific_denominator=0,
  Goal_probe_terminal=ref(E+'/Goal_probe_terminal/terminal_summary.json'),Goal_probe_new_policy_actions=0,Goal_probe_original_mismatch_reproduced=False,Goal_probe_cause_undetermined=True,Goal256seed17_original200_still_HOLD=True,
  Object256seed23_bridge_scientifically_admitted=False,Goal64seed41_machine_nonweights_archived_not_root_accepted=True,
  GPU_active_jobs=len(cap['occupied']),occupied_job_ids=cap['occupied'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,scheduler=obs,capacity=cap,owner=owner,lifecycle_lease_held=True,
  all_registered_allocations_counted_once=True,final_cost=False,source173_unchanged=True,scientific_settings_changed=False,final_completed=0,final_expected=35200,final_release=False,
  pending=None,reserved_GPU_slots=0,healthy_jobs_left_to_controller_and_scheduled_supervision=True,final_integrity_cross_check_pending=True)
 sr=B+'/summary_after_dispatch.json';summary_ref=dict(path=sr,sha256=hashlib.sha256(raw(summary)).hexdigest())
 f['nonLong_development_submissions_1530']=entries
 f['root_completed_evidence_integrity_review_20261020T1530']=dict(status='passed',independent_review=postref,accepted_evidence=summary['completed_evidence'],new_training_groups_accepted=2,new_development_trials_accepted=600)
 f['Goal_t0_probe_3050711_terminal']=dict(status='completed_bounded_engineering_fault_not_reproduced',terminal=summary['Goal_probe_terminal'],dispatch=ref(B+'/Goal_t0_dispatch/receipt.json'),GPU_seconds=354,GPU_cost_already_in_global_total=True,policy_actions=0,scientific_release=False,original200_still_HOLD=True,cause='undetermined')
 f['supervision_integrity_review_20261020T1530']=dict(status='pending_final_cross_check',summary=summary_ref,completed_evidence_post_independent_review=postref,dispatch_independent_review=dindref,final_release=False)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 s['current_work']=f"66/72 root+independent training,331000 reviewed updates;600 new accepted development,current4400 plus explicit legacyLong600 compatible5000,400 unique initials. Four64 development jobs {JOBS} planned800,0accepted. Goalprobe3050711 completed12query120dummy0policy,fault not reproduced;original200HOLD. Object256s23 bridge unadmitted;Goal64s41 root review pending. {len(cap['occupied'])}GPU active,{seconds/3600:.3f}GPUh. Final0/35200sealed."
 s['next_actions']=[
 'Leave healthy training and four registered64 development jobs to controller and scheduled supervision; no continuous polling or duplicate submission.',
 'At next supervision accept only genuine original consumer and independent terminal receipts; Goal64s41 machine completion is not root completion.',
 'Goal256s17 original200 remainHOLD. Probe3050711 did not reproduce fault and does not clear it; inspect original failing sequence before bounded repair approval.',
 'Object256s23 versioned consumer compatibility candidate is not scientifically admitted; require independent and actual entry/consumer acceptance before deployment.',
 'Preserve Spatial256 B-A+0.333pp CI[-0.667,+1.333],Goal128 negative1.333pp andLong128 negative2.67pp. No tuning,equivalence or unmeasured speed claim.',
 'Keep final35200 and same-checkpoint O2A/components behind registered identity/freeze/release; sealed final values unread.']
 s['next_allowed_action']=s['next_actions'][0]
 for k in ['last_root_supervision_snapshot','last_root_health_check','last_healthy_supervision']:s[k]=summary_ref
 s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']=datetime.now(timezone(timedelta(hours=8))).date().isoformat()
 allowed={'formal_main_progress','current_round_cost','current_work','next_actions','next_allowed_action','last_root_supervision_snapshot','last_root_health_check','last_healthy_supervision','last_supervision_utc','updated_utc','updated_date'}
 for k,v in old.items():
  if k not in allowed:assert s[k]==v,k
 assert s['registered_jobs']==old['registered_jobs'] and s['autonomous_training_v1']==old['autonomous_training_v1']
 for k,v in old['formal_main_progress'].items():
  if k!='parallel_execution':assert f[k]==v,k
 brief=f"{stamp}：正式训练已双审66/72组；新增600条开发已验收，当前动作语义4400条、400个唯一初态。四组Spatial/Object64开发已唯一派发800条，尚未终审；当前{len(cap['occupied'])}个GPU作业，累计{seconds/3600:.3f}GPU小时。Goal探针完成354GPU秒、12次查询/120等待步/0策略动作，未复现原t0差异，原因仍不明，原200条继续HOLD。Object256 seed23来源兼容桥未准入，Goal64 seed41仅机器完成待root终验。最后评测0/35200、封存不变。见[本轮监督](../{sr})。"
 docs={};prior={}
 for n in ['docs/实验进度.md','docs/完整实验计划.md','docs/正式自动连续训练执行登记.md']:
  original=(R/n).read_bytes();prior[n]=h(R/n);a,sep,b=original.partition(bytes([10]));assert sep;docs[n]=a+bytes([10,10])+brief.encode()+bytes([10,10])+b
 n='docs/正式下游阻塞登记_20261020T1530.md'
 docs[n]=(chr(10).join(['# 正式下游工程与开发登记','',brief,'',
 '四个新开发作业：Spatial64 seed17/41（3050870/3050890），Object64 seed17/41（3050901/3050916）。每组A/B各100条，保持原全部10任务开发面板；4个会计数据库短暂缺行均通过原ACK/精确token对账，未重发。原始失败、资源收据、提交入口与独立审计全部保留。',
 '', 'Goal工程仅在原固定开发状态上执行ABBA×3 reset/query。12次输入hash均与原B相同，原A差异未重现。该探针未重放原200条之前的模型与环境历史，不能证明原记录正确；保留原200条，不删除不配对条目、不作科学重跑。288份NPZ原始数组留服务器，来源/逐文件hash与非权重记录已归档。',
 '', 'Object256 seed23兼容候选保留旧失败3028460及成本，尚未完成独立生产入口准入。Goal64 seed41非权重产物已回存、无根验收完成数增量。',
 '', 'Spatial256三种子开发A98.000%、B98.333%、B−A+0.333个百分点，95%配对区间[−0.667,+1.333]；尚无同checkpoint完整O2A，不能确认剪枝折中改善。既有Goal与Long负结果保持。',
 '', '健康作业留给自动控制器与后续监督；本轮无实时轮询、无额外实验扩展，最终封存门槛保持。',''])).encode()
 for name in [sr,B+'/final_supervision_intent.json',B+'/final_supervision_state_before.json',B+'/final_supervision_completion.json',n]:assert not (R/name).exists(),name
 intent=dict(state_before_sha256=before,source=ref(Path(__file__).relative_to(R).as_posix()),previous_top_fields={k:old.get(k) for k in allowed if k not in ['formal_main_progress','current_round_cost']},summary=summary_ref,documents_before=prior,documents_after={k:hashlib.sha256(v).hexdigest() for k,v in docs.items()})
 new(B+'/final_supervision_intent.json',raw(intent));new(B+'/final_supervision_state_before.json',before_raw);new(sr,raw(summary))
 for name,data in docs.items():
  target=R/name
  if name in prior:
   assert h(target)==prior[name];tmp=target.with_name(target.name+'.'+uuid.uuid4().hex+'.partial')
   with tmp.open('xb') as tf:tf.write(data)
   assert h(target)==prior[name];os.replace(tmp,target)
  else:new(name,data)
 c.atomic_json(sp,s,before)
 result=dict(status='root_summary_applied_pending_final_cross_check',summary=summary_ref,state_before_sha256=before,state_after_sha256=h(sp),intent=ref(B+'/final_supervision_intent.json'),docs={n:ref(n) for n in docs},core_scientific_acceptance_unchanged=True,controller_and_registry_unchanged=True)
 completion=new(B+'/final_supervision_completion.json',raw(result))
 print(json.dumps(dict(summary=summary_ref,completion=completion,root_complete=66,active_GPU=len(cap['occupied']),GPU_hours=seconds/3600,new_planned800_not_accepted=True)),flush=True)
