from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1426';E='results/formal_main_v2/engineering/supervision_delivery_0626'
NR='results/formal_main_v2/libero_object/k256/seed23/training/segment_reviews/3042627.json';NI=NR.replace('.json','_independent.json')
IND='.local/independent_object3042627_0626/independent_review.json';MAN='.local/independent_object3042627_0626/manifest.json'
LD='.local/independent_long256_development_0626';SD='.local/independent_long_submissions_0626'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_bytes())
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return read(rel)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as stream:json.dump(x,stream,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
 return ref(rel)
def manifest_rows(rel,pin):
 manifest=checked(rel,pin);base=Path(rel).parent;rows=[]
 for raw in manifest['files']:
  row=dict(raw);rp=Path(row['path'])
  if not rp.is_relative_to(base):rp=base/rp
  assert rp.is_relative_to(base) and '..' not in rp.parts and not rp.is_absolute(),rp
  row['path']=rp.as_posix();rows.append(row)
 rows.append(dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size))
 seen=set()
 for row in rows:
  assert row['path'] not in seen;seen.add(row['path']);p=R/row['path']
  assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to((R/base).resolve())
  assert h(p)==row['sha256'] and p.stat().st_size==row['bytes'],row['path']
  assert p.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc'] and p.stat().st_size<100*(1<<20)
 for row in manifest.get('execution_audits',[]):
  assert h(R/row['path'])==row['sha256'] and (R/row['path']).stat().st_size==row['bytes']
 return rows,base
def archive(rows,base,subdir):
 copies=[]
 for row in rows:
  source=R/row['path'];dest=R/E/subdir/Path(row['path']).relative_to(base);dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as stream:stream.write(source.read_bytes())
  copies.append(dict(source=row,archive=ref(dest.relative_to(R).as_posix())))
 return copies
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('root_integrate0626',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==60 and f['root_and_independent_reviewed_arm_updates']==305000
 assert f['completed_development_trials']==1612 and f['current_action_development_trial_count']==400 and f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 assert ctl['reserved_GPU_slots']==0 and 'libero_object_k256_seed23' not in f['completed_training_pairs']
 root=checked(NR,'ef4fa5c45dd73db1fef8f68a18d563959b408337cd3a1992613d673e15540e0a')
 ind=checked(IND,'e87a594516432526e718b80bd284146c164eac1c42f864c5bc349a3c42a83c98')
 assert root['status']=='passed' and ind['status']=='passed_complete_training_only' and root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000}
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==58917
 assert ind['cost']['allocations']==[{'GPU_seconds':84,'job_id':'3028460'},{'GPU_seconds':6512,'job_id':'3039258'},{'GPU_seconds':52321,'job_id':'3042627'}]
 assert ind['same_AB_initialization_and_full40000_order'] and ind['all173_R_S_and_mirror_match'] and ind['new_reviewed_arm_updates']==9000
 assert ind['historical_failure_preserved_and_rebuilt'] and not ind['scientific_closed_loop_claimed'] and not ind['final_release_authorized']
 assert ind['root_review']==ref(NR) and ind['selected_server_review']==ref(B+'/3042627_selected_server.json')
 for path,pin in ind['read_evidence_sha256'].items():assert h(R/path)==pin,path
 grows,gbase=manifest_rows(MAN,'3d4ffd8c102106dc977bdc8b263b4a6ef183a68e11cc0bb9df8135e84e39263a')
 selected=[]
 for a in ['A','B']:
  dr='results/formal_main_v2/libero_object/k256/seed23/training/'+a+'/deployment_receipt.json';d=read(dr);ar=ind['arms'][a]
  assert ar['completed_updates']==5000 and ar['sample_uses']==ar['unique_windows']==ar['cursor']==40000
  assert d['checkpoint_sha256']==ar['best_sha256'] and d['metadata']['update']==ar['earliest_selected_update']==5000 and d['metadata']['validation_metric']==ar['selected_teacher_l1']
  selected.append(dict(arm=a,path='/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_object/k256/seed23/'+a+'/best.pt',expected_sha256=d['checkpoint_sha256'],selected_update=5000,validation_metric=ar['selected_teacher_l1'],metadata_source=ref(dr)))
 lrows,lbase=manifest_rows(LD+'/manifest.json','ac7ce07dc8e5781ed1f0996f0af3151613eeb69df46b30c949ffeb3ee0eac67b')
 linds={};lroots={}
 for job,pins,successes,cost in [('3046779',('968b0e8b09577ce93320a02c1c69f5b37f6bc0256004962aaaa8a62e55789919','8beeb55a298179d25221ff01f0249c569a2fd9abd58659ef7272c8f2265bce4a'),{'A256_seed17':92,'B256_seed17':95},2937),('3046798',('251788eb33c35f2cd17e613d4bb4842cb1aa6ba6eb14937578fb1675a3d139de','2386c425fa645e5a00daaa019d1a055d3e9f222612ebcd6aa8dda82998888bec'),{'A256_seed23':94,'B256_seed23':96},3159)]:
  lr='results/formal_main_v2/downstream_reviews/'+job+'.json';li=LD+'/job'+job+'/independent_review.json'
  lroot=checked(lr,pins[0]);lind=checked(li,pins[1]);lroots[job]=lroot;linds[job]=lind
  assert lroot['status']==lind['status']=='passed' and lroot['scientific_complete'] and lind['scientific_complete'] and lind['blockers']==[]
  assert lroot['completed_trials']==lind['completed_trials']==200 and lind['unique_initial_states']==100 and lind['successes']==successes
  assert lind['cost']['all_attempt_GPU_seconds']==lroot['cost']['all_attempt_gpu_seconds']==cost and lind['root_review']==ref(lr)
  assert not lind['final_state_values_read'] and not lind['final_release'] and not lind['O2A_latency_verified'] and not lind['synthetic_evidence_used_for_scientific_acceptance'] and not lind['legacy_terminal_trials_reused']
  for path,pin in lind['evidence_sha256'].items():assert h(R/path)==pin,path
  cross=checked(lind['cross_seed_panel_identity']['path'],lind['cross_seed_panel_identity']['sha256'])
  assert len([x for x in f['Long_remaining16_development_submissions'] if x['job_id']==job and x['completed_trials_accepted']==0])==1
 combined=checked(LD+'/summary.json','803aa7d9080a51cf5fe739dfa661c63687d62cfea93d6f7ca1f6633d3830ed3a')
 assert combined['status']=='passed' and combined['completed_trials']==400 and combined['unique_initial_states']==100
 shared=checked(combined['shared_development_panel_check']['path'],combined['shared_development_panel_check']['sha256'])
 assert shared['status']=='passed' and shared['current_trials']==shared['prior_trials']==400 and shared['unique_initial_states_across_all_four_jobs']==100
 assert shared['not_independent_across_budget_or_seed'] and not shared['old1212_action_trials_merged']
 assert {r['root_review']['path'] for r in shared['prior_matched_runtime_jobs']}=={'results/formal_main_v2/downstream_reviews/3043709.json','results/formal_main_v2/downstream_reviews/3045322.json'}
 sind=checked(SD+'/independent_review.json','7991a85e8c0023626a00dc1dd422d48a2e1a099cf36d260e918871b620905f2c')
 assert sind['status']=='passed' and sind['blockers']==[] and sind['planned_trials']==600 and sind['new_trials_completed_by_this_review']==0
 assert sind['capacity_sequence']==[{'before':5,'after':6},{'before':6,'after':7},{'before':7,'after':8}]
 assert {j['job_id'] for j in sind['jobs']}=={'3047152','3047156','3047163'}
 srows,sbase=manifest_rows(SD+'/manifest.json','ad82e5291f1b223d90515c5b53bf4631e7b098900e8abde89e326408d816625b')
 submissions=[]
 invpins={'3047152':'2551eb5fb98e4e060316ff4c2bdfe4065f31431f3f6800edad23276c9a5ef80b','3047156':'97957ae4fdbc161fb863f94521026867c1496857d29c0b593fd31bcd88c2a280','3047163':'657469914d10e9462ec3cbc789167eea2ac5434582456a9a24ffe2364d40ca5d'}
 for row in sind['jobs']:
  jobid=row['job_id'];seed=row['seed'];budget=row['budget'];auth=row['authorization'];assert ref(auth['path'])==auth
  rec=checked(row['root_reconciliation']['path'],row['root_reconciliation']['sha256'])
  assert rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0 and rec['job']['job_id']==jobid
  ad='results/formal_main_v2/downstream_gateway/'+auth['sha256']
  assert read(ad+'/committed.json')['root_reconciliation']==row['root_reconciliation']
  js=[j for j in s['registered_jobs'] if str(j['job_id'])==jobid];assert len(js)==1
  assert js[0]['method_ids']==[f'A{budget}_seed{seed}',f'B{budget}_seed{seed}'] and js[0]['invocation_sha256']==invpins[jobid]
  assert ctl['downstream_reservations_consumed'][auth['sha256']]['job_id']==jobid
  submissions.append(dict(job_id=jobid,suite='libero_10',visual_tokens=budget,seed=seed,method_ids=js[0]['method_ids'],planned_trials=200,unique_development_initial_states=100,completed_trials_accepted=0,status='submitted_once_original_ACK_and_full_identity_reconciled',authorization=auth,reconciliation=row['root_reconciliation'],independent_submission_review=dict(path=E+'/Long_submissions_independent/independent_review.json',sha256=h(R/SD/'independent_review.json')),failure_retained=ref(ad+'/failed_transaction.json'),original_failure_type=row['original_failure_type'],exact_reservation_consumed=True,automatic_retry=False,final_evaluation_enabled=False))
 assert not any(x['job_id'] in invpins for x in f['Long_remaining16_development_submissions'])
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8 and obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 for jobid,secs in [('3042627',52321),('3046779',2937),('3046798',3159)]:assert obs['rows'][jobid]['status']=='COMPLETED' and obs['rows'][jobid]['elapsed_seconds']==secs
 for jobid in invpins:assert obs['rows'][jobid]['status'] in ['RUNNING','PENDING','CONFIGURING'] and jobid in cap['occupied']
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost']['allocated_gpu_seconds']
 inventory=checked('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin
 assert not (R/NI).exists() and not (R/B/'summary.json').exists()
 gcopies=archive(grows,gbase,'Object256seed23_independent');lcopies=archive(lrows,lbase,'Long256_terminal_independent');scopies=archive(srows,sbase,'Long_submissions_independent')
 for dest,source in [(NI,IND)]+[('results/formal_main_v2/downstream_reviews/'+j+'_independent.json',LD+'/job'+j+'/independent_review.json') for j in linds]:
  with (R/dest).open('xb') as stream:stream.write((R/source).read_bytes())
 delivery=save(B+'/Object3042627_independent_delivery.json',dict(copies=gcopies,canonical=ref(NI),source_manifest=ref(MAN),no_GPU_execution=True))
 ldelivery=save(B+'/Long256_independent_delivery.json',dict(copies=lcopies,source_manifest=ref(LD+'/manifest.json'),no_GPU_execution=True))
 sdelivery=save(B+'/Long_submissions_independent_delivery.json',dict(copies=scopies,report=ref(E+'/Long_submissions_independent/independent_review.json'),source_manifest=ref(SD+'/manifest.json'),no_GPU_execution=True))
 binding=save(B+'/3042627_selected_binding.json',dict(status='root_and_independent_selected_identity_verified',root_review=ref(NR),independent_review=ref(NI),actual_server_bytes=ref(B+'/3042627_selected_server.json'),selected_checkpoints=selected,weights_copied=False))
 f['completed_training_pairs']['libero_object_k256_seed23']=dict(job_id='3042627',suite='libero_object',visual_tokens=256,seed=23,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),selected_checkpoints=selected,selected_server_review=binding['path'],selected_server_review_sha256=binding['sha256'],verification_kind='root_startup_consumer_and_independent_raw_reconstruction',trained_arms=2,completed_by_arm={'A':5000,'B':5000},allowed_next_segment_end=None,machine_original_outcome=None,historical_failure_retained=ind['historical_failure_review'],historical_original500_dual_review=ind['historical_dual_review_receipts'])
 f['trained_arms']=2*len(f['completed_training_pairs']);assert f['trained_arms']==62
 f['root_and_independent_completed_arms']=62;f['root_and_independent_reviewed_arm_updates']+=9000
 f['completed_engineering_segments'].append(dict(job_id='3042627',suite='libero_object',visual_tokens=256,seed=23,status='passed_root_and_independent_complete_training',updates_by_arm={'A':5000,'B':5000},allocated_gpu_seconds=52321,pair_total_gpu_seconds=58917,root_review=NR,root_review_sha256=h(R/NR),independent_review=NI,independent_review_sha256=h(R/NI),new_reviewed_arm_updates=9000,prior_root_independent_updates_per_arm=500))
 newdevs=[]
 verified=f['new_action_development_verified_by_job'];assert set(verified)=={'3043709','3045322'}
 for job,seed in [('3046779',17),('3046798',23)]:
  lind=linds[job];lr='results/formal_main_v2/downstream_reviews/'+job+'.json';li=lr.replace('.json','_independent.json');delta=round(lind['B_minus_A_success_rate']*100,8)
  newdev=dict(job_id=job,suite='libero_10',visual_tokens=256,seed=seed,completed_trials=200,unique_initial_states=100,root_review=ref(lr),independent_review=ref(li),successes=lind['successes'],B_minus_A_percentage_points=delta,paired_outcomes=lind['paired_outcomes'],per_task=lind['per_task'],initial_observation_token_overlap_mean=lind['initial_observation_token_overlap_mean'],token_overlap_scope=lind['token_overlap_scope'],action_semantics_sha256=lind['action_semantics_sha256'],GPU_seconds=lind['cost']['all_attempt_GPU_seconds'],O2A_complete=False,whole_suite_development_complete=False,no_legacy_semantics_equivalence_claimed=True)
  verified[job]=newdev;newdevs.append(newdev)
  prior=[x for x in f['Long_remaining16_development_submissions'] if x['job_id']==job][0]
  prior.update(status='passed_root_and_independent_terminal',completed_trials_accepted=200,root_terminal_review=ref(lr),independent_terminal_review=ref(li),terminal_GPU_seconds=newdev['GPU_seconds'],successes=lind['successes'],B_minus_A_percentage_points=delta)
 f['latest_new_action_development_verified']=newdevs[-1]
 f['completed_development_trials']=2012;f['current_action_development_trial_count']=800;f['current_action_development_unique_initial_states']=100;f['historical_other_action_semantics_development_trials']=1212
 f['Long_remaining16_development_submissions'].extend(submissions)
 keys=[]
 for k,v in f['completed_training_pairs'].items():
  if v.get('root_review') and v.get('independent_review'):
   for role in ['root_review','independent_review']:assert h(R/v[role])==v[role+'_sha256']
   keys.append(k)
  elif v.get('terminal_root_and_independent_review'):
   x=v['terminal_root_and_independent_review'];assert x['completed_by_arm']=={'A':5000,'B':5000}
   for role in ['root_review','independent_review']:assert ref(x[role]['path'])==x[role]
   keys.append(k)
 assert len(keys)==31
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':16,'libero_goal':12}
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 next_actions=['Leave healthy auto5000 training to the controller; next scheduled heartbeat handles terminals and exceptions, no continuous in-turn polling.',
 'Long256 seed41 and Long64 seed17/23 development3047152/3047156/3047163 registered once,600 planned; review genuine terminal artifacts at next supervision, never rerun accepted development.',
 'Continue only registered remaining development and exact selected-checkpoint latency work after actual free slots; all historical failures and replay costs retained.',
 'All72 checkpoints+16reference identities+4suite complete development and root globalrelease required before final35200; no final-state reading, result-based reselection or automatic scope expansion.']
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='scheduled_supervision_training_and_two_development_pairs_accepted_three_slots_refilled',utc=now,root_independent_complete=62,total_arms=72,completed_by_suite=suites,new_completed_training_groups=2,root_independent_updates=314000,new_reviewed_arm_updates=9000,Object256seed23_root=ref(NR),Object256seed23_independent=ref(NI),selected_identity=binding,independent_delivery=delivery,automatic_machine_original_outcome_for_new_pair=None,original_failure_and_original500_dual_review_retained=True,training_sample_uses_per_arm=40000,unique_training_windows_per_arm=40000,validation_nodes_per_arm=11,validation_windows_per_node=204,terminal_training_segment_GPU_seconds=52321,all_training_pair_GPU_seconds=58917,new_development_trials_accepted=400,all_historical_and_new_development_trials=2012,current_action_development_trials=800,current_action_unique_initial_states=100,historical_other_action_trials_not_pooled=1212,Long256_development=newdevs,Long_terminal_independent_delivery=ldelivery,new_GPU_submissions_by_root=list(invpins),Long_development_submissions=submissions,Long_submissions_independent_delivery=sdelivery,original_ACK_reconciled_no_resubmit=True,third_original_name_failure_row_unavailable=True,new_duplicate_submissions=0,scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_GPU_slots=0,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,completed_final_trials=0,expected_final_trials=35200,final_sealed=True,normal_training_left_to_controller=True,server_only=True,scientific_files_unchanged=173,nonweight_archive=ind['archive_reconstruction']['snapshot'],new_archived_raw_bytes=213072852,independent_review_limitations=ind['limitations'],next=next_actions))
 f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary)
 f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied']);f['parallel_execution']['actual_running_allocated_GPUs']=sum(obs['rows'][x]['gpus'] for x in cap['occupied'] if obs['rows'][x]['status']=='RUNNING')
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']=f'62/72 root+independent complete (Long18,Spatial16,Object16,Goal12),314000 reviewed arm updates. Object256seed23 restored original500 then completed5000; prior CUDA84sec retained,totalpair58917sec,no fabricated machine completion. Long256seed17/23 development400 trials accepted A92/B95 and A94/B96 over same100 initial states; no latency or three-seed claim. Current runtime800 trials and old1212 trials separate. New development3047152/3047156/3047163 planned600,accepted0. {len(cap["occupied"])} active GPUs,final0/35200sealed.'
 s['next_actions']=next_actions;s['next_allowed_action']=next_actions[0]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 text=f'{stamp}：正式训练 **62/72组通过root与独立复核**（Long18、Spatial16、Object16、Goal12）。新增Object256 seed23 A/B各5000步；保留原500步双审，本次新增9000已审臂更新，累计314000。独立重建每臂40000次使用且40000个唯一窗口、相同初始化和数据顺序、11×204验证。A/B均选5000步，teacher L1为0.00862454/0.00880729。原CUDA失败84秒、原500步6512秒及终段52321秒全部保留，pair累计58917 GPU秒。原失败阻断历史不清除，未伪造控制器完成收据。optimizer/RNG基于真实恢复链、冻结源码和断点哈希验证，本轮未独立反序列化张量。\n\n'
 text+='Long256开发 **seed17：A92/100、B95/100，配对+3个百分点；seed23：A94/100、B96/100，配对+2个百分点**。两作业各200条经原consumer与独审通过，分配2937+3159=6096 GPU秒。全部复用同100开发初态，连同已验收Long128 seed23/41共800条当前动作语义试验，仍仅100唯一初态；旧1212条不同动作语义结果分列。保留此前128预算的负结果，尚无三seed或完整延迟结论，不据此宣称总体改善或统计等效。\n\n'
 text+=f'释放的三卡已单次提交Long256 seed41、Long64 seed17/23开发3047152/3047156/3047163，共600条待验收；前两次提交后记账缺行、第三次名称核验失败均保留，通过原ACK/token与完整身份核验后登记，没有重发。第三次原异常行未留存，原因无法确认，不改写为单纯记账延迟。当前{len(cap["occupied"])}卡活动（5训练、3开发），正式轮累计 **{seconds/3600:.3f} GPU小时**（含失败、加载、运行中分配，非最终）。非权重结果均在服务器，173科学文件不变；归档总开发2012条，最终0/35200封存。正常运行交控制器及后续定时监督。[证据](../{B}/summary.json)。\n\n'
 short=f'{stamp}：62/72训练组双审通过；Object256 seed23 A/B完成5000步，原失败与恢复成本保留。本次Long256 seed17/23新增400条开发双审通过，A/B分别92/95与94/96，配对+3/+2个百分点。当前语义800条共享100初态，旧1212条另列；完整延迟及三seed结论未完成。新开发3047152/3047156/3047163各200条待验收，共{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时（非最终）。最终0/35200继续封存，173科学文件不变。[证据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式Long其余16选择器开发登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];first,tail=p.read_text().split('\n',1);oldsha=h(p);p.write_text(first+'\n\n'+(text if name=='实验进度' else short)+tail.lstrip('\n'));docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 report='# 正式Long256种子17与23开发结果\n\n'+stamp+'，formal_main_v2；仅开发结果，最终主表尚未开放。\n\n'
 report+='固定Long官方基座、每视角128 tokens、5000更新、有效batch8、h8、λ0.1，按任务等权硬teacher L1选checkpoint。两个seed独立初始化，各自A/B共享初始化及数据顺序。10任务×10共同开发初态，等待10步、chunk8、最多520控制步；一次硬Top-k、共同packing和一次VLA前向，未来头与后续执行动作不进入部署。\n\n'
 report+='| 任务ID | seed17 A/10 | seed17 B/10 | B−A百分点 | seed23 A/10 | seed23 B/10 | B−A百分点 |\n|---|---:|---:|---:|---:|---:|---:|\n'
 for t in range(10):
  vals=[]
  for j,seed in [('3046779',17),('3046798',23)]:
   a=linds[j]['per_task'][f'A256_seed{seed}'][str(t)]['successes'];b=linds[j]['per_task'][f'B256_seed{seed}'][str(t)]['successes'];vals.extend([str(a),str(b),f'{(b-a)*10:+d}'])
  report+='| '+str(t)+' | '+' | '.join(vals)+' |\n'
 report+='| 全部100初态 | 92/100 | 95/100 | +3 | 94/100 | 96/100 | +2 |\n\n'
 for j,seed in [('3046779',17),('3046798',23)]:
  v=linds[j];o=v['paired_outcomes'];ac=v['action_checks']
  report+=f'seed{seed}：共同成功{o["(1, 1)"]}、仅A成功{o["(1, 0)"]}、仅B成功{o["(0, 1)"]}、均失败{o["(0, 0)"]}；共同初始观测token集合重合率{v["initial_observation_token_overlap_mean"]:.9f}。核对{ac["raw_policy_calls"]}个8×7动作chunk及{ac["executed_control_steps"]}控制步，实际动作逐步等于chunk前缀，未来头调用0。全部Slurm分配{v["cost"]["all_attempt_GPU_seconds"]} GPU秒，包含加载和设置。\n\n'
 report+='两作业累计400条trial、6096 GPU秒（1.693333 GPU小时）。与已验收Long128 seed23/41同100个开发初态，当前语义总800条仍为100个唯一初态簇；不能把跨seed/预算重复计为独立样本。旧1212条不同动作语义结果保留并另列。此前128预算两seed的A95/B92负差异不删除，也不据此次256预算正差异挑选seed或预算。\n\n'
 report+='本轮两个seed的B均高于A，但第三seed、全套件开发、完整O2A/组件计时及最终统计未齐，不能据此宣称成功率—延迟折中已改善，不能以未显著解释等效。动作误差完整汇总待同checkpoint诊断面板；未来预测误差只作诊断。封存最终初态未读取，不改变方法、选模、任务或预算。\n\n'
 for j in linds:
  report+=f'[{j} root收据](../results/formal_main_v2/downstream_reviews/{j}.json)，[独审](../results/formal_main_v2/downstream_reviews/{j}_independent.json)。\n\n'
 report+=f'[完整本轮记录](../{B}/summary.json)。全部权重留服务器；原始trial、执行日志、成本和审计代码归档供复核。\n'
 p=R/'docs/正式Long256种子17与23开发结果.md';assert not p.exists();p.write_text(report);docs.append(dict(path=p.relative_to(R).as_posix(),after_sha256=h(p)))
 op=R/B/'root_operations';op.mkdir(exist_ok=True)
 names=['observe_formal_0626.py','pull_terminal_0626.py','review_object_terminal_0626.py','archive_results_0626.py','review_long_3046779_0626.py','review_long_3046798_0626.py','integrate_0626.py']
 names+=['reserve_Long256seed41_0626.py','dispatch_long256seed41_0626.py','reconcile_long256s41_pending_0626.py','reserve_Long64seed17_0626.py','dispatch_long64seed17_0626.py','reconcile_long64s17_pending_0626.py','reserve_Long64seed23_0626.py','dispatch_long64seed23_0626.py','diagnose_long64s23_pending_0626.py','reconcile_long64s23_pending_0626.py']
 for name in names:
  raw=(R/'.local'/name).read_bytes();compile(raw,name,'exec')
  with (op/name).open('xb') as stream:stream.write(raw)
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_0530_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(status='integrated',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,new_GPU_jobs=list(invpins),frozen_scientific_files=173,normal_gpu_realtime_polling=False))
 print(json.dumps(dict(status='integrated',root_completed=62,reviewed_updates=314000,new_development=400,active_GPU_jobs=len(cap['occupied']),GPU_hours=seconds/3600,summary=summary)),flush=True)
