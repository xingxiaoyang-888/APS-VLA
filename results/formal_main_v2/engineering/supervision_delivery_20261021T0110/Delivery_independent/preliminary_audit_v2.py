"""Read-only root delivery preliminary audit. Goal author code is excluded from independent scope."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).parent
B='results/formal_main_v2/preflight/heartbeat_20261021T0910';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0110'
checks=[];evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(n,v,detail=None):
 checks.append({'name':n,'passed':bool(v),'detail':detail})
 if not v:raise AssertionError(n)
def read(n,pin=None):
 p=R/n;b=p.read_bytes();actual=sha(b);ck('pin/'+n,pin is None or actual==pin)
 evidence[n]={'sha256':actual,'bytes':len(b)};return json.loads(b)
def source(n,pin):
 b=(R/n).read_bytes();ck('source/'+n,sha(b)==pin);evidence[n]={'sha256':sha(b),'bytes':len(b)};ast.parse(b);return b.decode()
def write(n,v):
 p=D/n
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def main():
 accept=source('.local/accept_spatial588_20261021T0110_v1.py','85befd265e100b4a47c921580933132a6987476fc2a9443392d75e472fe2ba65')
 deliver=source('.local/deliver_20261021T0110_v1.py','d9c592c4985b8b8c00677705fdaa084bc1a0b17ed5df2a77b97f1c73efa41282')
 push=source('.local/github_push_20261021T0110.py','d177fde4c56092ba2728bc9a1a37debb78c62c51c4a24ea46c77dd07d4fcdf69')
 archive=source('.local/archive_packages_20261021T0110_v3.py','a93f9f7619c2c2cde4c14cd870f4499e10d2e8a92d4fe32d1ec9f15863a315c9')
 snapshot=source('.local/final_snapshot_20261021T0110_v1.py','49cc46f515e495005a661059d091aa2b5ae4d8432689d4da470c5efa56c44d70')
 # Static review recorded only for exact read sources; these programs are NOT executed.
 ck('root_acceptance_lock_CAS',all(t in accept for t in ['exclusive_lock','assert h(R/STATE)==BEFORE','os.replace(tmp,R/STATE)','accepted_after_original_typed_consumer_and_independent_raw_review','source173_verified']))
 ck('git_lock_empty_index_exact_final_review',all(t in deliver for t in ["with c.exclusive_lock","git('diff','--cached','--name-only').stdout==b''","audit['status']=='passed_final_delivery_review'","audit['state_sha256']==h(R/'results/experiment_supervisor/state.json')"]))
 ck('git_nonweight173_allowlist_checks',all(t in deliver for t in ["frozen_files_verified_in_worktree_and_index']==173","force_refs[rel]={'path':rel,'sha256':row['sha256'],'bytes':row['bytes']}","git('add','-f','--',*selected","not in ['.pt','.pth','.ckpt','.safetensors','.bin'","--cached','--check"]))
 ck('git_only_exact_archived_whitespace_exceptions',"n.startswith((E+'/',B+'/root_operations/'))" in deliver and "git('diff','--cached','--check','--','.'" in deliver)
 ck('no_live_Slurm_in_delivery_helpers',all(not any(x in t for x in ["'sbatch'","'squeue'","'sacct'","'scontrol'"]) for t in [accept,deliver,push,snapshot]))
 ck('push_stdin_temporary_and_exact_HEAD',all(t in push for t in ['auth=json.load(sys.stdin)','del auth',"--expected-head","value['credentials_persisted'] is False","value['local_head']==value['remote_head_after']==args.expected_head"]))
 sync=source('scripts/ops/server_github_sync.py','218bf59be0f28ed145a38ed4196cf02b5a6134fcf8a4531abf127f838cc5f729')
 ck('sync_no_force_push',not any(s in sync for s in ['--force','force-with-lease']))
 ck('archive_exact_manifest_no_loose_weights',all(t in archive for t in ['len(files)==count','h(src)==row["sha256"]'.replace('"',"'"),'not_runtime_admission=True',"assert not raws","with c.exclusive_lock"]))
 snap=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 ck('frozen_source173_count',len(snap['files'])==173)
 for n,h in snap['files'].items():
  for label,base in [('R',R),('Rmirror',R/'snapshots/formal_main_v2_run_564be0995e'),('S',P/'snapshots/formal_main_v2_run_564be0995e')]:
   ck('frozen173/'+label+'/'+n,sha((base/n).read_bytes())==h)
 tx=read(B+'/Spatial3054201_acceptance_transaction.json','5ac3e4dbbd778d31f086e62ba2dab21160886af50bb0dd0f70d3ed5fd7196ed1')
 adoption=read(tx['acceptance']['path'],tx['acceptance']['sha256'])
 rr=read(adoption['root_review']['path'],adoption['root_review']['sha256'])
 independent=read(adoption['independent_review']['path'],adoption['independent_review']['sha256'])
 ck('Spatial_two_actual_terminal_reviews',rr['status']=='passed' and rr['scientific_complete'] and rr['completed_trials']==600 and independent['status']=='passed_real_raw_terminal_review' and not independent['blockers'] and independent['original_typed_consumer_rebuilt'])
 ck('Spatial_review_declared_independent',independent['reviewed_by']=='independent')
 for n,h in rr['files'].items():
  for label,base in [('R',R),('P',P)]:ck('Spatial_review_raw/'+label+'/'+n,sha((base/n).read_bytes())==h)
 ledger='results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01/trials.jsonl'
 raw=(R/ledger).read_bytes();evidence[ledger]={'sha256':sha(raw),'bytes':len(raw)}
 ck('Spatial_old12_raw_prefix_original',sha(raw[:592887])=='3a175dbc5dd7a23cd2c3c8385cb6ff3c525f09d4e607ff32a69a10869672a2f9')
 rows=[json.loads(line) for line in raw.splitlines()];byorigin=defaultdict(list);starts={};origin=None;invocations=[]
 for row in rows:
  if row['event']=='invocation':origin=row['slurm_job_id'];invocations.append(origin)
  elif row['event']=='start':ck('unique_start/'+row['trial_id'],row['trial_id'] not in starts);starts[row['trial_id']]=row
  elif row['event']=='result':
   ck('unique_completed_start_result/'+row['trial_id'],row['trial_id'] in starts and row['status']=='completed')
   for k in ('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method'):ck('raw_identity/'+row['trial_id']+'/'+k,row[k]==starts[row['trial_id']][k])
   byorigin[origin].append(row)
  else:raise AssertionError('unexpected Spatial raw event')
 ck('Spatial_real_invocations_only',invocations==['3022743','3054201'])
 ck('Spatial12legacy588current',dict((k,len(v)) for k,v in byorigin.items())=={'3022743':12,'3054201':588})
 result={}
 for jid,sub in byorigin.items():
  methods={m:{'completed_trials':len([r for r in sub if r['method']==m]),'successes':sum(r['success'] for r in sub if r['method']==m)} for m in sorted({r['method'] for r in sub})}
  result[jid]={'completed_trials':len(sub),'unique_initial_states':len({r['state_trial_id'] for r in sub}),'methods':methods}
  original=adoption['origin_breakdown'][jid]
  ck('Spatial_origin_exact/'+jid,all(original[k]==v for k,v in result[jid].items()))
 whole=sum(byorigin.values(),[])
 ck('Spatial_unique100',len({r['state_trial_id'] for r in whole})==100)
 ck('Spatial_full_each100',set(Counter(r['method'] for r in whole).values())=={100})
 ck('Spatial_scope_not_global_freeze',all(adoption[k] is False for k in ('current_action_global_freeze_eligible','profiling_authorized','final_release')) and adoption['global_unique_initial_states_added']==0)
 ck('Spatial_all_cost_once',adoption['cost']['all_attempt_gpu_seconds']==7030 and {j['job_id']:j['elapsed_seconds'] for j in adoption['cost']['allocations']}=={'3022743':393,'3042529':2,'3054201':6635})
 before=read(B+'/Spatial3054201_state_before.json','3281eaab5f761b3aa61bf702b3b3d4b36386569667d17ff343e7199e4f159796')
 ck('before_original_state_canonical_bytes',sha((json.dumps(before,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode())==tx['before_sha256'])
 f=before['formal_main_progress']
 ck('Spatial_before_5800_7012',sum(j['completed_trials'] for j in f['new_action_development_verified_by_job'].values())==f['current_action_development_trial_count']==5800 and f['completed_development_trials']==7012)
 ck('Spatial_arithmetic_and_denominators',tx['current_trials']==5800+588==6388 and tx['complete_batch_trials']==6388+600+12==7000 and tx['historical_accepted_trials']==7012+588==7600 and tx['unique_initial_states']==400)
 observation=read(B+'/terminal_observation_from_Object_preflight.json','89820eb12808cce09c4882c7ce17d189b44b8e01c460299663a32fd0c64e3c94')
 formal=[j for j in before['registered_jobs'] if j.get('experiment')=='formal_main_v2'];ids=[str(j['job_id']) for j in formal];o=observation['observation']['rows']
 ck('Spatial_terminal_cost271_unique',len(ids)==len(set(ids))==271 and sum(o[j]['gpus']*o[j]['elapsed_seconds'] for j in ids)==1991937==tx['GPU_seconds'])
 # Only original saved Object ACK/release artifacts; never query healthy GPU.
 X='results/formal_main_v2/execution/object_single_error_v1/gateway_attempt01/'
 ack=read(X+'sbatch_result.json','ba4916ca823bf5d2f61bedc1fba3fc6b856a167f4496be7fd74a78257288728b')
 held=read(X+'registered_held.json','1d451fd23b2cb2823c2da67e9154f793be90e677665726649adb4bec3c840f0e')
 release=read(X+'release_attempt.json','32f30a544508e8781ba46957815afc2e12030ce308a52fb66bb84f611df98073')
 release_result=read(X+'release_result.json','7410fea67d62cf3116568ed4a96240746e49584e9864e800c02d2047de75674d')
 committed=read(X+'committed.json','3f80ee590115f84edd2a4003d75d5bc17acf37a279c8e2eb287b838371bd28b9')
 reconciled=read(X+'reconciled_release.json','e687ede154fc4213a34a40773994317e2f795d70facb304705065548f5dff7b5')
 job=held['job'];fields=reconciled['actual']['fields']
 ck('Object_unique_original_ACK',ack['returncode']==0 and ack['stdout']==job['original_sbatch_ACK']=='3054409\n' and job['job_id']=='3054409' and '--hold' in ack['actual_sbatch_argv'])
 ck('Object_original_exact_comment_command',fields['Comment']==job['slurm_comment'] and '--comment='+fields['Comment'] in ack['actual_sbatch_argv'] and fields['Command']=='/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/scripts/ops/formal_object_single_error_gateway_v1/run.slurm')
 ck('Object_single_release_saved',release['argv']==release_result['argv']==['scontrol','release','3054409'] and release_result['returncode']==0 and reconciled['original_release_attempt']==release)
 ck('Object_original_ACK_commit_no_retry',committed['status']=='original_ACK_reconciled_no_resubmission' and committed['automatic_retry'] is False and job['maximum_attempts']==1 and job['ordinary_resume'] is False)
 ck('Object_actual_release_observed_only_lower_bound',fields['JobState']=='RUNNING' and fields['RunTime']=='00:01:07' and fields['Restarts']=='0' and job['gpus']==1)
 ck('Object_no_science_acceptance_claim',job['final_states_opened'] is False and job['mode']=='object_single_error_linked')
 report={'status':'passed_preliminary_root_delivery_scope_pending_final_snapshot','scope':'independent Spatial count/acceptance transaction, saved Object ACK/release provenance and static root Git/snapshot guards only; own Goal runtime excluded','checks':checks,'source173_verified':True,'Spatial_origin_breakdown_rebuilt_from_raw':result,'Spatial_current_trials_after':6388,'complete_development_batches':7000,'historical_acceptance_catalog':7600,'unique_initial_states':400,'Object_original_ACK':'3054409','Object_GPU_seconds_last_saved':67,'saved272_cost_lower_bound':1991937+67,'snapshot_v1_advisory':['Goal_original200_and_new_science_HOLD must not become false solely on engineering job id; root notified, final exact source/state still required'],'final_review_issued':False,'future_Git_commit_or_push_verified':False,'new_live_Slurm_queries':0,'GPU_submissions':0,'state_writes':0,'Git_operations':0,'P_writes':0,'evidence':evidence}
 return report
try:r=main()
except BaseException as e:
 r={'status':'failed_preliminary_audit','checks':checks,'error':str(e),'traceback':traceback.format_exc(),'evidence':evidence};write('preliminary_review_v2.json',r);print(json.dumps({'status':r['status'],'error':str(e)}));raise
write('preliminary_review_v2.json',r);print(json.dumps({'status':r['status'],'checks':len(checks),'report_sha256':sha((D/'preliminary_review_v2.json').read_bytes())}))
