from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1133';E='results/formal_main_v2/engineering/supervision_delivery_0333'
NR='results/formal_main_v2/libero_goal/k256/seed41/training/segment_reviews/3038735.json';NI=NR.replace('.json','_independent.json')
MAN='.local/independent_goal3038735_0333/delivery_files.json';IND='.local/independent_goal3038735_0333/3038735_independent_review.json'
OMAN='.local/independent_object3044844_0333/manifest.json';OIND='.local/independent_object3044844_0333/independent_review.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return {'path':rel,'sha256':h(R/rel)}
def read(rel):return json.loads((R/rel).read_text())
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return read(rel)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
 return ref(rel)
def archive_manifest(rel,pin,subdir):
 manifest=checked(rel,pin);copies=[]
 rows=manifest['files']+[dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)]
 for row in rows:
  source=R/row['path'];assert source.parent==R/Path(rel).parent and source.is_file() and not source.is_symlink()
  assert h(source)==row['sha256'] and source.stat().st_size==row['bytes']
  assert source.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc'] and source.stat().st_size<100*(1<<20)
  dest=R/E/subdir/source.name;dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(source.read_bytes())
  copies.append(dict(source=row,archive=ref(dest.relative_to(R).as_posix())))
 return copies
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('root_integrate0333',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==54 and f['root_and_independent_reviewed_arm_updates']==278000
 assert f['completed_development_trials']==1412 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 root=checked(NR,'b29aa269ce5efeecebfe0d2f85788a27ac379a3c52376ece37837411ffee1216')
 ind=checked(IND,'3180f2b14f40724f868e049449faf3fe5343f3145febf26168018b4a957800df')
 assert root['status']=='passed' and ind['status']=='passed_complete_training_only' and root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000}
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==75309
 assert ind['cost']['allocations']==[{'GPU_seconds':75309,'job_id':'3038735'}]
 assert ind['same_AB_initialization_and_full40000_order'] and ind['all173_R_and_S_match']
 assert not ind['scientific_closed_loop_claimed'] and not ind['final_release_authorized']
 proof=ind['parallel_root_reconstruction'];assert proof['path']==NR and proof['sha256']==h(R/NR) and proof['new_reviewed_arm_updates']==10000 and proof['fresh_pair']
 assert proof['selected_server_proof']==ref(B+'/3038735_selected_server.json')
 for path,pin in ind['read_evidence_sha256'].items():assert h(R/path)==pin,path
 copies=archive_manifest(MAN,'0d719933035ab601d4a5b0530e13e940aebc195ed9289c5b43f5bef1a4593944','Goal256seed41_independent')
 with (R/NI).open('xb') as stream:stream.write((R/IND).read_bytes())
 delivery=save(B+'/Goal3038735_independent_delivery.json',dict(copies=copies,canonical=ref(NI),source_manifest=ref(MAN),no_GPU_execution=True))
 oind=checked(OIND,'c8480bd8d11d671fb740688d75753a442c4ff66f5189aa0f4f678d473aee0a78');assert oind['status']=='passed' and oind['job_id']=='3044844' and oind['blockers']==[] and oind['kind']=='object64_continuous_pending_reconciliation_independent_review'
 ocopies=archive_manifest(OMAN,'a8b6290e3da0d8c1d44e79e743d5a62b1d37a108508550797dfa02037c27cedb','Object64_pending_independent')
 oref=ref(E+'/Object64_pending_independent/'+Path(OIND).name)
 odelivery=save(B+'/Object3044844_independent_delivery.json',dict(copies=ocopies,independent_report=oref,no_GPU_execution=True))
 rec=checked(B+'/Object3044844_pending_reconciliation.json','1b9d5580870d2943dd0565081d53950e4e740f6e555def890f7386861d3e0455')
 assert rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0 and rec['job']['job_id']=='3044844'
 ad='results/formal_main_v2/continuous_admissions/3044017/6619bd4e9a8e75b76200bca401a861bc5c6c1180a54c37cf739da18f55ea019c'
 assert read(ad+'/committed.json')['root_reconciliation']==ref(B+'/Object3044844_pending_reconciliation.json')
 jobs=[j for j in s['registered_jobs'] if str(j['job_id'])=='3044844'];assert len(jobs)==1
 assert jobs[0]['invocation_sha256']=='f494c0f2377d59a59fa1ed2b6ea061c20dc4e63ebb81e834ef5603d02cde0446'
 entry=f['completed_training_pairs']['libero_goal_k256_seed41'];assert entry['verification_kind']=='machine_automatic_not_independent'
 selected=[]
 for a in ['A','B']:
  dr='results/formal_main_v2/libero_goal/k256/seed41/training/'+a+'/deployment_receipt.json';d=read(dr);ar=ind['arms'][a]
  assert ar['completed_updates']==5000 and ar['sample_uses']==40000 and ar['unique_windows']==33859 and ar['cursor']==40000
  assert d['checkpoint_sha256']==ar['best_sha256'] and d['metadata']['update']==ar['earliest_selected_update'] and d['metadata']['validation_metric']==ar['selected_teacher_l1']
  selected.append(dict(arm=a,path='/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k256/seed41/'+a+'/best.pt',expected_sha256=d['checkpoint_sha256'],selected_update=ar['earliest_selected_update'],validation_metric=ar['selected_teacher_l1'],metadata_source=ref(dr)))
 binding=save(B+'/3038735_selected_binding.json',dict(status='root_and_independent_selected_identity_verified',root_review=ref(NR),independent_review=ref(NI),actual_server_bytes=ref(B+'/3038735_selected_server.json'),selected_checkpoints=selected,weights_copied=False))
 entry.update(job_id='3038735',suite='libero_goal',visual_tokens=256,seed=41,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),selected_checkpoints=selected,selected_server_review=binding['path'],selected_server_review_sha256=binding['sha256'],verification_kind='machine_automatic_plus_root_and_independent_raw_reconstruction')
 assert not any(x.get('suite')=='libero_goal' and x.get('visual_tokens')==256 and x.get('seed')==41 and x.get('root_review') and x.get('independent_review') for x in f['completed_engineering_segments'])
 f['root_and_independent_completed_arms']=56;f['root_and_independent_reviewed_arm_updates']+=10000
 f['completed_engineering_segments'].append(dict(job_id='3038735',suite='libero_goal',visual_tokens=256,seed=41,status='passed_root_and_independent_complete_training',updates_by_arm={'A':5000,'B':5000},allocated_gpu_seconds=75309,pair_total_gpu_seconds=75309,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),new_reviewed_arm_updates=10000))
 f['object64seed23_continuous_ready'].update(GPU_submitted=True,job_id='3044844',status='submitted_once_pending_accounting_delay_reconciled',reconciliation=ref(B+'/Object3044844_pending_reconciliation.json'),independent_submission_review=oref,failure_retained=ref(ad+'/failed_transaction.json'))
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8 and obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 assert obs['rows']['3038735']['status']=='COMPLETED' and obs['rows']['3038735']['elapsed_seconds']==75309
 assert obs['rows']['3044844']['status'] in ['RUNNING','PENDING','CONFIGURING'] and '3044844' in cap['occupied']
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds'];s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 keys=[]
 for k,v in f['completed_training_pairs'].items():
  if v.get('root_review') and v.get('independent_review'):
   for role in ['root_review','independent_review']:assert h(R/v[role])==v[role+'_sha256']
   keys.append(k)
  elif v.get('terminal_root_and_independent_review'):
   x=v['terminal_root_and_independent_review'];assert x['completed_by_arm']=={'A':5000,'B':5000}
   for role in ['root_review','independent_review']:assert ref(x[role]['path'])==x[role]
   keys.append(k)
 assert len(keys)==28
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':14,'libero_goal':8}
 inventory=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 next_actions=['Leave healthy auto5000 training to the controller; next scheduled heartbeat handles terminals and exceptions, no continuous in-turn polling.',
 'Object64 seed23 continuation3044844 and Spatial64 seed23 continuation3044479 are already registered once. Do not resubmit or clear original historical CUDA failure blocks.',
 'Proceed with the remaining registered development and latency work through exact authorization and shared8-slot accounting as slots become available; never rerun accepted Long3043709.',
 'All72 selected checkpoints+16reference identities+4suite complete development receipts and root globalrelease remain required before final35200; no final-state reading or result-based reselection.']
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_training_accepted_and_slot_refilled',utc=now,root_independent_complete=56,machine_complete=f['trained_arms'],completed_by_suite=suites,total_arms=72,new_completed_training_groups=2,root_independent_updates=288000,new_reviewed_arm_updates=10000,Goal256seed41_root=ref(NR),Goal256seed41_independent=ref(NI),selected_identity=binding,independent_delivery=delivery,training_sample_uses_per_arm=40000,unique_training_windows_per_arm=33859,second_traversal_uses_per_arm=6141,validation_nodes_per_arm=11,validation_windows_per_node=186,terminal_pair_GPU_seconds=75309,new_development_trials_accepted=0,all_historical_and_new_development_trials=1412,new_GPU_submissions_by_root=['3044844'],Object64_continuation=ref(B+'/Object3044844_pending_reconciliation.json'),Object64_submission_independent=oref,original_ack_accounting_delay_reconciled_no_resubmit=True,new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=ctl['reserved_GPU_slots'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173,nonweight_archive=ind['archive_reconstruction']['snapshot'],raw_bytes=182651083,independent_review_limitations=ind['limitations'],next=next_actions))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']=f'56/72 complete groups root+independent accepted (Long18,Spatial16,Object14,Goal8),288000 reviewed arm updates. New Goal256seed41 fresh A/B5000,11x186 validations,40000 uses/33859 unique windows,A3000/B4500 selected. Object64seed23 continuation3044844 registered once after exact accounting-delay reconciliation;{len(cap["occupied"])} active GPUs. Development1412 unchanged and final0/35200 sealed.'
 s['next_actions']=next_actions;s['next_allowed_action']=next_actions[0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：正式训练 **56/72组通过root与独立复核**（Long18、Spatial16、Object14、Goal8）。新增Goal256 seed41 A/B各5000步；原始记录独立重建11×186硬剪枝验证、相同初始化和完整40000次采样顺序，33859个唯一窗口及第二轮6141次使用，零重放。A选3000、B选4500步，teacher L1分别0.00792110/0.00786009；best/resume实际SHA、173份科学源、Goal官方组件和182651083字节非权重日志无损重建均通过。新增10000已审臂更新，累计288000；该pair完整75309 GPU秒计入总账，不叠加内部阶段耗时。本pair为从头单次训练，无跨作业恢复；optimizer/RNG张量未在本次独审反序列化，恢复资格继承原Goal F03验收。\n\n'
 text+=f'本轮将真实空槽补入Object64 seed23连续500→5000，唯一作业3044844；提交后Slurm即时记账缺行已按原ACK、精确token、scontrol和全登记作业对账解决，无重发，历史失败与5210 GPU秒恢复前成本保留。当前 **{len(cap["occupied"])}卡活动，正式轮累计{seconds/3600:.3f} GPU小时**（含失败和运行中分配，非最终成本）。Spatial3044479继续运行，173科学文件和全部方法设置未改变。此次仅确认训练与身份，不据离线误差判断闭环收益；原开发1412条保留，本轮无新增开发，最终0/35200继续封存。正常运行交自动控制器，下次定时监督处理终态。[本轮收据](../{B}/summary.json)。\n\n'
 short=f'{stamp}：56/72组训练双审通过，新增Goal256 seed41 A/B各5000步、11×186验证，A/B分别选3000/4500。Object64 seed23从双审500步断点单次续跑至5000（3044844），记账延迟按原ACK对账，无重复提交。{len(cap["occupied"])}卡活动，正式轮累计{seconds/3600:.3f} GPU小时（非最终）。本轮无新增闭环收益或延迟结论，开发1412条保留，最终0/35200封存。非权重结果完整归档，权重仅服务器。[本轮证据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];first,tail=p.read_text().split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 for name in ['observe_formal_0333.py','submit_object64_continuation_0333.py','reconcile_object64_pending_0333.py','review_terminal_0333.py','archive_results_0333.py','integrate_0333.py']:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec')
  with (op/name).open('xb') as stream:stream.write(raw)
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_0238_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,new_GPU_jobs=['3044844'],frozen_scientific_files=173,normal_gpu_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=56,reviewed_updates=288000,new_development=0,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)
