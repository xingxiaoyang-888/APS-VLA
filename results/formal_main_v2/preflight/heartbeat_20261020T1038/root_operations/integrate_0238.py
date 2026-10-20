from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,copy,sys,importlib.util
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1038'
NR='results/formal_main_v2/libero_object/k64/seed23/training/segment_reviews/3044017.json'
NI=NR.replace('.json','_independent.json')
PUB=B+'/Object64_continuous_publication.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel):return json.loads((R/rel).read_bytes())
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return rd(rel)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
 return ref(rel)
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','integrate0238ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==54 and f['root_and_independent_reviewed_arm_updates']==277000
 assert f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert not any(x.get('job_id')=='3044017' for x in f['completed_engineering_segments'])
 root=checked(NR,'2bffb9a9194b4c1b434b0c79491d165ce6f14d12305f3ebe9b6f4843af288d84')
 ind=checked(NI,'25c78029fa2b5456ea07cf596e518356f96f5acba252b6fe4ef6bc1a5e7b97b0')
 assert root['status']=='passed' and ind['status']=='passed_original_target_recovery_only' and root['completed_by_arm']==ind['completed_by_arm']=={'A':500,'B':500}
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==5210
 assert ind['cost']['retained_FAILED_GPU_seconds']==69 and ind['cost']['successful_recovery_GPU_seconds']==5141 and ind['reviewed_arm_updates_added']==1000
 assert ind['same_full40000_sampling_order'] and ind['all173_source_R_and_S_match'] and not ind['final_release_authorized']
 pub=checked(PUB,'0095ded27d7d620c275d3bdadf33c3493d4c7bc2be0ef3b449a058da02b996a5')
 assert pub['status']=='published_and_registered_no_GPU_submission' and not pub['GPU_submitted']
 authref=pub['authorization'];auth=checked(authref['path'],authref['sha256'])
 assert auth['status']=='approved_exact_once_500_to5000' and auth['pair_key']=='libero_object_k64_seed23'
 pre=checked(pub['canonical_preflight']['path'],pub['canonical_preflight']['sha256'])
 assert pre['status']=='passed_readonly_actual_evidence' and not pre['GPU_submitted'] and not pre['invocation_published']
 spatial=checked(B+'/Spatial3044479_pending_reconciliation.json','7117ddfcc611262cdfc16c346d378f689f40c608aa3706e3a68eef651992541d')
 assert spatial['status']=='exact_original_ACK_job_reconciled' and spatial['new_submissions']==0
 jobs=[j for j in s['registered_jobs'] if j.get('job_id')=='3044479'];assert len(jobs)==1
 assert jobs[0]['suite']=='libero_spatial' and jobs[0]['visual_tokens']==64 and jobs[0]['training_seed']==23 and jobs[0]['segment_end']==5000
 for a in ['A','B']:
  x=ind['arms'][a];assert x['cursor']==x['actual_samples']==x['unique_samples']==4000 and x['resumed_from_existing_checkpoint'] is False and x['replayed_or_uncommitted_samples']==0
 f['completed_engineering_segments'].append(dict(job_id='3044017',suite='libero_object',visual_tokens=64,seed=23,status='passed_root_and_independent_original_target_recovery',updates_by_arm={'A':500,'B':500},allocated_gpu_seconds=5141,pair_total_gpu_seconds=5210,original_FAILED_retained=True,original_failed_GPU_seconds=69,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),new_reviewed_arm_updates=1000,not_completed_formal_training=True))
 f['root_and_independent_reviewed_arm_updates']+=1000
 cu=f['CUDA_startup_issue']
 cu['original_target_recovery_3044017']=dict(status='passed_original500_root_and_independent',job_id='3044017',original_failed_job_id='3028468',original_failed_GPU_seconds=69,recovery_GPU_seconds=5141,pair_GPU_seconds=5210,root_review=ref(NR),independent_review=ref(NI),root_summary=ref(B+'/3044017_root_terminal.json'),completed_by_arm={'A':500,'B':500},original_failure_had_checkpoint=False,original_recovery_used_fresh_initialization=True,full5000_complete=False,continuous5000_admission=pub['authorization'])
 cu['continuous5000_admission_3044017']=dict(status='approved_exact_once_wait_for_real_spare_capacity',authorization=authref,root_review=pub['root_review'],independent_review=pub['independent_review'],actual_preflight=pub['canonical_preflight'],submitted=False,automatic_retry=False,controller_block_preserved=True,scientific_settings_changed=False)
 cu['continuous_after3043399']=dict(status='registered_running',job_id='3044479',submitted=True,target_updates=5000,authorization=jobs[0]['continuous_admission']['authorization'],prior1500_recovery_retained=True,controller_block_retained=True,reconciliation=ref(B+'/Spatial3044479_pending_reconciliation.json'))
 cu['original_target_recovery_3043399']['status']='passed_original1500_root_and_independent_continuous3044479_submitted'
 cu['status']='all_three_original_targets_recovered_two_continuations_active_Object64_admitted_waiting_capacity'
 cu['next']='Object64 seed23 recovered original500 and has separate exact500-to5000 root admission. Submit once only after fresh unreserved capacity and full registry/owner/lease gates. Spatial3044479 and Object2563042627 already submitted; never repeat their admissions.'
 cu['scheduler_next']='Healthy controller continues. Object64 exact continuous admission waits for a real unreserved slot; preserve all failed histories and blocked_pairs.'
 for row in cu['single_recovery_authorizations']:
  if row['failed_job_id']=='3028468':
   row.update(recovery_job_id='3044017',status='original_target500_double_reviewed_continuous5000_admitted_not_submitted',root_terminal_review=ref(NR),independent_terminal_review=ref(NI),reservation_consumed=True,reservation_activated_in_state=False)
  elif row['failed_job_id']=='3028522':row.update(status='original_target1500_double_reviewed_continuous3044479_submitted',continuous_job_id='3044479')
  elif row['failed_job_id']=='3028460':row.update(status='original_target500_double_reviewed_continuous3042627_running',continuous_job_id='3042627')
 ready=f['spatial64seed23_continuous_v2_ready'];ready.update(status='submitted_once_pending_accounting_delay_reconciled',GPU_submitted=True,job_id='3044479',reconciliation=ref(B+'/Spatial3044479_pending_reconciliation.json'),failure_retained=spatial['original_failure'])
 f['object64seed23_continuous_ready']=dict(status='root_and_independent_actual_admission_passed_wait_for_real_spare_GPU',authorization=authref,canonical_preflight=pub['canonical_preflight'],root_publication=ref(PUB),GPU_submitted=False,original500_complete=True,full5000_complete=False)
 for row in f['parallel_execution']['awaiting_terminal_review']:
  if row['job_id']=='3028522':row['status']='FAILED_retained_original1500_passed_continuous3044479_running'
  if row['job_id']=='3028468':row['status']='FAILED_retained_original500_passed_continuous5000_admitted_waiting_capacity'
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])==8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3044017']['status']=='COMPLETED' and obs['rows']['3044017']['elapsed_seconds']==5141 and obs['rows']['3044479']['status']=='RUNNING'
 g=mod('scripts/ops/formal_object64_cuda_continuous_admission_v1/gateway.py','2aaed25efd1d8783ace9ace93a5212f67b52f1d1a6fde1072349d8d8a830f54a','integrate0238gateway')
 owner=g.controller_owner(R,s,obs,auth)
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 inv=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inv['files'])==173
 for rel,pin in inv['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_exact_recovery_and_capacity_refill',utc=now,root_independent_complete=54,machine_complete=f['trained_arms'],total_arms=72,completed_by_suite={'libero_10':18,'libero_spatial':16,'libero_object':14,'libero_goal':6},new_completed_training_groups=0,root_independent_updates=278000,new_reviewed_arm_updates=1000,Object64_original500_root=ref(NR),Object64_original500_independent=ref(NI),Object64_continuous_publication=ref(PUB),Object64_GPU_submitted=False,Object64_continuous_waiting_for_capacity=True,Spatial64_continuous_job_id='3044479',Spatial_submission_failure_retained=spatial['original_failure'],Spatial_exact_pending_reconciliation=ref(B+'/Spatial3044479_pending_reconciliation.json'),new_root_GPU_submissions=['3044479'],new_duplicate_submissions=0,controller_owner=owner,scheduler=obs,capacity=cap,active_GPU_jobs=8,reserved_GPU_slots=ctl['reserved_GPU_slots'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,new_development_trials=0,all_historical_and_new_development_trials=1412,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=8;f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']='54/72 complete training groups root+independent accepted (Long18,Spatial16,Object14,Goal6),278000 reviewed arm updates. Object64seed23 recovery3044017 independently accepted at original500; separate exact500-to5000 admission ready, no GPU submission at full8. Spatial64seed23 continuous3044479 submitted once; initial accounting delay retained, exact ACK/token and actual Slurm identity reconciled without resubmission. Eight healthy GPU jobs continue under controller; no new development or final inference.'
 s['next_actions']=['Leave healthy automatic5000 training to controller; normal jobs do not need real-time polling, preserve11 validation nodes/full optimizer/RNG/cursor and max8 GPU slots.',
 'At next genuine spare unreserved capacity, Object64seed23 may use '+authref['path']+' SHA'+authref['sha256']+' and exact canonical object64 gateway after fresh full registry/owner/lease/server checkpoint checks. Original500 recovery3044017 passed root+independent; preserve69 failed GPU seconds and all blocked history. Do not resubmit original500 or restore legacy segment waits.',
 'Spatial64seed23 continuous3044479 is already registered and running under authorization1cdb14995f275d03557d86be1b565f615a005d911b994ce8c17a3d229e989411. Pending cleared only after exact original ACK/token/Slurm reconciliation. Keep failed transaction; do not call its once-only submit again.',
 'Proceed with remaining7 registered Long development200 shards only through exact authorization/reservation and common8-slot accounting; never rerun accepted3043709 or change checkpoints based on development. Spatial failed development continuation remains a separate bounded issue.',
 'All72 selected checkpoints+16reference identities+4suite complete development receipts and root globalrelease remain mandatory before final35200. Complete same-checkpoint O2A/component timing and all cost delivery.']
 s['next_allowed_action']=s['next_actions'][0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：正式训练仍为 **54/72组通过root与独立复核**（Long18、Spatial16、Object14、Goal6），**8卡并行，累计{seconds/3600:.3f} GPU小时**（含失败与运行中分配，非最终成本）。本轮新增Object64 seed23原目标500步恢复验收：A/B各500步、4000次使用且均为独立窗口，同初始化与完整40000次既定顺序，val0/500各204窗口；原失败发生在初始化前，恢复作业正确从头开始，不能称为已观察到旧optimizer/RNG恢复。两份500步resume实际SHA已复核，后续原训练器仍须完整恢复optimizer/RNG/cursor。原失败69秒＋恢复5141秒＝5210 GPU秒保留。新增1000已审臂更新，累计278000；尚未增加5000步完成组数。\\n\\n'.replace('\\\\n','\\n')
 text+=f'Spatial64 seed23已单次提交1500→5000连续作业3044479。提交ACK后Slurm账目短暂缺行，原失败事务与pending证据保留；按原job/token/完整身份完成双审补登记，未重发。Object64 seed23另行完成500→5000源码、CPU独审和真实server预检登记，当前8槽已满，等待真实空槽再走一次性准入；正常训练继续由控制器自动运行。所有173科学文件保持原字节，模型、方法、5000步调度及11次验证不变。\\n\\n本轮无新增科学闭环或测速，不据训练诊断推断未来监督收益。既有开发记录1412条保留，最终0/35200继续封存。全部非权重证据回存服务器Git工作区；权重留服务器。[本轮证据](../{B}/summary.json)。\\n\\n'.replace('\\\\n','\\n')
 text=text.replace('\\n','\n')
 short=f'{stamp} 更新：54/72组训练双审完成，8卡运行，累计{seconds/3600:.3f} GPU小时（非最终）。Object64 seed23原目标500步恢复双审通过，新增1000已审更新；独立500→5000续跑准入已登记，满槽等待。Spatial64 seed23连续作业3044479已单次启动，ACK后账目延迟经原身份补登记解决，无重复提交。173科学文件未变，原始失败和全部成本保留；本轮无新增开发/最终评测，最终0/35200封存。[收据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inv['files'];first,tail=p.read_text().split('\n',1);prior=h(p)
  p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=prior,after_sha256=h(p)))
 with (R/B/'root_operations/integrate_0238.py').open('xb') as stream:stream.write(Path(__file__).read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,new_GPU_jobs=['3044479'],Object64_new_submission=False,frozen_scientific_files=173))
 print(json.dumps(dict(status='integrated',complete=54,reviewed_updates=278000,active_GPU_jobs=8,GPU_hours=seconds/3600,summary=summary)),flush=True)
