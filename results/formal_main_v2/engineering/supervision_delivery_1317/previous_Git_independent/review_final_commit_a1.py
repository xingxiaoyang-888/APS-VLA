"""Independent read-only exact Git delivery review; bind only after root's verified push."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/final_delivery_independent_1220'
B='results/formal_main_v2/preflight/heartbeat_20261020T2020/'
CORE=D/'review_commit_core.py'
CORE_SHA='31c7eb063b95c207e079ce36f84bb259f6e4e8066b9161c9c0de9665ebfe6330'
SUMMARY={'path':B+'summary_after_dispatch.json','sha256':'b6faae7369781c6a6818f49038c31832655065c2c96c42c22f17a11f77f3d865'}
JOBS=['3049132','3049172','3049191']
ACCEPTED=['3048572','3048581']
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(path,pin):return {'path':path,'sha256':pin}
def put(name,value):
 p=D/name;assert not p.exists(),str(p)
 b=(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode();p.write_bytes(b)
 return {'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)}
def local_ref(r):
 p=R/r['path'];assert p.resolve().is_relative_to(R.resolve());b=p.read_bytes();assert sha(b)==r['sha256'],r['path'];return b
assert sha(CORE.read_bytes())==CORE_SHA
ns={'__name__':'independent_commit_core'};exec(compile(CORE.read_bytes(),str(CORE),'exec'),ns)
started=time.monotonic();binding=None
try:
 assert len(sys.argv)==3,'Need private final bindings path and exact SHA after verified push'
 bp=Path(sys.argv[1]);assert bp.parent==D and bp.suffix=='.json'
 raw=bp.read_bytes();assert sha(raw)==sys.argv[2];binding=json.loads(raw)
 C=binding['commit'];BASE=binding['base_commit']
 assert binding['summary']==SUMMARY
 cr=json.loads(local_ref(binding['commit_receipt']))
 assert cr['commit']==C and cr['baseline']==BASE and cr['root_complete']==64
 t=ns['Tree'](C)
 try:
  req=json.loads(t.ref(binding['required_files_ref']));summary=json.loads(t.ref(SUMMARY))
  closed=[];deliveries=[]
  for row in req['files']:
   path=row['path']
   if path.startswith('results/formal_main_v2/control_transport/'):
    events=[json.loads(x) for x in t.ref(row).splitlines()]
    assert events[0]['event']=='control_start' and events[-1]['event']=='control_end',path
    closed.append(row)
   if path.startswith(B) and path.endswith('_delivery.json'):
    v=json.loads(t.ref(row))
    if 'copies' in v:deliveries.append(row)
  jobs=summary['new_submissions'];assert [x['job_id'] for x in jobs]==JOBS
  jobrefs=[x[k] for x in jobs for k in ['authorization','original_ACK','original_failed_transaction','root_reconciliation','independent_submission_review']]
  mandatory=[SUMMARY,binding['index_guard_ref'],binding['git_delivery_ref']]
  cfg={'commit':C,'base_commit':BASE,'verified_push_ref':binding['verified_push_ref'],
   'required_files_ref':binding['required_files_ref'],'mandatory_refs':mandatory,
   'extra_commit_paths':binding['extra_commit_paths'],'closed_transport_refs':closed,
   'archive_delivery_refs':deliveries,'job_delivery_refs':jobrefs,'new_job_ids':JOBS,
   'doc_paths':['docs/完整实验计划.md','docs/实验进度.md','docs/正式主实验规划.md','docs/正式主实验阶段结论.md','docs/正式自动连续训练执行登记.md','docs/正式非Long开发结果.md','docs/正式Long完整开发结果.md'],
   'json_assertions':[]}
  expected={'root_independent_complete':64,'total_training_arms':72,'root_independent_updates':321000,
   'new_development_trials':400,'raw_historical_and_current_development_trials':3212,
   'current_action_development_trials':2000,'current_action_unique_initial_states':300,
   'explicit_legacy_equivalent_Long_trials':600,'compatible_current_and_explicit_legacy_trials':2600,
   'legacy1212_preserved_and_not_relabelled':True,'active_GPU_jobs':8,'allocated_GPU_seconds':1900067,
   'cost_is_final':False,'new_final_trials':0,'final_completed':0,'final_expected':35200,
   'final_release':False,'pending':None,'reserved_GPU_slots':0,'source173_unchanged':True,
   'scientific_settings_changed':False,'automatic_expansion':False,'includes_all_registered_allocations':True}
  cfg['json_assertions']=[{'path':SUMMARY['path'],'keys':[k],'expected':v} for k,v in expected.items()]
 finally:t.close()
 result=ns['audit'](cfg)
 assert result['changed_paths']==cr['files']
 t=ns['Tree'](C)
 try:
  summary=json.loads(t.ref(SUMMARY));guard=json.loads(t.ref(binding['index_guard_ref']));delivery=json.loads(t.ref(binding['git_delivery_ref']))
  assert guard['status']=='verified_index_archive_delivery' and guard['head']==BASE
  assert guard['frozen_files_verified_in_worktree_and_index']==173
  assert guard['required_files']['sha256']==binding['required_files_ref']['sha256']
  assert guard['required_count']==result['required_files']
  assert guard['ordinary_staged_files_verified']==result['required_files']+1
  assert guard['archive_verification']=='verified' and guard['restore_verification']=='restored_verified'
  assert guard['real_originals_changed'] is False and guard['scientific_completion_inferred'] is False
  assert guard['codec_sha256']=='f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2'
  assert guard['checker_sha256']=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
  assert sha(t.blob('scripts/ops/nonweight_archive.py'))==guard['codec_sha256']
  assert sha(t.blob('scripts/ops/check_nonweight_archive_stage.py'))==guard['checker_sha256']
  for row in guard['archive_index_files'].values():t.ref(row)
  assert delivery['weights_added'] is False and delivery['sealed_final_values_added'] is False
  assert delivery['final_sealed'] is True and delivery['active_runs_not_terminally_collected'] is True
  archivepaths=[p for p in t.rows if p.startswith('results/formal_main_v2/nonweight_archives/v1/')]
  base_tree=ns['Tree'](BASE)
  try:
   assert {p:t.rows[p] for p in archivepaths}=={p:v for p,v in base_tree.rows.items() if p.startswith('results/formal_main_v2/nonweight_archives/v1/')}
  finally:base_tree.close()
  pull_index=json.loads(t.blob(B+'terminal_pull.json'));assert pull_index['files']==24
  assert pull_index['state_unchanged'] is True and pull_index['weights_copied'] is False
  pull=json.loads(t.ref(pull_index['pull']));assert pull['status']=='verified_nonweight_snapshot'
  assert pull['requested_job_ids']==ACCEPTED and len(pull['files'])==24
  assert not pull['weights_copied'] and not pull['sealed_initial_states_copied'] and not pull['scientific_completion_inferred']
  assert not pull['missing'] and not pull['skipped']
  pull_files=[]
  for row in pull['files']:
   r={'path':row['relative'],'sha256':row['sha256'],'bytes':row['bytes']};t.ref(r);pull_files.append(r)
  state=json.loads(t.blob('results/experiment_supervisor/state.json'));f=state['formal_main_progress']
  expected_state={'root_and_independent_completed_arms':64,'root_and_independent_reviewed_arm_updates':321000,
   'completed_development_trials':3212,'current_action_development_trial_count':2000,
   'current_action_development_unique_initial_states':300,'historical_other_action_semantics_development_trials':1212,
   'completed_final_trials':0,'expected_final_trials':35200,'test_opened':False,'global_release_created':False}
  for k,v in expected_state.items():assert f[k]==v,(k,f[k])
  assert f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600
  assert f['nonLong_development_submissions_1220']==summary['new_submissions']
  assert f['latest_capacity_refill']==SUMMARY
  current=f['new_action_development_verified_by_job'];assert sum(x['completed_trials'] for x in current.values())==2000
  states=defaultdict(set)
  for jid,entry in current.items():
   review=json.loads(t.ref(entry['root_review']));assert review['job_id']==jid and review['status']=='passed'
   assert review['completed_trials']==entry['completed_trials']
   for pair in review['reconstructed_summary']['paired_AB'].values():
    states[review['suite']].update(x['state_trial_id'] for x in pair['results'])
  unique={k:len(v) for k,v in states.items()}
  assert unique==summary['unique_current_initial_states_by_suite']==f['current_action_development_unique_initial_states_by_suite']=={'libero_10':100,'libero_spatial':100,'libero_object':100}
  assert sum(unique.values())==300 and not set(JOBS)&set(current)
  diag=json.loads(t.ref(summary['diagnostics']));assert diag['total_trials']==400 and diag['unique_initial_states']==200
  assert diag['all_job_GPU_seconds']==4551 and diag['GPU_cost_already_in_Slurm_total'] is True
  assert diag['O2A_measured'] is False and diag['bootstrap_three_seed_claimed'] is False and diag['final_results'] is False
  assert diag['jobs']==summary['accepted_jobs']
  joint=json.loads(t.ref(diag['source_independent']));assert joint['status']=='passed' and joint['synthetic'] is False
  assert joint['totals']['trials']==400 and joint['totals']['allocated_gpu_seconds']==4551
  pair_ref=diag['per_task_and_full_paired_trials'];pairs=json.loads(t.ref(pair_ref))
  assert pair_ref['sha256']==joint['paired_states']['sha256'] and len(pairs['states'])==200
  fixed={'3048572':('libero_spatial',97,96,-1,2365),'3048581':('libero_object',98,99,1,2186)}
  accepted_checks=[]
  for item in diag['jobs']:
   jid=item['job_id'];suite,aa,bb,delta,gpu=fixed[jid]
   assert item['suite']==suite and item['seed']==23 and item['visual_tokens']==128
   assert item['completed_trials']==200 and item['unique_initial_states']==100
   assert item['successes']=={'A128_seed23':aa,'B128_seed23':bb}
   assert item['B_minus_A_percentage_points']==delta and item['GPU_seconds']==gpu
   assert item['O2A_complete'] is False and item['whole_suite_development_complete'] is False
   assert item['no_legacy_semantics_equivalence_claimed'] is True
   root=json.loads(t.ref(item['root_review']));t.ref(item['independent_review'])
   assert root['status']=='passed' and root['scientific_complete'] is True and root['completed_trials']==200
   assert root['cost']['all_attempt_gpu_seconds']==gpu
   assert root['final_release'] is False and root['final_state_values_read'] is False
   rows=[json.loads(line) for line in t.ref(item['raw_ledger']).splitlines()]
   events=Counter(x['event'] for x in rows);assert events=={'invocation':1,'start':200,'result':200}
   actual=[x for x in rows if x['event']=='result'];assert len({x['trial_id'] for x in actual})==200
   assert {x['method'] for x in actual}=={'A128_seed23','B128_seed23'}
   assert all(x['split']=='development' and x['suite']==suite and x['runtime_seed']==17 and x['environment_seed']==0 and x['action_chunk']==8 and x['wait_steps']==10 for x in actual)
   groups=defaultdict(dict)
   for x in actual:
    key=x['state_trial_id'];assert x['method'] not in groups[key];groups[key][x['method']]=x
   assert len(groups)==100 and Counter(next(iter(v.values()))['task_id'] for v in groups.values())=={i:10 for i in range(10)}
   sums=Counter();discord=Counter()
   for key,v in groups.items():
    a,b=v['A128_seed23'],v['B128_seed23'];assert a['initial_state_sha256']==b['initial_state_sha256']
    sums['A']+=int(a['success']);sums['B']+=int(b['success'])
    discord['both_success' if a['success'] and b['success'] else 'A_only' if a['success'] else 'B_only' if b['success'] else 'both_failure']+=1
    p=[z for z in pairs['states'] if z['suite']==suite and z['state_trial_id']==key];assert len(p)==1
    assert p[0]['A_success']==a['success'] and p[0]['B_success']==b['success'] and p[0]['training_seed']==23
   assert sums=={'A':aa,'B':bb}
   assert {k:discord[k] for k in ['A_only','B_only','both_failure','both_success']}==item['paired_outcomes']
   assert current[jid]==item
   for arm,v in item['offline_validation_diagnostics'].items():t.ref(v['validation_ref']);assert v['validation_tasks']==10 and 'not closed-loop action error' in v['scope']
   accepted_checks.append({'job_id':jid,'suite':suite,'seed':23,'trials':200,'unique_states':100,'A_success':aa,'B_success':bb,'B_minus_A_pp':delta,'GPU_seconds_already_counted':gpu,'raw':item['raw_ledger']})
  assert sum(x['GPU_seconds_already_counted'] for x in accepted_checks)==4551
  def records(v,path='$'):
   if isinstance(v,dict):
    if str(v.get('job_id','')) in JOBS and 'invocation' in v and 'downstream_gateway' in v:yield(path,v)
    for k,x in v.items():yield from records(x,path+'.'+k)
   elif isinstance(v,list):
    for i,x in enumerate(v):yield from records(x,path+'['+str(i)+']')
  registered=list(records(state));job_delivery=[]
  for idx,item in enumerate(summary['new_submissions']):
   jid=item['job_id'];auth=json.loads(t.ref(item['authorization']))
   assert auth['maximum_attempts']==1 and auth['automatic_retry'] is False
   assert auth['final_release_authorized_by_gateway'] is False and auth['plan_arguments']['stage']=='development'
   for k in ['controller','controller_activation','planner','independent_review','plan','prepared_invocation','root_reservation','runtime_readiness','scientific_plan']:t.ref(auth[k])
   for p,h in auth['gateway_files'].items():t.ref(ref(p,h))
   ack=json.loads(t.ref(item['original_ACK']));failure=json.loads(t.ref(item['original_failed_transaction']));rec=json.loads(t.ref(item['root_reconciliation']))
   assert ack['returncode']==0 and ack['stdout'].strip()==jid
   assert failure['automatic_retry'] is False and failure['error']=='post-submit accounting incomplete'
   assert failure['status']=='stopped_requires_root_reconciliation_no_retry'
   token='cti-downstream-gateway-v1:'+item['authorization']['sha256']
   assert '--comment='+token in ack['actual_sbatch_argv'] and '--no-requeue' in ack['actual_sbatch_argv']
   assert rec['new_submissions']==0 and rec['automatic_retry'] is False and rec['status']=='exact_original_ACK_job_reconciled'
   assert rec['original_ACK']==item['original_ACK'] and rec['original_failure']==item['original_failed_transaction']
   assert rec['lifecycle_lease_held'] and rec['all173_R_and_S_match'] and rec['unrelated_controller_fields_unchanged']
   assert rec['final_release_authorized'] is False and rec['exact_reservation_consumed']==auth['root_reservation']
   job=rec['job'];assert job['job_id']==jid and job['suite']==item['suite'] and job['method_ids']==item['method_ids']
   assert job['downstream_gateway']['request_token']==token and job['downstream_gateway']['actual_sbatch_argv']==ack['actual_sbatch_argv']
   assert job['mode']=='development' and job['gpus']==1 and job['invocation_sha256']==auth['prepared_invocation']['sha256']
   assert t.ref(ref(job['invocation'],job['invocation_sha256']))==t.ref(auth['prepared_invocation'])
   t.ref(job['action_execution_contract']);t.ref(ref(job['wrapper'],job['wrapper_sha256']));t.ref(rec['original_preflight'])
   committed=json.loads(t.blob(str(Path(item['original_ACK']['path']).parent/'committed.json')))
   assert committed['job']==job and committed['request_token']==token and committed['reservation_consumed'] is True
   assert committed['automatic_retry'] is False and committed['root_reconciliation']==item['root_reconciliation']
   assert len(rec['capacity']['occupied'])<=8 and not rec['capacity']['unknown'] and not rec['capacity']['findings']
   matches=[(p,r) for p,r in registered if str(r['job_id'])==jid];assert matches
   fields=['job_id','suite','method_ids','invocation','invocation_sha256','mode','stage_key','source_sha256','wrapper_sha256']
   assert all(all(r[k]==job[k] for k in fields) for p,r in matches)
   assert item['completed_trials_accepted']==0 and item['final_evaluation_enabled'] is False and item['duplicate_submissions']==0 and item['scientific_terminal_acceptance_pending'] is True
   assert item['planned_trials']==200 and item['unique_development_initial_states']==100
   job_delivery.append({'job_id':jid,'planned_trials':200,'accepted_trials':0,'authorization':item['authorization'],'original_ACK':item['original_ACK'],'failure_retained':item['original_failed_transaction'],'reconciliation':item['root_reconciliation'],'committed_registry_matches':[p for p,r in matches]})
  assert sum(x['planned_trials'] for x in job_delivery)==600
  assert abs(summary['allocated_GPU_hours']-1900067/3600)<1e-12
  text=t.blob('docs/正式非Long开发结果.md').decode()
  for phrase in ['单seed差异不能证明稳定收益或等效','完整O2A尚未齐备','未用开发成功率重选模','未证明其语义等价','400条原始试验共4551GPU秒'] :assert phrase in text,phrase
  progress=t.blob('docs/实验进度.md').decode()[:1000]
  assert all(x in progress for x in ['64/72','400','600','527.796','0/35200'])
  result.update({'findings':[],'status':'passed','root_complete':64,'reviewed_arm_updates':321000,
   'new_development_acceptances':accepted_checks,'all_original_development_trials':3212,'current_wrapper_actual_trials':2000,
   'current_unique_initial_states':300,'unique_states_by_suite':unique,'legacy1212_not_relabelled':True,
   'explicit_Long_legacy_equivalent_trials':600,'compatible_current_plus_explicit_legacy_trials':2600,
   'single_seed_nonLong_limitation_preserved':True,'new_submissions':job_delivery,'new_planned_trials':600,'new_pending_trials_accepted':0,
   'pull':pull_index['pull'],'pull_files_exact_Git_bytes':pull_files,'immutable_nonweight_archive_tree_identical_to_base':True,
   'archive_objects_unchanged':len(archivepaths),'index_guard':binding['index_guard_ref'],'git_delivery':binding['git_delivery_ref'],
   'allocated_GPU_hours_at_snapshot':summary['allocated_GPU_hours'],'accepted_GPU_cost_not_counted_twice':True,
   'live_scheduler_queried':False,'active_job_outputs_collected':False,'checkpoint_bytes_read':False,'sealed_values_read':False,
   'decompression_repeated':False,'scope_note':'Exact committed snapshot and pinned prior audits. No live scheduler query, trial rerun, model load, state write, Git index write, or authenticated remote command.',
   'commit_receipt':binding['commit_receipt'],'entrypoint':ref(str(Path(__file__).relative_to(R)),sha(Path(__file__).read_bytes())),
   'bindings':ref(str(bp.relative_to(R)),sha(raw)),'total_audit_wall_seconds':time.monotonic()-started})
 finally:t.close()
 report=put('independent_review.json',result)
 files=[]
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='manifest.json':
   b=p.read_bytes();files.append({'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)})
 manifest=put('manifest.json',{'schema':'formal_main_v2','kind':'independent_exact_commit_delivery_manifest','status':'passed','commit':C,'files':files})
 print(json.dumps({'status':'passed','report':report,'manifest':manifest,'live_scheduler_queried':False}))
except Exception as e:
 failure=put('failure_a1.json',{'status':'failed','type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'binding':binding,'scientific_results_modified':False,'CPU_wall_seconds':time.monotonic()-started})
 print(json.dumps({'status':'failed','failure':failure}));raise
