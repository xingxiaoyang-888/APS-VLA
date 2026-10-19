from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,hashlib,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T0332'
D='results/formal_main_v2/execution/long_remaining16_action_v1_1827/k128_seed23'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_text())
def save(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(rel)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('integrate1932ctl',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress'];ctl=s['autonomous_training_v1']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==46 and f['root_and_independent_reviewed_arm_updates']==239000
 assert ctl['reserved_GPU_slots']==1 and ctl['reservation_root_record']==ref(D+'/reservation_root_record.json')
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 nr='results/formal_main_v2/libero_object/k64/seed17/training/segment_reviews/3037054.json'
 ni='results/formal_main_v2/libero_object/k64/seed17/training/segment_reviews/3037054_independent.json'
 assert h(R/nr)=='b7e528439916fd881668ca2d2960735a8aa751b05e198fff6e15cccb68ec1756'
 assert h(R/ni)=='f14b26c65a7a337dd629d2ae87ca10d94e9ad31d96dffcfb0e6cbf39188fefd7'
 root=read(nr);ind=read(ni)
 assert root['status']=='passed' and ind['status']=='passed_complete_training_only'
 assert root['completed_by_arm']==ind['completed_by_arm']=={'A':5000,'B':5000}
 assert root['pair_allocated_gpu_seconds']==ind['cost']['all_pair_allocated_GPU_seconds']==61932
 actual=read(B+'/3037054_selected_server.json');selection=[]
 for row in actual['checks']:
  arm=row['arm'];dep=f'results/formal_main_v2/libero_object/k64/seed17/training/{arm}/deployment_receipt.json';dv=read(dep)
  best=min(dv['evaluations'],key=lambda x:(x['validation_metric'],x['update']))
  assert dv['training_complete'] and dv['completed_updates']==5000 and [e['update'] for e in dv['evaluations']]==list(range(0,5001,500))
  assert dv['checkpoint_sha256']==row['sha256']==ind['arms'][arm]['best_sha256']
  assert dv['metadata']['update']==best['update']==ind['arms'][arm]['earliest_selected_update']
  assert dv['metadata']['validation_metric']==best['validation_metric']==ind['arms'][arm]['selected_teacher_l1']
  selection.append(dict(arm=arm,path=row['path'],expected_sha256=row['sha256'],selected_update=best['update'],validation_metric=best['validation_metric'],metadata_source=ref(dep)))
 sr=save(B+'/3037054_selected_binding.json',dict(status='actual_server_hashes_and_raw_validation_selection_agree',root_review=ref(nr),independent_review=ref(ni),actual_server_probe=ref(B+'/3037054_selected_server.json'),selected_checkpoints=selection,weights_copied=False))
 entry=f['completed_training_pairs']['libero_object_k64_seed17'];assert not entry.get('root_review') and 'machine_verification' in entry
 entry.update(job_id='3037054',suite='libero_object',visual_tokens=64,seed=17,trained_arms=2,verification_kind='machine_automatic_plus_root_and_independent_raw_reconstruction',root_review=nr,root_review_sha256=h(R/nr),independent_review=ni,independent_review_sha256=h(R/ni),selected_server_review=sr['path'],selected_server_review_sha256=sr['sha256'],selected_checkpoints=selection,allowed_next_segment_end=None)
 prior=[x for x in f['completed_engineering_segments'] if x.get('suite')=='libero_object' and x.get('visual_tokens')==64 and x.get('seed')==17 and x.get('root_review') and x.get('independent_review')]
 assert {str(x['job_id']) for x in prior}=={'3026219','3030833'}
 previous={a:max(x['updates_by_arm'][a] for x in prior) for a in ['A','B']};assert previous=={'A':1000,'B':1000}
 for x in prior:
  a=read(x['root_review']);b=read(x['independent_review'])
  assert b['status']=='passed' and b['root_review_path']==x['root_review'] and b['root_review_sha256']==h(R/x['root_review'])
  assert a['completed_by_arm']=={arm:b['arms'][arm]['completed_updates'] for arm in ['A','B']}==x['updates_by_arm']
 increment=sum(5000-previous[a] for a in ['A','B']);assert increment==8000
 f['root_and_independent_reviewed_arm_updates']+=increment;keys=[]
 for key,v in f['completed_training_pairs'].items():
  if v.get('root_review') and v.get('independent_review'):
   for role in ['root_review','independent_review']:assert h(R/v[role])==v[role+'_sha256']
   keys.append(key)
  elif v.get('terminal_root_and_independent_review'):
   x=v['terminal_root_and_independent_review'];assert x['completed_by_arm']=={'A':5000,'B':5000}
   for role in ['root_review','independent_review']:assert ref(x[role]['path'])==x[role]
   keys.append(key)
 assert len(keys)==24;f['root_and_independent_completed_arms']=48
 suites={suite:2*sum(k.startswith(suite+'_k') for k in keys) for suite in ['libero_10','libero_spatial','libero_object','libero_goal']}
 assert suites=={'libero_10':18,'libero_spatial':16,'libero_object':12,'libero_goal':2}
 obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
 assert not cap['findings'] and not cap['unknown'] and len(cap['occupied'])<=8
 assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
 j=next(j for j in s['registered_jobs'] if j['job_id']=='3043399');row=obs['rows']['3043399']
 assert row['status']=='RUNNING' and row['gpus']==1
 expected='cti-cuda-recovery-v1:7411a2e5e0d7e2123eea8bfea4c2bbaccb037d54b09697180340a597e3cfb18a'
 assert obs['queue']['3043399']['comment']==expected and row['scheduler_name']=='cti-formal'
 assert j['startup_recovery']['failed_job_id']=='3028522' and j['segment_end']==1500
 assert h(R/j['invocation'])==h(P/j['invocation'])==j['invocation_sha256']
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 assert seconds>=s['current_round_cost'].get('allocated_gpu_seconds',0)
 s['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 resume_observation=dict(status='running_exact_registered_identity_first_update_not_yet_observed',job_id='3043399',arm='A',actual_B_resume_observed=False,training_complete_claimed=False)
 run=P/'results/formal_main_v2/libero_spatial/k64/seed23/training'
 matches=[]
 for path in (run/'A/attempts').glob('*/cost_events.jsonl'):
  with path.open('rb') as stream:
   first=stream.readline()
  if first.endswith(b'\n') and json.loads(first).get('job_id')=='3043399':matches.append(path)
 assert len(matches)<=1
 if matches:
  path=matches[0];buf=[];rows=[]
  with path.open('rb') as stream:
   for line in stream:
    if not line.endswith(b'\n'):break
    v=json.loads(line);buf.append(line);rows.append(v)
    if v['event']=='update_end':break
    assert len(buf)<100
  assert rows[0]['event']=='attempt_start' and rows[0]['resumed'] is True and rows[0]['completed_update']==1000 and rows[0]['next_sample_cursor']==8000
  resume_observation.update(status='A_actual_resume1000_cursor8000_observed',source_journal=str(path),prefix_rows=len(rows))
  if rows[-1]['event']=='update_end':
   orderpath=run/'A/training_order.json';order=json.loads(orderpath.read_text())
   assert order['seed']==23 and len(order['samples'])==40000
   assert all(x['job_id']=='3043399' for x in rows) and rows[-1]['update']==1001 and rows[-1]['forward_backward_samples']==8 and rows[-1]['grad_norm']>0
   assert rows[1]['event']=='update_start' and rows[1]['window_ids']==order['samples'][8000:8008]
   assert (run/'B/training_order.json').read_bytes()==orderpath.read_bytes()
   resume_observation.update(status='A_actual_resume1000_cursor8000_and_update1001_match_original_order',first_update=rows[-1],AB_order_bytes_identical=True,training_order_sha256=h(orderpath))
  raw=b''.join(buf);dest=B+'/CUDA3043399_A_first_prefix.jsonl'
  with (R/dest).open('xb') as stream:stream.write(raw)
  resume_observation['source_prefix']=ref(dest);resume_observation['prefix_bytes']=len(raw)
  with path.open('rb') as stream:assert stream.read(len(raw))==raw
 logs=[]
 for suffix in ['out','err']:
  p=R/f'results/slurm/cti-formal_3043399.{suffix}'
  with p.open('rb') as stream:data=stream.read(p.stat().st_size)
  dest=B+'/CUDA3043399_startup_prefix.'+suffix
  with (R/dest).open('xb') as stream:stream.write(data)
  logs.append(dict(source=str(p),snapshot=ref(dest),bytes=len(data),live_prefix=True))
 recovery=save(B+'/CUDA3043399_running_identity_and_resume.json',dict(schema='formal_main_v2',utc=datetime.now(timezone.utc).isoformat(),job=copy.deepcopy(j),actual_scheduler=row,queue_identity=obs['queue']['3043399'],invocation_R_P_exact=True,resume=resume_observation,logs=logs,first_recovery_not_terminal=True,original_FAILED_retained=True,continuous5000_admission=False,no_continuous_polling=True))
 f['CUDA_startup_issue']['original_target_recovery_3043399']=dict(status='running_original_target1500',job_id='3043399',original_failed_job_id='3028522',authorization=ref('configs/experiments/formal_main_v2_cuda_single_recovery_3028522_v1.json'),running_evidence=recovery,original_failure_retained=True,automatic_retry=False,continuous5000_admission=False)
 f['downstream_action_range_issue']['Long16_pre_execution_qualified_scope'].update(slot_reservation_activated=True,active_reserved_shard='k128_seed23',reservation_activation=ref(B+'/Long128seed23_reservation_activation.json'),new_GPU_submissions=[])
 archive='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261020_1932_union29.json'
 ar=read(archive);assert len(ar['files'])==29
 inventory=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json');assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==pin
 now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
 summary=save(B+'/summary.json',dict(schema='formal_main_v2',kind='root_scheduled_supervision_terminal_pair_and_bounded_CUDA_recovery',utc=now,root_independent_complete=48,total_arms=72,completed_by_suite=suites,root_independent_updates=247000,new_completed_training_groups=2,new_reviewed_arm_updates=increment,previous_reviewed_by_arm=previous,new_terminal_pair=dict(pair='libero_object_k64_seed17',root_review=ref(nr),independent_review=ref(ni),selected=sr,pair_total_GPU_seconds=61932),scheduler=obs,capacity=cap,active_GPU_jobs=len(cap['occupied']),reserved_next_GPU_slots=1,reservation_activation=ref(B+'/Long128seed23_reservation_activation.json'),allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,cost_is_final=False,new_GPU_submission='3043399',CUDA_recovery=recovery,new_development_trials=0,old_development_trials_preserved=f['completed_development_trials'],completed_final_trials=0,expected_final_trials=35200,final_sealed=True,nonweight_archive=ref(archive),raw_files=29,raw_bytes=sum(x['bytes'] for x in ar['files']),normal_controller_healthy=True,no_continuous_in_turn_polling=True,server_only=True,scientific_files_unchanged=173))
 f['latest_completed_pairs_independent_delivery']=summary;f['latest_incremental_review']=summary;f['incremental_review_history'].append(summary);f['parallel_execution']['registered_requested_active_GPU_jobs']=len(cap['occupied'])
 f['nonweight_archive_preparation_20261020_1932']=dict(snapshot=ref(archive),files=29,raw_bytes=sum(x['bytes'] for x in ar['files']),server_originals_retained=True,index_guard_pending=True)
 s['last_root_supervision_snapshot']=summary;s['last_supervision_utc']=now;s['updated_utc']=now;s['updated_date']='2026-10-20'
 s['current_work']='48/72 training groups root and independently verified;Spatial64seed23 original-target recovery3043399 running to1500. Next actual free GPU slot reserved for exact admitted Long128seed23 development200. Other healthy training left to controller.'
 s['next_actions']=[
 'Normal controller continues auto5000;leave healthy jobs running,max8 GPU occupancy including exception and development jobs.',
 'At a later heartbeat inspect registered3043399 original1500 target and actual raw/optimizer/RNG/cursor;retain original3028522 failure and all costs. No automatic retry;continuous5000 needs separate exact root/independent engineering admission.',
 'Next actual free slot belongs to Long128seed23 development200 under existing exact authorization/readiness and active dedicated reservation. Root checks all registered jobs/pending/lease/identity and uses pinned formal_action_deployment_v1 gateway once;no plan regeneration or repeated stage.',
 'Continue terminal evidence reviews and original remaining CUDA recovery3028468;do not clear blocked history or consume another plan reservation.',
 'Keep original1212 development trials/all negative results. Finish all72 selected and16 references,all suite development receipts and root globalrelease before final35200;no current O2A or scientific success claim from pre-execution approval.'
 ]
 s['next_allowed_action']=s['next_actions'][2]
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']
 c.atomic_json(sp,s,before)
 detail=f'{stamp}：正式训练 **48/72组**通过root和独立原始证据复核（Long18、Spatial16、Object12、Goal2）。新增Object64 seed17 A/B各5000步，完整11次验证；A选1500步，B选2000步，原样本顺序与服务器best/resume身份一致。新增8000次已审臂更新，总247000；每臂40000次窗口使用不等于独立窗口数。此处只报告训练验收，不据离线误差判断闭环收益。\n\n'+f'**{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时**，含失败及运行中分配，非最终账单。空槽已单次提交Spatial64 seed23恢复作业3043399，从原1000步恢复至1500步，真实Slurm身份核对通过；旧失败和blocked历史保留，尚未取得终态，不能视作恢复验收完成。下一实际空槽已绑定Long128 seed23的已审200条开发计划，本轮未新增开发trial；最终0/35200封存。\n\n'+f'29份大体积终态JSONL使用无损分片归档，原件及权重保留服务器；正常训练交自动控制器和下次定时监督。[本轮收据](../{B}/summary.json)。\n\n'
 short=f'{stamp} 更新：训练48/72组双审通过，新增Object64 seed17 A/B；{len(cap["occupied"])}卡活动，累计{seconds/3600:.3f} GPU小时（非最终）。Spatial异常恢复3043399已单次启动，目标1500；下一空槽预留Long128 seed23开发200条。未新增闭环结果，最终0/35200封存。[本轮收据](../{B}/summary.json)。\n\n'
 docs=[]
 for name in ['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式CUDA启动失败恢复登记','正式Long其余16选择器开发登记']:
  rel='docs/'+name+'.md';p=R/rel;assert rel not in inventory['files'];prior=p.read_text();first,tail=prior.split('\n',1);oldsha=h(p)
  p.write_text(first+'\n\n'+(detail if name=='实验进度' else short)+tail.lstrip('\n'))
  docs.append(dict(path=rel,before_sha256=oldsha,after_sha256=h(p)))
 ops=R/B/'root_operations';ops.mkdir(exist_ok=True)
 for name in ['observe_formal_1932.py','dispatch_cuda3028522_1932.py','review_terminal_1932.py','reserve_Long128seed23_1932.py','archive_independent_1932.py','archive_pack_1932.py','integrate_1932.py']:
  p=R/'.local'/name;compile(p.read_bytes(),name,'exec')
  with (ops/name).open('xb') as stream:stream.write(p.read_bytes())
 with (R/B/'previous_Git_push_verified.json').open('xb') as stream:stream.write((R/'.local/github_push_1827_verified.json').read_bytes())
 save(B+'/root_integration.json',dict(schema='formal_main_v2',state_before_sha256=before,state_after_sha256=h(sp),summary=summary,docs=docs,controller_and_registry_unchanged_by_integration=True,fresh_Slurm_cost_accounting=True,earlier_transport_input_error='Absolute entrypoint was rejected before execution; corrected to canonical relative entrypoint with identical source SHA. No Slurm submission or scientific result was involved.',weights_local_copy=False))
 print(json.dumps(dict(status='48_training_groups_verified',summary=summary,occupied=len(cap['occupied']),GPU_hours=seconds/3600,CUDA_resume=resume_observation['status'],Long_next_reserved='k128_seed23_development200')))
