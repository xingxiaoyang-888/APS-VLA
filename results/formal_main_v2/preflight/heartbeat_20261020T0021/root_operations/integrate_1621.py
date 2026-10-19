from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0021'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';spec=importlib.util.spec_from_file_location('integrate1621ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=json.loads(sp.read_text());old=copy.deepcopy(s);ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and s['formal_main_progress']['root_and_independent_completed_arms']==46
 assert ctl['reserved_GPU_slots']==1 and ctl['reservation_root_record']['sha256']=='0aabce41556248f83877ce47a102ebb32817624eac4ad04a431862b098289c9d'
 assert s['formal_main_progress']['completed_final_trials']==0 and not s['formal_main_progress']['global_release_created']
 authdir=R/'.local/spatial_resume_audit_1621';manifest=authdir/'archive_closure.json';assert h(manifest)=='a29e10e459c05112367d8bab239177c8dc0a3b4459d2709d74baa87cb50f237e'
 rows=json.loads(manifest.read_text())['files']
 if isinstance(rows,dict):rows=[dict(path='.local/spatial_resume_audit_1621/'+n,**v) for n,v in rows.items()]
 rows=rows+[dict(path=manifest.relative_to(R).as_posix(),sha256=h(manifest),bytes=manifest.stat().st_size)]
 mappings=[]
 for row in rows:
  p=R/row['path'];assert p.parent==authdir and p.is_file() and not p.is_symlink() and h(p)==row['sha256'] and p.stat().st_size==row['bytes']
  dest=R/B/'spatial_resume_independent'/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as f:f.write(p.read_bytes())
  mappings.append(dict(source=row['path'],path=dest.relative_to(R).as_posix(),sha256=h(dest),bytes=dest.stat().st_size))
 independent_archive=save(B+'/spatial_resume_independent_archive.json',dict(schema='formal_main_v2',files=mappings,originals_retained=True))
 indpath=B+'/spatial_resume_independent/independent_review.json';assert h(R/indpath)=='1a31a6ea6d858863e7ef1dd8f62e0942e06cc8aaea19f36d6d0583f72b612a3e'
 ind=json.loads((R/indpath).read_text());assert ind['status']=='passed_nonexecutable_planning_review' and ind['production_decision']=='HOLD_PRODUCTION' and ind['independent_checks']['passed']==23 and ind['independent_checks']['failed']==0
 candidatepath=B+'/spatial_resume_candidate/attempt03_candidate.json';assert h(R/candidatepath)=='b4d75649fd6bb29e065b22840a729a8eae416fff3b99d4f36f0ec25661ed344d'
 candidate=json.loads((R/candidatepath).read_text());assert candidate['submission_authorized'] is False and candidate['production_readiness'] is False and candidate['maximum_new_trial_ids']==588 and candidate['prior_allocation_GPU_seconds']==395
 assert candidate['prior_job_ids']==['3022743','3042529'] and candidate['actual_ledger_contributors']==['3022743']
 assert ind['production_hold_reasons']==candidate['unresolved_integration']
 rootreview=save(B+'/Spatial_development_candidate_root_review.json',dict(schema='formal_main_v2',kind='root_nonexecutable_planning_review',status='accepted_as_preparation_only',candidate=ref(candidatepath),independent=ref(indpath),author=ref(B+'/spatial_resume_candidate/candidate_review.json'),proof_basis=ref(B+'/spatial_resume_candidate/proof_basis_addendum.json'),root_read_runtime_source_and_plan=True,author_CPU_checks=41,independent_CPU_checks=23,production_decision='HOLD_PRODUCTION',no_new_authorization_or_invocation=True,no_GPU_submission=True,new_trials=0,old_trials_preserved=12,remaining_trials=588,all_prior_GPU_seconds=395,child_started_conclusion_uses_combined_exact_evidence_not_old_wrapper_boolean=True,required_before_submission=candidate['unresolved_integration']))
 obrel=B+'/reservation_activation_scheduler.json';ob=json.loads((R/obrel).read_text());assert h(R/B/'Spatial64_seed23_reservation_activation.json')=='68009de000de8e75813369246723b485e5d13db6a57cf5ed5a20119747a3ee24'
 assert set(ob['observation']['rows'])=={str(j['job_id']) for j in s['registered_jobs']}
 seconds=sum(ob['observation']['rows'][str(j['job_id'])]['elapsed_seconds']*ob['observation']['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 inventory=json.loads((R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json').read_text())
 for rel,pin in inventory['files'].items():assert h(R/rel)==pin
 now=datetime.now(timezone.utc).isoformat()
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_exception_preparation',utc=now,root_independent_complete=46,machine_and_prior_complete=s['formal_main_progress']['trained_arms'],root_independent_updates=239000,root_training_complete_by_suite=dict(Long=18,Spatial=16,Object=10,Goal=2),observation_utc=ob['utc'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,active_GPU_jobs=len(ob['capacity']['occupied']),active_evidence=ref(B+'/active_evidence.json'),scheduler=ref(obrel),root_and_independent_reservation_preparation=ref(B+'/Spatial64_seed23_reservation_activation.json'),reserved_next_GPU_slots=1,reservation_not_an_extra_allocated_GPU=True,Spatial_development_candidate=rootreview,original_failed_allocation_retained=True,new_GPU_submissions=[],new_completed_training_pairs=[],new_final_trials=0,completed_final_trials=0,final_release=False,normal_training_left_to_controller=True,no_in_turn_realtime_polling=True,server_only=True,previous_verified_Git_commit='816a96bbcd8a4a7ee4daffa0da8062af727c10dd',frozen_files_unchanged=173))
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now
 s['current_work']='46/72 root+independent completed;8 healthy GPU jobs observed. Existing Spatial64 seed23 CUDA recovery owns next free slot;Spatial development attempt03 is audited nonexecutable preparation and remains held.'
 s['next_actions']=['Normal controller continues auto5000 with at most8 GPUs, respecting the exact single reserved CUDA recovery slot; no healthy job cancellation.', 'When real capacity is free, root runs exact3028522 recovery gateway fresh preflight and single submit to1500; after actual recovery evidence, separately admit5000.', 'Implement and independently audit exact3042529 before-child planning and terminal-cost integration, then new root readiness/one-use authorization for remaining588 Spatial development trials; never reuse55f6.', 'Retain all failure/history and keep final/O2A/global freeze gates closed until their full registered evidence is accepted.']
 s['next_allowed_action']=s['next_actions'][1]+' '+s['next_actions'][2]
 s['formal_main_progress']['downstream_action_range_issue']['latest_nonexecutable_Spatial_resume_preparation']=rootreview
 assert s['registered_jobs']==old['registered_jobs'] and s['autonomous_training_v1']==old['autonomous_training_v1']
 c.atomic_json(sp,s,before)
 note='2026-10-20 00:35 CST 快照：正式训练仍为 **46/72组**（Long18、Spatial16、Object10、Goal2），8个GPU作业运行，累计分配 **383.799 GPU小时**，含失败及运行中分配，非最终费用。Object256 seed23的已登记恢复作业3042627在本轮单次日志快照中A已到937步；不将日志进度算作完成验收。\n\nSpatial64 seed23（原3028522）A/B1000步、cursor8000的实际resume字节及授权经root/独审复核，已用writer锁/CAS激活已有精确1槽预约，等待下一真实空槽恢复至1500；正常8卡不取消，原5000调度不变。预约不是额外占用GPU，本轮未提交新作业；实际恢复后仍须复核再准入连续5000。\n\nSpatial开发attempt03仅完成不可执行的准备与审查：作者41项、独立23项CPU检查；原12条终态/25行账本、3022743与3042529合计395 GPU秒完整保留，仅计划剩余588条。既有P侧输入与未改wrapper检查通过，但最新失败审阅、规划及零trial作业费用消费接口尚未接入，新readiness和授权未生成，**保持HOLD_PRODUCTION**。原字段original_scientific_wrapper_executed恒False不能独自证明新child未启动，本案依据精确父verify异常复现、控制流、空产物及未变前缀的组合证据。173冻结文件未改，最终仍0/35200，正常训练交控制器和后续定时监督。[本轮收据](../'+B+'/summary.json)。\n\n'
 changed=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式CUDA启动失败恢复登记','正式动作执行入口接入记录']:
  rel='docs/'+name+'.md';assert rel not in inventory['files'];p=R/rel;prior=p.read_text();assert '2026-10-20 00:35 CST 快照' not in prior
  first,tail=prior.split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+note+tail.lstrip('\n'));changed.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 readme=R/'scripts/ops/formal_action_deployment_v1/README.md';prior=readme.read_text();first,tail=prior.split('\n',1);oldsha=h(readme)
 latest='Current status, 2026-10-20 CST: the original seven files are present in P. The first actual Spatial deployment allocation3042529 failed before the child and produced0 trials. Its missing immutable prior-review dependency was restored exactly; the unchanged P wrapper now passes CPU preflight. The attempt03 proposal is independently reviewed preparation only and remains HOLD_PRODUCTION pending explicit no-child planning/cost integration and a new exact authorization. Authorization55f6 is consumed. The next reserved GPU slot belongs to the separately approved Spatial64 seed23 training recovery.\n\nThe following preserves the initial component publication description; its initial not-activated status is historical.\n\n'
 readme.write_text(first+'\n\n'+latest+tail.lstrip('\n'));changed.append(dict(path=readme.relative_to(R).as_posix(),before_sha256=oldsha,after_sha256=h(readme)))
 ops=R/B/'root_operations';ops.mkdir(exist_ok=True)
 for name in ['observe_formal_1621.py','capture_active_1621.py','activate_spatial_cuda_reservation_1621.py','archive_candidate_cuda_1621.py','integrate_1621.py']:
  with (ops/name).open('xb') as f:f.write((R/'.local'/name).read_bytes())
 with (R/B/'previous_Git_push_verified.json').open('xb') as f:f.write((R/'.local/github_push_1518_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(schema='formal_main_v2',state_before=before,state_after=h(sp),summary=summary,documentation=changed,independent_archive=independent_archive,source_and_science_unchanged=True,CPU_failures_retained=True,initial_reservation_lock_contention_before_any_state_write=True,no_automatic_retry_or_new_GPU_job=True))
 print(json.dumps(dict(summary=summary,root_complete=46,observed_GPU=8,GPU_hours=seconds/3600,reserved_next_GPU=1,Spatial_development='HOLD_PRODUCTION',documents=len(changed))))
