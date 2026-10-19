from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0530'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_text())
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('integrate2130ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==48 and f['root_and_independent_reviewed_arm_updates']==247000
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 nr='results/formal_main_v2/libero_spatial/k64/seed23/training/segment_reviews/3043399.json';ni=nr.replace('.json','_independent.json')
 assert h(R/nr)=='065917e14e91cd28a37677e95563df96598fd7c343f439dab901a36e65d1bea5' and h(R/ni)=='6cfde8e029ab7b31f748175dfd052f75b1b5b3f457229a6abf689f8936afea5e'
 root=read(nr);ind=read(ni);assert root['status']=='passed' and ind['status']=='passed_original_target_recovery_only'
 assert root['completed_by_arm']==ind['completed_by_arm']=={'A':1500,'B':1500} and root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==11958
 prior=[x for x in f['completed_engineering_segments'] if x.get('suite')=='libero_spatial' and x.get('visual_tokens')==64 and x.get('seed')==23 and x.get('root_review') and x.get('independent_review')]
 assert {str(x['job_id']) for x in prior}=={'3024716','3025205'}
 previous={a:max(x['updates_by_arm'][a] for x in prior) for a in ['A','B']};assert previous=={'A':1000,'B':1000}
 for x in prior:
  a=read(x['root_review']);b=read(x['independent_review'])
  assert b['status']=='passed' and b['root_review_path']==x['root_review'] and b['root_review_sha256']==h(R/x['root_review'])
  assert a['completed_by_arm']=={arm:b['arms'][arm]['completed_updates'] for arm in ['A','B']}==x['updates_by_arm']
 increment=sum(1500-previous[a] for a in ['A','B']);assert increment==ind['new_reviewed_arm_updates']==1000
 f['completed_engineering_segments'].append(dict(job_id='3043399',suite='libero_spatial',visual_tokens=64,seed=23,status='passed_root_and_independent_original_target_recovery',updates_by_arm={'A':1500,'B':1500},allocated_gpu_seconds=3401,pair_total_gpu_seconds=11958,root_review=nr,root_review_sha256=h(R/nr),independent_review=ni,independent_review_sha256=h(R/ni),not_completed_formal_training=True,original_FAILED_retained=True))
 f['root_and_independent_reviewed_arm_updates']+=increment
 admission=read(B+'/Spatial_continuous_root_admission.json');assert admission['status']=='approved_for_one_future_capacity_checked_submission' and admission['new_GPU_submissions']==[]
 admref=ref(B+'/Spatial_continuous_root_admission.json')
 rec=ctl['downstream_reservations_consumed']['6e574361d66aaba7869b536082d9c605106bdaf2ec428f3ccb46ea986c8ef37a']
 assert rec['job_id']=='3043709' and ctl['reserved_GPU_slots']==0
 jr=next(j for j in s['registered_jobs'] if str(j['job_id'])=='3043709')
 assert jr['method_ids']==['A128_seed23','B128_seed23'] and jr['mode']=='development'
 reconciliation='results/formal_main_v2/engineering/supervision_delivery_2130/known_ack_reconciliation/root_commit_a1.json';assert h(R/reconciliation)=='e3da0ac2804e246b3919334f639ba71a6ab9f4de4c575a92b61dc75459948e18'
 assert read(reconciliation)['new_sbatch_calls']==0 and read(reconciliation)['state_written']
 assert h(R/B/'Long3043709_startup_observation.json')=='6871fcc550e47724609c79e3dff2fc84787e393f73fff9680e813f94c6d277ea'
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3043399']['status']=='COMPLETED' and obs['rows']['3043399']['elapsed_seconds']==3401
 assert obs['rows']['3043709']['status']=='RUNNING' and obs['queue']['3043709']['comment']==jr['downstream_gateway']['request_token']
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost'].get('allocated_gpu_seconds',0)
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 f['CUDA_startup_issue']['original_target_recovery_3043399'].update(status='passed_original1500_root_and_independent_continuous_admitted_not_submitted',root_review=ref(nr),independent_review=ref(ni),root_summary=ref(B+'/3043399_root_terminal.json'),original_target_completed_by_arm={'A':1500,'B':1500},recovery_GPU_seconds=3401,pair_GPU_seconds=11958,continuous5000_admission=admref,full5000_complete=False)
 scope=f['downstream_action_range_issue']['Long16_pre_execution_qualified_scope']
 scope.update(slot_reservation_activated=False,active_reserved_shard=None,submitted_shards=[dict(pair='k128_seed23',job_id='3043709',planned_trials=200,submission=ref('results/formal_main_v2/submissions/3043709.json'),reconciliation=ref(reconciliation),startup=ref(B+'/Long3043709_startup_observation.json'))],new_GPU_submissions=['3043709'],accepted_new_trials=0)
 keys=[k for k,v in f['completed_training_pairs'].items() if v.get('root_review') and v.get('independent_review') or v.get('terminal_root_and_independent_review')]
 assert len(keys)==24
 machine_complete=sum(v.get('trained_arms',0) for v in f['completed_training_pairs'].values())
 machine_pending=[k for k in f['completed_training_pairs'] if k not in keys]
 assert machine_complete==50 and machine_pending==['libero_object_k64_seed41']
 automatic_entry=f['completed_training_pairs'][machine_pending[0]]
 assert automatic_entry['machine_verification']['verification_kind']=='machine_automatic_not_independent'
 automatic_refs=automatic_entry['machine_verification']['machine_output']
 assert h(R/automatic_refs['path'])==automatic_refs['sha256']
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':12,'libero_goal':2}
 inventory=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_original_target_recovery_and_development_start',utc=now,root_independent_complete=48,machine_complete=machine_complete,machine_only_pending_root_and_independent=machine_pending,machine_output=automatic_refs,total_arms=72,completed_by_suite=suites,new_completed_training_groups=0,root_independent_updates=248000,new_reviewed_arm_updates=1000,Spatial_recovery=dict(root_review=ref(nr),independent_review=ref(ni),completed_by_arm={'A':1500,'B':1500},pair_GPU_seconds=11958,original_FAILED_retained=True,continuous_admission=admref),new_GPU_submissions=['3043709'],new_GPU_submission_mode='registered_Long128seed23_A_B_development200',known_ack_reconciliation=ref(reconciliation),new_duplicate_submissions=0,first_actual_new_action_startup=ref(B+'/Long3043709_startup_observation.json'),scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=ctl['reserved_GPU_slots'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,new_development_trials_accepted=0,prior_development_trials_preserved=f['completed_development_trials'],completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,normal_GPU_repeated_polling=False,server_only=True,scientific_files_unchanged=173))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary);f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 for x in f['parallel_execution'].get('awaiting_terminal_review',[]):
  if str(x['job_id'])=='3028522':x['status']='FAILED_retained_recovery3043399_original1500_passed_continuous5000_admitted_not_submitted'
  if str(x['job_id'])=='3028460':x['status']='FAILED_retained_recovery3039258_passed_continuous3042627_running'
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']='48/72 root-independent accepted groups;50/72 machine complete, Object64seed41 root/independent pending;Spatial64seed23 A/B1500 recovery root+independent passed with exact continuous5000 admission ready,not submitted. Long128seed23 development200 job3043709 running;known-ACK registration reconciled without resubmission. Healthy training left to controller.'
 s['next_actions']=['Normal controller continues auto5000 with11validation nodes,max8 GPUs and exact resume;leave healthy jobs to next scheduled supervision.','At next genuine free capacity use newly admitted Spatial64seed23 continuous1500to5000 gateway exactly once;preserve all four prior allocations and blocked history. No manual500 boundary restart.','At Long3043709 terminal,retain whole new-action provenance/trials/cost and perform original science plus new-action root/independent reviews before accepting development results. Never resubmit consumed6e574 authorization.','Continue outstanding original-target Object64seed23 CUDA recovery3028468 with its separately bound reservation and admission;do not treat prior failure as successful.','Keep old1212 development trials and all failures. All72 selected,16 references,4suite development receipts and root globalrelease precede final35200. No final opening or benefit claim from partial development results.']
 s['next_actions'].insert(1,'Review newly machine-completed Object64seed41 job3037535 with original root and independent evidence; 50 machine-complete is not 50 independently accepted. Controller has already refilled Goal64seed17 as3043762.')
 s['next_allowed_action']=s['next_actions'][1]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 detail=f'{stamp}：正式训练仍 **48/72组**完成并通过root/独立复核（Long18、Spatial16、Object12、Goal2）。控制器另完成Object64 seed41两组，机器完成共50/72；该新增pair仍待root与独立复核。控制器已自动补上Goal64 seed17作业3043762。Spatial64 seed23恢复作业3043399已完成原1500目标：两臂1500步、cursor12000、四次189窗口硬64验证完整；实际resume与候选身份核验通过。新增1000次已审臂更新，总248000。恢复3401 GPU秒及原失败73秒全部保留，四段合计11958 GPU秒；这不是5000组完成。专用连续1500→5000入口经CPU双审和真实输入检查后登记，尚未提交。\n\n'+f'**{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时**（含失败与运行中分配，非最终账单）。Long128 seed23的已登记A/B开发200条单次提交为3043709，实际新版动作入口与科学适配器已启动。首次提交后sacct短暂不可见，网关保留pending并停止；root按同一ACK、token、队列及完整登记对账，追加真实作业并消费预约，未重复sbatch。原失败收据保留，未将运行中trial作为验收结果。\n\n'+f'原1212开发记录保留，最终0/35200封存，尚无新增成功率—延迟结论。正常训练交控制器，下次定时监督处理终态与空槽。[本轮收据](../{B}/summary.json)。\n\n'
 short=f'{stamp} 更新：50/72组机器训练完成，其中48/72组通过root/独立复核，Object64 seed41待审；{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时（非最终）。Spatial64 seed23原1500步恢复通过双审，连续5000入口已登记未提交；Long128 seed23开发200条作业3043709运行，提交登记延迟已按原token对账，无重复提交。未新增已验收闭环结果，最终0/35200封存。[本轮收据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式CUDA启动失败恢复登记','正式Long其余16选择器开发登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];prior_text=p.read_text();first,tail=prior_text.split('\n',1);oldsha=h(p)
  p.write_text(first+'\n\n'+(detail if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 rel='scripts/ops/formal_action_deployment_v1/README.md';p=R/rel;beforetext=p.read_text();first,tail=beforetext.split('\n',1);oldsha=h(p)
 p.write_text(first+'\n\nCurrent status, 2026-10-20 CST: the first exact Long128 seed23 fresh A/B development200 shard is running as3043709. A delayed accounting row stopped its original submission transaction after ACK; root reconciled the exact existing job/token and consumed its own reservation with zero new sbatch calls. Original failure evidence is retained. Runtime identity and original scientific adapter startup are observed, not terminal scientific acceptance. The other7 shard authorizations remain unused. See results/formal_main_v2/preflight/heartbeat_20261020T0530/summary.json.\n\nThe earlier status paragraphs below are retained historical snapshots.\n\n'+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 ops=R/B/'root_operations';ops.mkdir(exist_ok=True)
 for name in ['observe_formal_2130.py','dispatch_long128seed23_2130.py','review_spatial_recovery_2130.py','publish_spatial_recovery_2130.py','archive_initial_delivery_2130.py','archive_terminal_delivery_2130.py','capture_long3043709_startup_2130.py','integrate_2130.py','integrate_2130_v2.py','archive_spatial_continuous_author_2130.py']:
  p=R/'.local'/name;compile(p.read_bytes(),name,'exec')
  with (ops/name).open('xb') as stream:stream.write(p.read_bytes())
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_2032_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(schema='formal_main_v2',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,fresh_Slurm_cost_accounting=True,new_GPU_submissions=['3043709'],no_duplicate_sbatch=True,weights_local_copy=False))
 print(json.dumps(dict(status='supervision_integrated',summary=summary,occupied=len(cap['occupied']),GPU_hours=seconds/3600,root_complete=48,reviewed_updates=248000,Long_job='3043709',Spatial_continuous_registered_not_submitted=True)))
