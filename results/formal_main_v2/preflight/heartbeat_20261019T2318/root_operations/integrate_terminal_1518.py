from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T2318'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((R/n).read_text())
def ref(n):return dict(path=n,sha256=h(R/n))
def record(n,v):
 with (R/n).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(n)
p=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(p)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('integrate1518',p);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';oldsha=h(statepath);old=read('results/experiment_supervisor/state.json');s=copy.deepcopy(old);assert s['pending_submission'] is None;p=s['formal_main_progress'];pairs=p['completed_training_pairs']
 nr='results/formal_main_v2/libero_object/k128/seed41/training/segment_reviews/3036313.json';ni='results/formal_main_v2/libero_object/k128/seed41/training/segment_reviews/3036313_independent.json'
 rt=read(B+'/3036313_root_terminal.json');assert rt['root_review']==ref(nr);assert h(R/ni)=='046b6e9b7001ad314920563d42b25ed565dab39496407d8514ee566c17272338'
 root=read(nr);ind=read(ni);assert root['status']=='passed' and ind['status']=='passed_complete_training_only';assert root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000};assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==55274
 selected=read(B+'/3036313_selected_server.json');selection=[]
 for row in selected['checks']:
  arm=row['arm'];dep=f'results/formal_main_v2/libero_object/k128/seed41/training/{arm}/deployment_receipt.json';dv=read(dep)
  v=min(dv['evaluations'],key=lambda x:(x['validation_metric'],x['update']))
  assert dv['training_complete'] and dv['completed_updates']==5000 and len(dv['evaluations'])==11
  assert dv['checkpoint_sha256']==row['sha256']==ind['arms'][arm]['best_sha256']
  assert dv['metadata']['update']==v['update']==ind['arms'][arm]['earliest_selected_update'] and dv['metadata']['validation_metric']==v['validation_metric']==ind['arms'][arm]['selected_teacher_l1']
  selection.append(dict(arm=arm,path=row['path'],expected_sha256=row['sha256'],selected_update=v['update'],validation_metric=v['validation_metric'],metadata_source=ref(dep)))
 sr=record(B+'/3036313_selected_binding.json',dict(status='actual_server_hashes_and_raw_validation_selection_agree',root_review=ref(nr),independent_review=ref(ni),actual_server_probe=ref(B+'/3036313_selected_server.json'),selected_checkpoints=selection,candidate_and_finalized_hashes_not_assumed_equal=True,weights_copied=False))
 entry=pairs['libero_object_k128_seed41'];assert not entry.get('root_review') and 'machine_verification' in entry
 entry.update(job_id='3036313',suite='libero_object',visual_tokens=128,seed=41,trained_arms=2,verification_kind='machine_automatic_plus_root_and_independent_raw_reconstruction',root_review=nr,root_review_sha256=h(R/nr),independent_review=ni,independent_review_sha256=h(R/ni),selected_server_review=sr['path'],selected_server_review_sha256=sr['sha256'],selected_checkpoints=selection,allowed_next_segment_end=None)
 prior=[x for x in p['completed_engineering_segments'] if x.get('suite')=='libero_object' and x.get('visual_tokens')==128 and x.get('seed')==41 and x.get('root_review') and x.get('independent_review')]
 assert {str(x['job_id']) for x in prior}=={'3025875','3030276'}
 previous_by_arm={arm:max(x['updates_by_arm'][arm] for x in prior) for arm in ['A','B']};assert previous_by_arm=={'A':1000,'B':1000}
 for x in prior:
  a=read(x['root_review']);b=read(x['independent_review']);assert a['completed_by_arm']==b['completed_by_arm']==x['updates_by_arm']
 increment=sum(5000-previous_by_arm[a] for a in ['A','B']);assert increment==8000 and p['root_and_independent_reviewed_arm_updates']==231000
 p['root_and_independent_reviewed_arm_updates']+=increment
 keys=[]
 for key,v in pairs.items():
  if v.get('root_review') and v.get('independent_review'):
   for role in ['root_review','independent_review']:assert h(R/v[role])==v[role+'_sha256']
   keys.append(key)
  elif v.get('terminal_root_and_independent_review'):
   x=v['terminal_root_and_independent_review'];assert x['completed_by_arm']=={'A':5000,'B':5000}
   for role in ['root_review','independent_review']:assert ref(x[role]['path'])==x[role]
   keys.append(key)
 assert len(keys)==23;p['root_and_independent_completed_arms']=46
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']};assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':10,'libero_goal':2}
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538');assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 spatial=read(B+'/Spatial_dependency_repair.json');assert spatial['status']=='exact_original_bytes_published_actual_P_CPU_verify_passed' and not spatial['new_GPU_submissions']
 failed=next(j for j in s['registered_jobs'] if str(j['job_id'])=='3042529');assert failed['status']=='FAILED' and failed['elapsed_seconds']==2
 p['first_spatial_development'].update(status='12_preserved_new_attempt3042529_startup_FAILED_dependency_repaired_new_authorization_required',failed_continuation_job_id='3042529',failed_continuation_GPU_seconds=2,exact_pending_reconciliation=ref(B+'/Spatial_pending_reconciliation.json'),dependency_repair=ref(B+'/Spatial_dependency_repair.json'),new_trials_added=0,next='Prepare a new explicitly audited single development continuation plan preserving both prior allocations and12 terminal trials; use unmodified actual P CPU preflight before any next GPU submission. Do not reuse consumed authorization.',automatic_retry=False)
 p['downstream_asset_consumer_integration']['new_actual_GPU_runtime_chain_verified']=False
 cuda=[j for j in s['registered_jobs'] if j.get('continuous_admission',{}).get('recovery_job_id')=='3039258' or j.get('invocation')=='results/formal_main_v2/invocations/libero_object_train_k256_seed23_attempt03.json']
 assert len(cuda)<=1
 cudasummary=dict(submitted=bool(cuda),job_id=cuda[0]['job_id'] if cuda else None,status=obs['rows'][cuda[0]['job_id']]['status'] if cuda else 'not_submitted',target_updates=5000,prior500_recovery_retained=True,controller_block_retained=True)
 if cuda:p['CUDA_startup_issue']['continuous_after3039258']=dict(**cudasummary,authorization=ref('configs/experiments/formal_main_v2_cuda_continuous_3039258_v1.json'))
 archive='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_1518_union26.json';ar=read(archive);assert len(ar['files'])==26
 now=datetime.now(timezone.utc).isoformat();summary=dict(schema='formal_main_v2',kind='root_heartbeat_supervision_summary',utc=now,status='new_terminal_pair_verified_startup_failure_reconciled_dependency_repaired',root_and_independent_completed_arms=46,total_arms=72,completed_by_suite=suites,root_and_independent_reviewed_arm_updates=p['root_and_independent_reviewed_arm_updates'],new_reviewed_arm_updates=increment,previous_root_reviewed_by_arm=previous_by_arm,intermediate1500_review_was_machine_only=True,new_completed_pair=dict(pair='libero_object_k128_seed41',root=ref(nr),independent=ref(ni),selected_binding=sr),occupied_GPU_jobs=len(cap['occupied']),active_job_ids=cap['occupied'],reserved_GPU_slots=s['autonomous_training_v1']['reserved_GPU_slots'],allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,GPU_cost_final=False,scheduler_observation=obs,pending_submission=None,spatial_failed_job='3042529',spatial_failed_GPU_seconds=2,spatial_new_trials=0,spatial_dependency_repair=ref(B+'/Spatial_dependency_repair.json'),cuda_continuous=cudasummary,completed_development_trials_unchanged=p['completed_development_trials'],completed_final_trials=0,expected_final_trials=35200,final_sealed=True,nonweight_archive=ref(archive),raw_files=26,raw_bytes=sum(v['bytes'] for v in ar['files']),scientific_settings_changed=False,all173_frozen_unchanged=True,server_only=True,next=['Normal controller continues auto5000 and fills approved free slots; no in-turn polling','Prepare newly authorized bounded Spatial development continuation after missing immutable dependency repair; retain failed3042529 cost and12 prior trials','Continue registered terminal reviews, remaining exception recoveries and frozen final/latency gates'])
 sr2=record(B+'/summary.json',summary);p['latest_completed_pairs_independent_delivery']=sr2;p['latest_incremental_review']=sr2;p['incremental_review_history'].append(sr2);p['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 p['nonweight_archive_preparation_20261019_1518']=dict(snapshot=ref(archive),files=26,raw_bytes=summary['raw_bytes'],server_originals_retained=True,index_guard_pending=True)
 s['last_root_supervision_snapshot']=sr2;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-19';s['current_work']='46/72 root+independently verified; Spatial3042529 failed before child, exact missing dependency now published and CPU preflight passed; normal controller continues5000.';s['next_actions']=summary['next']
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 assert p['completed_final_trials']==0 and not p['test_opened'] and not p['global_release_created']
 c.atomic_json(statepath,s,oldsha)
 base=f'2026-10-19本轮监督：完整训练 **46/72组**（Long18、Spatial16、Object10、Goal2），新增Object128 seed41 A/B各5000通过root和独立原始证据复核。A选update4000、B选3500，完整11次验证、40000次窗口使用、best/resume身份一致；此离线选模不代表闭环收益。累计已审239000次臂更新（新增8000；原1500机器核验不冒充此前独审）。\n\n实际Slurm快照累计 **{seconds/3600:.3f} GPU小时**，{len(cap["occupied"])}个GPU作业活动，含失败及运行中分配，非最终成本。Spatial3042529启动2秒失败，唯一缺项为旧审核收据3022743；已按原SHA补入运行目录，未经改写的完整P侧CPU预检通过。未启动模型、未新增trial，原12条前缀保持。失败登记已按原token、真实终态scontrol存档及当前sacct寿命对账，pending清除、旧预约仅消费一次；旧授权不可再用，新续跑需新精确计划。\n\n'
 if cuda:base+=f'Object256 seed23已从双审500步断点单次提交连续至5000，作业{cuda[0]["job_id"]}，原失败和6596 GPU秒历史保留；正常控制器blocked记录不清除。\n\n'
 else:base+='Object256 seed23连续5000一次入口已审，本轮未新增该续跑作业；按实际空闲槽推进。\n\n'
 base+='正常训练交自动控制器，后续定时监督处理终态与异常。原1212开发记录与全部失败保留，最终0/35200继续封存；本轮无新成功率或完整O2A结论。26份终态非权重raw已无损归档，权重只留服务器。'+f'[本轮收据](../{B}/summary.json)。\n\n'
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式动作执行入口接入记录']:
  path=R/('docs/'+name+'.md');text=path.read_text();head,rest=text.split('\n',1);path.write_text(head+'\n\n'+base+rest.lstrip('\n'))
 print(json.dumps(dict(status='root_independent_46_complete',summary=sr2,root_updates=239000,occupied=len(cap['occupied']),GPU_hours=seconds/3600,cuda_continuous=cudasummary)))
