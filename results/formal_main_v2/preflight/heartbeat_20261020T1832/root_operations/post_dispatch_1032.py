from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1832';E='results/formal_main_v2/engineering/supervision_delivery_1032'
NR='results/formal_main_v2/libero_spatial/k64/seed23/training/segment_reviews/3044479.json';NI=NR.replace('.json','_independent.json')
IND='.local/Spatial64seed23_terminal_1032/independent_review.json'
PACKAGES=[{"base":".local/Spatial64seed23_terminal_1032","manifest":"delivery_manifest.json","sha256":"c35515aab808512f5c5399d8397de282c386efd0e75aec325d99c7bb171f7328","archive":"Spatial64seed23_terminal_independent"},{"base":".local/nonLong_submission_independent_1032","manifest":"manifest.json","sha256":"8d14504315dc0425b1ff1b3af44444414e0103a7c4c34211c59d486fce839f85","archive":"nonLong_submission_independent"}]
ARCHIVE_REVIEW={"path":".local/Spatial64seed23_terminal_1032/archive_delivery_independent.json","sha256":"ec63f0943664bbccbed865d40d440b0c72da3c2e33cbfdd3d704c847193de082"}
SUB_REVIEW={"path":".local/nonLong_submission_independent_1032/independent_review.json","sha256":"c95c89c24e9825fe28ac8eae4470ae8f3c9d45dbc15efe19d2a9646b35af39fc"}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def rd(rel,pin=None):
 if pin:assert h(R/rel)==pin,rel
 return json.loads((R/rel).read_bytes())
def clone(rel,raw):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as stream:stream.write(raw)
 return ref(rel)
def save(rel,x):return clone(rel,(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','dispatch1032ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=rd('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None
 assert f['root_and_independent_completed_arms']==62 and f['root_and_independent_reviewed_arm_updates']==314000
 assert f['completed_development_trials']==2812 and f['current_action_development_trial_count']==1600
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert 'libero_spatial_k64_seed23' not in f['completed_training_pairs']
 root=rd(NR,'12ab9843ba7bd1982d4bbc1004b733db4a4d97ee2deb9863e3cfb9767add510c')
 ind=rd(IND,'cc04fd98fd39a2159ca32775167f262efcdd528ad3bb4945c4998d025fe7f554')
 selectedbytes=rd(B+'/3044479_selected_server.json','c20da6354cec2198dc12399b88ddf85d88d63525e2dbd3d7477e691fa8a8fbe6')
 assert root['status']=='passed' and ind['status']=='passed_complete_training_only'
 assert root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000}
 assert ind['prior_completed_by_arm']=={'A':1500,'B':1500} and ind['new_reviewed_arm_updates']==7000
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==42480
 assert ind['cost']['continuous_allocation_GPU_seconds']==30522 and ind['cost']['retained_FAILED_GPU_seconds']==73
 assert ind['same_AB_initialization_and_full40000_order'] and ind['source173_R_S_mirror_match']
 assert ind['historical_failure_preserved_and_rebuilt'] and not ind['scientific_closed_loop_claimed'] and not ind['final_release_authorized']
 assert ind['root_review']==ref(NR) and ind['selected_server_review']==ref(B+'/3044479_selected_server.json')
 for path,pin in ind['read_evidence_sha256'].items():assert h(R/path)==pin,path
 arev=rd(ARCHIVE_REVIEW['path'],ARCHIVE_REVIEW['sha256'])
 subrev=rd(SUB_REVIEW['path'],SUB_REVIEW['sha256'])
 assert arev['status']=='passed_archive_reconstruction_and_historical_raw_Git_identity' and subrev['status']=='passed'
 selected=[]
 for arm,update in [('A',2500),('B',3500)]:
  dr='results/formal_main_v2/libero_spatial/k64/seed23/training/'+arm+'/deployment_receipt.json';d=rd(dr);a=ind['arms'][arm]
  assert a['completed_updates']==5000 and a['sample_uses']==a['cursor']==40000 and a['unique_windows']==34703
  assert d['checkpoint_sha256']==a['best']['sha256'] and d['metadata']['update']==a['selected_update']==update
  assert d['metadata']['validation_metric']==a['selected_teacher_l1']
  assert [e['update'] for e in d['evaluations']]==list(range(0,5001,500))
  rawbest=Path(a['best']['path']);st=rawbest.stat();assert h(rawbest)==a['best']['sha256'] and rawbest.stat()==st
  selected.append(dict(arm=arm,path=str(rawbest),expected_sha256=a['best']['sha256'],selected_update=update,validation_metric=a['selected_teacher_l1'],metadata_source=ref(dr)))
 bindings=[('3048572','libero_spatial',23,['A128_seed23','B128_seed23'],200,'4a47032c83c03e81ac1297aa4c3f4ff31fc780a700990e7cb335c89cf65dbab4','Spatial'),('3048581','libero_object',23,['A128_seed23','B128_seed23'],200,'9ee17e773f283ff81ca70e25ed0ab8afac7abf5ce5de73ef81625db768b0509b','Object'),('3048609','libero_goal',17,['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'],600,'a686142e3af91491d83444270b51b2fbac1f95e7a0f95fd7a0f64f4fa374e89f','Goal')]
 submissions=[]
 for jid,suite,seed,methods,trials,apin,label in bindings:
  job=next(j for j in s['registered_jobs'] if str(j['job_id'])==jid)
  assert sum(str(j['job_id'])==jid for j in s['registered_jobs'])==1
  assert job['suite']==suite and job['method_ids']==methods
  authpath='results/formal_main_v2/execution/nonLong_action_v1_1032/'+suite+'_k128_seed'+str(seed)+'/submission_authorization.json'
  auth=rd(authpath,apin);ar=ref(authpath);ad='results/formal_main_v2/downstream_gateway/'+apin
  rec=rd(B+'/'+label+jid+'_pending_reconciliation.json')
  assert rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0
  assert all(rec['job'][k]==job[k] for k in rec['job'] if k not in {'status','elapsed_seconds','exit_code','node','allocation'})
  assert rd(ad+'/committed.json')['root_reconciliation']==ref(B+'/'+label+jid+'_pending_reconciliation.json')
  ack=rd(ad+'/sbatch_result.json');assert ack['returncode']==0 and ack['stdout']==jid+'\n'
  assert ctl['downstream_reservations_consumed'][apin]['job_id']==jid
  assert (R/job['invocation']).read_bytes()==(P/job['invocation']).read_bytes()
  submissions.append(dict(job_id=jid,suite=suite,seed=seed,method_ids=methods,planned_trials=trials,unique_development_initial_states=100,completed_trials_accepted=0,authorization=ar,root_reconciliation=ref(B+'/'+label+jid+'_pending_reconciliation.json'),original_failed_transaction=ref(ad+'/failed_transaction.json'),original_ACK=ref(ad+'/sbatch_result.json'),independent_submission_review=SUB_REVIEW,duplicate_submissions=0,final_evaluation_enabled=False))
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3044479']['status']=='COMPLETED' and obs['rows']['3044479']['elapsed_seconds']==30522
 for row in submissions:row['observed_status']=obs['rows'][row['job_id']]['status'];row['scientific_terminal_acceptance_pending']=True
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 owner=rd('results/formal_main_v2/autonomous_training/run_v1/owner.json');assert owner['owner_id']==ctl['owner_id']=='6b3beba5cdeb41df9d749b0b2054d485'
 with Path(owner['lock']).open('rb') as stream:
  held=False
  try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(stream,fcntl.LOCK_UN)
  except BlockingIOError:held=True
 assert held
 deliveries=[];published={}
 for item in PACKAGES:
  base=Path(item['base']);mp=base/item['manifest'];m=rd(mp.as_posix(),item['sha256']);rows=[]
  for original in m['files']:
   row=dict(original);name=Path(row['path'])
   if not name.is_relative_to(base):name=base/name
   assert name.is_relative_to(base) and not name.is_absolute() and '..' not in name.parts
   row['path']=name.as_posix();rows.append(row)
  rows.append(dict(path=mp.as_posix(),sha256=h(R/mp),bytes=(R/mp).stat().st_size));copies=[]
  for row in rows:
   src=R/row['path'];assert src.is_file() and not src.is_symlink() and h(src)==row['sha256'] and src.stat().st_size==row['bytes']
   assert src.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc','.npz','.npy'] and src.stat().st_size<100*(1<<20)
   dst=E+'/'+item['archive']+'/'+Path(row['path']).relative_to(base).as_posix()
   out=clone(dst,src.read_bytes());copies.append(dict(source=row,archive=out));published[row['path']]=out
  deliveries.append(save(B+'/'+item['archive']+'_delivery.json',dict(source_manifest=ref(mp.as_posix()),copies=copies,no_source_transformation=True,new_GPU_jobs=0)))
 clone(NI,(R/IND).read_bytes())
 binding=save(B+'/3044479_selected_binding.json',dict(status='root_and_independent_selected_identity_verified',root_review=ref(NR),independent_review=ref(NI),actual_server_bytes=ref(B+'/3044479_selected_server.json'),selected_checkpoints=selected,weights_copied=False))
 for row in submissions:row['independent_submission_review']=published[SUB_REVIEW['path']]
 f['completed_training_pairs']['libero_spatial_k64_seed23']=dict(job_id='3044479',suite='libero_spatial',visual_tokens=64,seed=23,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),selected_checkpoints=selected,selected_server_review=binding['path'],selected_server_review_sha256=binding['sha256'],verification_kind='root_startup_consumer_and_independent_raw_reconstruction',trained_arms=2,completed_by_arm={'A':5000,'B':5000},allowed_next_segment_end=None,machine_original_outcome=None,historical_failure_retained=ref('results/formal_main_v2/libero_spatial/k64/seed23/training/startup_failure_reviews/3028522.json'),historical_original1500_dual_review=ind['historical_dual_review_receipts'])
 f['trained_arms']=2*len(f['completed_training_pairs']);assert f['trained_arms']==64
 f['root_and_independent_completed_arms']=64;f['root_and_independent_reviewed_arm_updates']+=7000
 f['completed_engineering_segments'].append(dict(job_id='3044479',suite='libero_spatial',visual_tokens=64,seed=23,status='passed_root_and_independent_complete_training',updates_by_arm={'A':5000,'B':5000},allocated_gpu_seconds=30522,pair_total_gpu_seconds=42480,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),new_reviewed_arm_updates=7000,prior_root_independent_updates_per_arm=1500))
 tracking=f['parallel_execution']['pair_tracking']['libero_spatial_k64_seed23'];priortracking=copy.deepcopy(tracking)
 tracking.update(training_complete=True,last_completed_job_id='3044479',last_root_reviewed_common_update=5000,allowed_next_segment_end=None,root_review=NR,independent_review=NI,selected_server_review=binding['path'],selected_server_review_sha256=binding['sha256'],prior_preterminal_tracking=priortracking)
 issue=f['CUDA_startup_issue'];issue['continuous_after3043399'].update(status='passed_root_and_independent_complete5000',root_terminal_review=ref(NR),independent_terminal_review=ref(NI),prior_failure_retained=True)
 objectdone=f['completed_training_pairs']['libero_object_k256_seed23']
 issue['continuous_after3039258'].update(status='passed_root_and_independent_complete5000',root_terminal_review=ref(objectdone['root_review']),independent_terminal_review=ref(objectdone['independent_review']),prior_failure_retained=True)
 issue['status']='Object256_and_Spatial64_complete5000_Object64_continuous_registered'
 issue['next']='Object64seed23 continuous3044844 already submitted; inspect its real terminal evidence at next supervision. Do not replay any prior recovery/continuation submission.'
 issue['scheduler_next']=issue['next']
 for row in f['parallel_execution'].get('awaiting_terminal_review',[]):
  if row['job_id']=='3028522':row.update(status='FAILED_retained_recovery_and_full5000_dual_reviewed',terminal_job_id='3044479',terminal_root_review=ref(NR),terminal_independent_review=ref(NI))
  elif row['job_id']=='3028460':row.update(status='FAILED_retained_recovery_and_full5000_dual_reviewed',terminal_job_id='3042627',terminal_root_review=ref(objectdone['root_review']),terminal_independent_review=ref(objectdone['independent_review']))
  elif row['job_id']=='3028468':row.update(status='FAILED_retained_original500_passed_continuous3044844_registered',continuous_job_id='3044844')
 assert 'nonLong_development_submissions_1032' not in f;f['nonLong_development_submissions_1032']=submissions
 suites={suite:2*sum(k.startswith(suite+'_k') for k in f['completed_training_pairs']) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':18,'libero_object':16,'libero_goal':12}
 for k,v in f['completed_training_pairs'].items():
  if v.get('root_review') and v.get('independent_review'):
   for role in ['root_review','independent_review']:assert h(R/v[role])==v[role+'_sha256']
  else:
   x=v['terminal_root_and_independent_review'];assert x['completed_by_arm']=={'A':5000,'B':5000}
   for role in ['root_review','independent_review']:assert ref(x[role]['path'])==x[role]
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 next_actions=['Leave healthy registered training and development running; no in-turn normal-job polling.',
 'At next supervision accept genuine terminals for remaining8 training arms and nonLong1000 development trials only after original root+independent evidence checks. Never repeat3048572/3048581/3048609 submissions.',
 'Prepare further pre-registered nonLong development groups for actual available slots; all seeds, budgets and initial states remain fixed. Preserve original failed/development versions and replay costs.',
 'Preserve Long22 development negative128 contrast: A95.67%,B93%,paired B-A -2.67pp CI[-4.33,-1]pp. Other budgets intervals crosszero. No result-driven tuning.',
 'Complete all88deployment identities/four-suite development freeze before fullO2A/components under registered gates; final35200 needs original root globalrelease. Do not read final values.']
 summary=save(B+'/summary_after_dispatch.json',dict(schema='formal_main_v2',kind='Long_development_accepted_Spatial_training_closed_nonLong_development_dispatched',utc=now,
  prior_same_heartbeat_summary=ref(B+'/summary.json'),root_independent_complete=64,total_arms=72,completed_by_suite=suites,root_independent_updates=321000,new_completed_training_groups=2,new_reviewed_arm_updates=7000,
  Spatial64seed23_root=ref(NR),Spatial64seed23_independent=ref(NI),selected_identity=binding,all_training_pair_GPU_seconds=42480,latest_training_allocation_GPU_seconds=30522,retained_failure_GPU_seconds=73,
  samples_per_arm=40000,unique_windows_per_arm=34703,effective_epochs=40000/34703,validation_nodes=11,validation_windows=189,
  raw_archive=ref('results/formal_main_v2/nonweight_archives/v1/snapshots/Spatial64seed23_20261020_1032.json'),archive_independent_review=published[ARCHIVE_REVIEW['path']],
  Long_development_statistics=f['Long22_development_statistics'],all_raw_development_trials=2812,current_wrapper_actual_trials=1600,Long_compatible_development_trials=2200,Long_unique_initial_states=100,
  new_development_trials_accepted=0,new_planned_development_trials=1000,new_GPU_submissions_by_root=[x[0] for x in bindings],development_submissions=submissions,new_duplicate_submissions=0,
  scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),actual_running_GPUs=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING'),
  allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,independent_deliveries=deliveries,source_files_unchanged=173,controller_lease_held=True,normal_training_left_to_controller=True,
  completed_final_trials=0,expected_final_trials=35200,final_sealed=True,server_only=True,next=next_actions))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']=f'64/72 root+independent training groups complete,321000 reviewed arm updates;Long18,Spatial18,Object16,Goal12. Spatial64seed23 full5000 accepted after original1500; historical73sec failure retained. Three new nonLong development jobs3048572/3048581/3048609 registered once,1000 planned; no new terminal scientific results accepted. Long22 development2200 compatible records over100 unique states,128 B-A negative2.67pp. {len(cap["occupied"])} occupiedGPU,{seconds/3600:.3f}GPUh. Final0/35200sealed.'
 s['next_actions']=next_actions;s['next_allowed_action']=next_actions[0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 assert f['new_action_development_verified_by_job']==old['formal_main_progress']['new_action_development_verified_by_job']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：训练 **64/72组双审完成**（Long18、Spatial18、Object16、Goal12），本轮新增Spatial64 seed23的A/B完整5000步，沿原规则选A2500/B3500。各40000窗口使用、34703唯一窗口、11×189验证；原CUDA失败73GPU秒及全部恢复成本保留。\n\n'
 text+=f'已一次提交Spatial128 seed23 A/B（3048572，200条）、Object128 seed23 A/B（3048581，200条）、Goal参考及128 seed17 A/B（3048609，600条）。共同10任务×10开发初态，各身份与原包装入口经root及独审核验；3次提交后的记账延迟均按原ACK/token对账登记，没有重复提交。新1000条尚待终态验收，不计入已完成成功率。当前{len(cap["occupied"])}个GPU作业占槽，实分配累计 **{seconds/3600:.3f} GPU小时**（非最终）。\n\n'
 text+='Long22方法开发2200条（100唯一初态）的结论保持：128预算A95.67%、B93.00%，B−A为−2.67pp，95%配对区间[−4.33,−1.00]pp；256和64区间跨零，尚不支持稳定收益或等效。训练、开发继续按原矩阵；完整测速与最终35200条仍按全局冻结门槛推进。\n\n'
 text+=f'[本轮汇总](../{B}/summary_after_dispatch.json)，[Long完整开发结果](正式Long完整开发结果.md)。\n\n'
 short=f'{stamp}：64/72训练组双审完成；新非Long开发3批共1000条已一次登记，{len(cap["occupied"])}GPU占槽，累计{seconds/3600:.3f}GPU小时。Long128开发差值为−2.67pp，保留负结果。最终0/35200封存。见[本轮汇总](../{B}/summary_after_dispatch.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
  rel='docs/'+name+'.md';assert rel not in inventory['files'];p=R/rel;prior=h(p);first,tail=p.read_text().split('\n',1);p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=prior,after_sha256=h(p)))
 longdoc=R/'docs/正式Long完整开发结果.md';txt=longdoc.read_text();assert '本轮没有新GPU作业。' in txt
 txt=txt.replace('本轮没有新GPU作业。','Long等价证明与统计复核没有额外GPU作业；后续非Long开发批次另记成本。',1)
 longdoc.write_text(txt)
 clone(B+'/root_operations/post_dispatch_1032.py',Path(__file__).read_bytes())
 save(B+'/post_dispatch_integration.json',dict(status='integrated',summary=summary,state_before_sha256=before,state_after_sha256=h(sp),docs=docs,controller_and_registry_unchanged=True,new_training_groups=2,new_GPU_submissions=[x[0] for x in bindings],final_release=False))
 print(json.dumps(dict(status='integrated',completed_training_groups=64,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)
