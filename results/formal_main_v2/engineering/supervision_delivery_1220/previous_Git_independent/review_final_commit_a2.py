"""Bounded read-only final commit audit; no simulation, scheduler, or Git writes."""
from pathlib import Path
import hashlib,json,os,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/final_delivery_independent_1032'
B='results/formal_main_v2/preflight/heartbeat_20261020T1832/'
C='f14596305af9b875fb97d87183cd1e747d90f027'
BASE='908ecc34488bc02d112d60490ff7f6d5770bd584'
CORE=D/'review_commit_core.py'
CORE_SHA='31c7eb063b95c207e079ce36f84bb259f6e4e8066b9161c9c0de9665ebfe6330'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(path,pin):return {'path':path,'sha256':pin}
def put(name,value):
 p=D/name
 assert not p.exists(),str(p)
 b=(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
 p.write_bytes(b)
 return {'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)}
assert sha(CORE.read_bytes())==CORE_SHA
ns={'__name__':'independent_commit_core'}
exec(compile(CORE.read_bytes(),str(CORE),'exec'),ns)
mandatory=[
 ref(B+'summary_after_dispatch.json','06c3937e0a974c8a8e12bf33d7a862021d4e587c393ceab2f89342ab36393266'),
 ref(B+'git_index_guard.json','a7cf19c0090ab24fa81bb1efa7624df1eb04c9b42b181d52516a4bef2b2121e1'),
 ref(B+'git_delivery.json','86d75045b31ea015dab785eae9fdd8a335451db7791df5d3ae90d327eca911c4'),
 ref(B+'Long_legacy600_development_compatibility_proof.json','8468cf4fe4f9cf80741cff7d6d659ab733472ef8d4c5e825e59c0cd8e02a002a'),
 ref(B+'Long22_development_root_acceptance.json','62e95ee07f7dc6ba80a21dff177c0106279f8b462930de5074d7561ccecf5254'),
 ref(B+'Long22_development_statistics.json','35557e76c338ec0cb12f5dbb5b1871dc04d0ad3a8a807134b1ef320728c3abf1'),
 ref('results/formal_main_v2/nonweight_archives/v1/snapshots/Spatial64seed23_20261020_1032.json','46d99a0368858d1301310a890380873331a65f3f21ac4011605b00b41c06d9c4')
]
required_ref=ref(B+'git_required_files.json','64049f3c20659de23a86bc214d8a385d613aaf4ca93bf058fd8a9f8d1a0ec08b')
push_ref=ref('.local/github_push_1032_verified.json','e6d468d78c23f7a5bec89b14027e665de1ac51613a76a9fa93142abf0f0d09aa')
commit_ref=ref('.local/git_commit_1032.json','7f72e12fc999fd66f593906539fd0fe978d80d57ddf5728414d22d29a62660b1')
started=time.monotonic()
try:
 cb=(R/commit_ref['path']).read_bytes()
 assert sha(cb)==commit_ref['sha256']
 cr=json.loads(cb)
 assert cr['commit']==C and cr['baseline']==BASE and cr['files']==381 and cr['root_complete']==64
 t=ns['Tree'](C)
 try:
  req=json.loads(t.ref(required_ref));assert len(req['files'])==377
  summary=json.loads(t.ref(mandatory[0]))
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
  jobs=summary['development_submissions']
  job_refs=[item[k] for item in jobs for k in ['authorization','original_ACK','original_failed_transaction','root_reconciliation','independent_submission_review']]
  cfg={'commit':C,'base_commit':BASE,'verified_push_ref':push_ref,'required_files_ref':required_ref,'mandatory_refs':mandatory,
       'extra_commit_paths':[B+'git_index_guard.json',B+'git_delivery.json',B+'git_whitespace_diagnostic.json'],
       'closed_transport_refs':closed,'archive_delivery_refs':deliveries,'job_delivery_refs':job_refs,
       'new_job_ids':['3048572','3048581','3048609'],
       'doc_paths':['docs/完整实验计划.md','docs/实验进度.md','docs/正式Long完整开发结果.md','docs/正式主实验规划.md','docs/正式主实验阶段结论.md','docs/正式自动连续训练执行登记.md'],
       'json_assertions':[]}
  expected={'root_independent_complete':64,'total_arms':72,'root_independent_updates':321000,'source_files_unchanged':173,
            'active_GPU_jobs':7,'actual_running_GPUs':7,'allocated_GPU_seconds':1881881,'cost_is_final':False,
            'Long_compatible_development_trials':2200,'Long_unique_initial_states':100,'current_wrapper_actual_trials':1600,
            'completed_final_trials':0,'expected_final_trials':35200,'final_sealed':True,
            'new_GPU_submissions_by_root':['3048572','3048581','3048609'],'new_planned_development_trials':1000,
            'new_development_trials_accepted':0,'new_duplicate_submissions':0,'retained_failure_GPU_seconds':73}
  cfg['json_assertions']=[{'path':mandatory[0]['path'],'keys':[k],'expected':v} for k,v in expected.items()]
  assert json.loads((D/'final_bindings.json').read_text())==cfg
 finally:t.close()
 result=ns['audit'](cfg)
 assert result['changed_paths']==381 and result['archive_copy_files_verified']==156
 t=ns['Tree'](C)
 try:
  summary=json.loads(t.ref(mandatory[0]));guard=json.loads(t.ref(mandatory[1]));delivery=json.loads(t.ref(mandatory[2]))
  assert guard['status']=='verified_index_archive_delivery'
  assert guard['head']==BASE and guard['frozen_files_verified_in_worktree_and_index']==173
  assert guard['required_files']['sha256']==required_ref['sha256']
  assert guard['required_count']==377 and guard['ordinary_staged_files_verified']==378
  assert guard['archive_verification']=='verified' and guard['restore_verification']=='restored_verified'
  assert guard['real_originals_changed'] is False and guard['scientific_completion_inferred'] is False
  assert guard['codec_sha256']=='f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2'
  assert guard['checker_sha256']=='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
  assert sha(t.blob('scripts/ops/nonweight_archive.py'))==guard['codec_sha256']
  assert sha(t.blob('scripts/ops/check_nonweight_archive_stage.py'))==guard['checker_sha256']
  for row in guard['archive_index_files'].values():t.ref(row)
  snap=json.loads(t.ref(mandatory[-1]))
  raw=guard['raw_paths_restored_exactly']
  assert len(raw)==3 and sum(x['bytes'] for x in raw)==156929174
  assert all(x['path'] not in t.rows for x in raw)
  expected_raw={x['path']:(x['sha256'],x['bytes']) for x in raw}
  assert {x['path']:(x['sha256'],x['bytes']) for x in snap['files']}==expected_raw
  assert len([p for p in guard['archive_index_files'] if p.endswith('.gz')])==11
  archive_review=json.loads(t.ref(summary['archive_independent_review']))
  assert archive_review['status']=='passed_archive_reconstruction_and_historical_raw_Git_identity'
  assert archive_review['new_archived_raw_bytes']==156929174
  assert all(x['decoded_stream_matches_original_byte_for_byte'] for x in archive_review['new_archived_raw'])
  for r in archive_review['new_stdout_stderr_originals']:t.ref(r)
  for r in delivery['raw_original_whitespace_preserved']:t.ref(r)
  assert len(delivery['raw_original_whitespace_preserved'])==3
  assert delivery['weights_added'] is False and delivery['sealed_final_values_added'] is False
  assert delivery['final_sealed'] is True and delivery['active_runs_not_terminally_collected'] is True
  state=json.loads(t.blob('results/experiment_supervisor/state.json'))
  def records(v,path='$'):
   if isinstance(v,dict):
    if str(v.get('job_id','')) in cfg['new_job_ids'] and 'invocation' in v and 'downstream_gateway' in v:yield(path,v)
    for k,x in v.items():yield from records(x,path+'.'+k)
   elif isinstance(v,list):
    for i,x in enumerate(v):yield from records(x,path+'['+str(i)+']')
  registered=list(records(state));job_delivery=[]
  for idx,item in enumerate(summary['development_submissions']):
   jid=item['job_id'];auth=json.loads(t.ref(item['authorization']))
   assert auth['maximum_attempts']==1 and auth['automatic_retry'] is False
   assert auth['final_release_authorized_by_gateway'] is False and auth['plan_arguments']['stage']=='development'
   for k in ['controller','controller_activation','planner','independent_review','plan','prepared_invocation','root_reservation','runtime_readiness','scientific_plan']:t.ref(auth[k])
   for p,h in auth['gateway_files'].items():t.ref(ref(p,h))
   ack=json.loads(t.ref(item['original_ACK']));failure=json.loads(t.ref(item['original_failed_transaction']))
   rec=json.loads(t.ref(item['root_reconciliation']))
   assert ack['returncode']==0 and ack['stdout'].strip()==jid
   assert failure['automatic_retry'] is False and failure['error']=='post-submit accounting incomplete'
   assert failure['status']=='stopped_requires_root_reconciliation_no_retry'
   token='cti-downstream-gateway-v1:'+item['authorization']['sha256']
   assert '--comment='+token in ack['actual_sbatch_argv'] and '--no-requeue' in ack['actual_sbatch_argv']
   assert rec['new_submissions']==0 and rec['automatic_retry'] is False
   assert rec['status']=='exact_original_ACK_job_reconciled'
   assert rec['original_ACK']==item['original_ACK'] and rec['original_failure']==item['original_failed_transaction']
   assert rec['lifecycle_lease_held'] and rec['all173_R_and_S_match']
   assert rec['unrelated_controller_fields_unchanged'] and rec['final_release_authorized'] is False
   assert rec['exact_reservation_consumed']==auth['root_reservation']
   job=rec['job']
   assert job['job_id']==jid and job['suite']==item['suite'] and job['method_ids']==item['method_ids']
   assert job['downstream_gateway']['request_token']==token
   assert job['downstream_gateway']['actual_sbatch_argv']==ack['actual_sbatch_argv']
   assert job['mode']=='development' and job['gpus']==1
   assert job['invocation_sha256']==auth['prepared_invocation']['sha256']
   assert t.ref(ref(job['invocation'],job['invocation_sha256']))==t.ref(auth['prepared_invocation'])
   t.ref(job['action_execution_contract'])
   t.ref(ref(job['wrapper'],job['wrapper_sha256']))
   t.ref(rec['original_preflight'])
   cp=str(Path(item['original_ACK']['path']).parent/'committed.json')
   committed=json.loads(t.blob(cp))
   assert committed['job']==job and committed['request_token']==token and committed['reservation_consumed'] is True
   assert committed['automatic_retry'] is False and committed['root_reconciliation']==item['root_reconciliation']
   assert len(rec['capacity']['occupied'])==5+idx and not rec['capacity']['unknown'] and not rec['capacity']['findings']
   matches=[(p,r) for p,r in registered if str(r['job_id'])==jid]
   assert matches,jid
   identity_fields=['job_id','suite','method_ids','invocation','invocation_sha256','mode','stage_key','source_sha256','wrapper_sha256']
   assert all(all(r[k]==job[k] for k in identity_fields) for p,r in matches)
   assert item['completed_trials_accepted']==0 and item['final_evaluation_enabled'] is False
   assert item['duplicate_submissions']==0 and item['scientific_terminal_acceptance_pending'] is True
   job_delivery.append({'job_id':jid,'planned_trials':item['planned_trials'],'accepted_trials':0,
    'authorization':item['authorization'],'original_ACK':item['original_ACK'],
    'failure_retained':item['original_failed_transaction'],'reconciliation':item['root_reconciliation'],
    'committed_registry_matches':[p for p,r in matches],'original_single_submission_evidence_retained':True})
  assert sum(x['planned_trials'] for x in job_delivery)==1000
  progress=t.blob('docs/实验进度.md').decode()
  assert '64/72' in progress[:500] and '522.745' in progress[:1300] and '1000' in progress[:1300]
  longdoc=t.blob('docs/正式Long完整开发结果.md').decode()
  assert all(s in longdoc for s in ['100个唯一初态','600条旧版等价','1600条新版实际执行','开发结果','无O2A','最终0/35200'])
  result.update({'findings':[],'root_complete':64,'reviewed_arm_updates':321000,'allocated_GPU_hours_at_snapshot':summary['allocated_GPU_hours'],
   'job_delivery_lineage':job_delivery,'frozen_final_trials':0,
   'archive_delivery':{'snapshot':mandatory[-1],'original_files':3,'original_bytes':156929174,'compressed_chunks':11,
    'exact_committed_archive_refs_match_prior_restore_receipt':True,'raw_logs_absent_from_commit':True,
    'prior_restore_status':guard['restore_verification'],'independent_archive_review':summary['archive_independent_review'],
    'decompression_repeated_by_this_audit':False},
   'scope_note':'Committed snapshot only. Ongoing controller state/log appends are allowed and were not required to equal this commit. Prior byte-exact restoration evidence was checked; no redundant decompression or science rerun.',
   'live_scheduler_queried':False,'all_immutable_agent_deliveries_verified':True,
   'audit_assumption_correction':'a1 expected a generic passed string; a2 checks the precise published archive receipt status. The original failure and source are retained; no production evidence was changed.',
   'commit_receipt':commit_ref,'entrypoint':ref(str(Path(__file__).relative_to(R)),sha(Path(__file__).read_bytes())),
   'total_audit_wall_seconds':time.monotonic()-started})
 finally:t.close()
 report=put('independent_review.json',result)
 files=[]
 for p in sorted(D.iterdir()):
  if p.is_file() and p.name!='manifest.json':
   b=p.read_bytes();files.append({'path':str(p.relative_to(R)),'sha256':sha(b),'bytes':len(b)})
 manifest=put('manifest.json',{'schema':'formal_main_v2','kind':'independent_review_manifest','status':'passed','commit':C,'files':files})
 print(json.dumps({'status':'passed','report':report,'manifest':manifest,'frozen':173,'changed_files':381,'live_scheduler_queried':False}))
except Exception as e:
 failure=put('failure_a2.json',{'status':'failed','error':str(e),'type':type(e).__name__,'traceback':traceback.format_exc(),'commit':C,'scientific_results_modified':False})
 print(json.dumps({'status':'failed','failure':failure}))
 raise
