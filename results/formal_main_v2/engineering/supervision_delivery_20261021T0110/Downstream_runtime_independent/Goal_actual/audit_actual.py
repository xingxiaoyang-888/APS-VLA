from pathlib import Path
import copy,hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=Path(__file__).parent;B='results/formal_main_v2/preflight/heartbeat_20261021T0910';X='results/formal_main_v2/engineering/goal_full200_20261021T0110';A=R/X/'dispatch_attempt01';JID='3054717'
checks=[];originals=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ok(v,msg):
 if not v:raise AssertionError(msg)
 checks.append(msg)
def write(n,v):
 p=D/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
def load(p,pin,n):
 ok(h(p)==pin,'exact imported pure validator '+str(p.relative_to(R) if p.is_relative_to(R) else p))
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def capture(p,name,pin=None):
 if pin:ok(h(p)==pin,'pinned actual fact '+name)
 b=p.read_bytes();o=D/'facts'/name;o.parent.mkdir(parents=True,exist_ok=True)
 with o.open('xb') as f:f.write(b)
 ok(o.read_bytes()==b,'private byte-preserving copy '+name);originals.append(dict(path=str(p),sha256=h(o),bytes=len(b),private='facts/'+name))
 return json.loads(b)
def same_rp(n,pin=None):
 ok(h(R/n)==h(P/n),'actual R/P bytes match '+n)
 if pin:ok(h(R/n)==pin,'actual published SHA '+n)
def main():
 pub=capture(R/B/'Goal_source_publication.json','Goal_source_publication.json','da0604b6d7a56b41fee618eeb2bf15a3e6b6f1c93d84f7c0e61318903843676b')
 runtime_review=read(R/'.local/downstream_runtime_independent_20261021T0110/Goal_full200/final_independent_review.json')
 dispatch_review=read(R/'.local/downstream_runtime_independent_20261021T0110/Goal_dispatch/final_independent_review.json')
 expected={**runtime_review['package_files'],**dispatch_review['dispatch_files'],'scripts/ops/formal_goal_full200_gate_v1/package_manifest.json':runtime_review['package_manifest_sha256']}
 ok(len(expected)==13 and pub['installed_files']==expected,'actual published 13 sources equal independently frozen package maps')
 for n,pin in expected.items():same_rp(n,pin)
 cap=capture(R/B/'Goal_actual_P_capture.json','Goal_actual_P_capture.json','28fe306af50f2fc9e31be87c74c725e940ca477ac7e58caa183ab2d37d032e4b')
 cfg=expected['scripts/ops/formal_goal_full200_gate_v1/config.json'];ms=runtime_review['package_manifest_sha256'];entry=expected['scripts/ops/formal_goal_full200_gate_v1/entry.py']
 ok(cap['returncode']==0 and cap['stderr']=='' and cap['runtime_files']==runtime_review['package_files'],'actual P capture success and exact runtime map')
 ok(cap['argv']==['/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python','-B',str(P/'scripts/ops/formal_goal_full200_gate_v1/entry.py'),'--verify','--package-manifest-sha256',ms],'actual P canonical argv')
 value=json.loads(cap['stdout'])
 ok(value['status']=='passed_metadata_source_capacity_only' and value['package_manifest_sha256']==ms and value['config_sha256']==cfg,'actual P identity result bound')
 ok(value['identity']['original_fixed200_identity_order'] and value['identity']['unique_development_states']==100 and value['original200_HOLD'] and not value['actual_GPU_runtime_verified'] and not value['final_release'],'actual P complete fixed200 metadata but no GPU/old200/final adoption')
 for key,required in [('raw',9345375040),('local',5157355520)]:
  f=value['storage'][key];ok(f['required_bytes']==required and f['free_bytes']>=required and f['writable'] and not f['symlink'],'captured two-root storage bound '+key)
 ok(value['storage']['exclusive_claim_required_at_execution'] and value['storage']['filesystem_space_can_change_after_check'] and not value['storage']['new_storage_paths_created'],'login capacity is not future compute claim')
 auth=capture(R/X/'root_authorization.json','root_authorization.json','07a265e02fd283603b1ec4c7e555d75d00318e821c824f02dbf419988987dc5b')
 adm=capture(R/X/'dispatch_admission.json','dispatch_admission.json','7b6b64397f96175e1184c956766739ab8261bcfa71cd0faef0f7e275e85381a5')
 authsha=h(R/X/'root_authorization.json');token='cti-goal-full200-v1:'+authsha
 e=load(P/'scripts/ops/formal_goal_full200_gate_v1/entry.py',entry,'goal_actual_entry_pure_checks')
 g=load(R/'scripts/ops/formal_goal_full200_dispatch_v1/dispatch.py',expected['scripts/ops/formal_goal_full200_dispatch_v1/dispatch.py'],'goal_actual_dispatch_pure_checks')
 e.validate_authorization(auth,cfg,ms,entry);g.check_admission_fields(adm)
 ok(True,'actual unchanged published authorization and admission metadata validators accept raw records')
 for n in ['root_authorization.json','dispatch_admission.json','root_readiness.json','independent_readiness.json','reservation.json','held_dispatch_record.json']:same_rp(X+'/'+n)
 for k,reviewer in [('root_review','root'),('independent_review','independent')]:
  rp=Path(auth[k]['path']);ok(rp.is_relative_to(P) and h(rp)==auth[k]['sha256'],'authorization '+k+' exact original reference')
  rv=capture(rp,k+'.json',auth[k]['sha256']);e.check_review(rv,reviewer,ms,cfg);ok(True,'original runtime check_review '+reviewer)
 for k in ['authorization','actual_P_verification','runtime_independent_review','dispatch_independent_review']:
  ref=adm[k];p=R/ref['path'];ok(h(p)==ref['sha256'] and p.stat().st_size==ref['bytes'],'admission full actual binding '+k)
 for n in ['Goal_root_authorization_receipt.json','Goal_dispatch_admission_receipt.json']:
  capture(R/B/n,n)
 names=['committed.json','failed_transaction.json','held_capacity_before_registration.json','held_identity.json','pending.json','post_release_observation.json','preflight.json','registered_held.json','release_attempt.json','release_result.json','released_identity.json','sbatch_result.json']
 ok(sorted(p.name for p in A.iterdir() if p.is_file())==sorted(names),'one exact immutable transaction fact set, no second ACK or release')
 facts={n:capture(A/n,'dispatch_attempt01/'+n) for n in names}
 ok(h(A/'post_release_observation.json')=='88e68958535098af680ed0c8e2ee5a6fcce88d372a99c2fdcc2d8963f4507b93','saved post release observation exact')
 after=capture(R/B/'final_state_before.json','state_at_transaction_committed.json','2e53569c6435abd3fc9d1d9898d33938205c4ddef916938ac4b6af632202f104')
 before=capture(R/'.local/downstream_runtime_independent_20261021T0110/Object_transaction/state_at_committed.json','state_before_Goal_transaction.json','b37d2469bd25d54fed2a61cfdc22fe7b882f52e85f929412977f4c8b8dd4e81c')
 ok(facts['preflight.json']['state_sha256']==h(D/'facts/state_before_Goal_transaction.json')==cap['state_sha256'],'fresh original state CAS chain to actual P')
 ack=facts['sbatch_result.json'];pending=facts['pending.json'];held=facts['registered_held.json'];post=facts['post_release_observation.json'];done=facts['committed.json']
 ok(ack['returncode']==0 and ack['stdout']==JID+'\n' and ack['stderr']=='','single unique original sbatch ACK3054717')
 bundle=dict(comment=token,authorization_sha256=authsha)
 argv=g.sbatch_argv(bundle)
 ok(ack['actual_sbatch_argv']==pending['actual_sbatch_argv']==facts['preflight.json']['actual_sbatch_argv']==argv,'original ACK, pending and preflight all exact held/no-requeue argv')
 ok(pending['submission_token']==token==pending['slurm_comment'] and pending['requested_gpus']==1 and pending['automatic_retry'] is False,'pending exact token and one GPU without retry')
 failure=facts['failed_transaction.json'];ok(failure['status']=='HOLD_reconcile_original_ACK_only' and failure['error']=='missing registered allocation' and failure['automatic_retry'] is False,'original immediate accounting lag failure preserved')
 release=facts['release_attempt.json'];result=facts['release_result.json']
 ok(release['argv']==result['argv']==['scontrol','release',JID] and result['returncode']==0 and result['stdout']==result['stderr']=='','one original successful release fact')
 ok(release['state_sha256']==held['state_sha256'] and release['submission_token']==token,'release bound to already registered held state and original token')
 ok(pending['created_utc']<ack['started_utc']<ack['returned_utc']<failure['utc']<release['utc']<post['utc'],'durable pending then original ACK, failure retained, then one release')
 job=held['job'];ok(job['job_id']==JID and job['original_sbatch_ACK']==ack['stdout'] and job['ACK_reconciled_by_token_comment'],'registration linked to original ACK')
 ok(job['invocation_sha256']==authsha and job['submission_token']==token and job['mode']=='development' and job['goal_dispatch_mode']==g.MODE and job['run_root']==str(P/g.OUT/'original_run'),'actual v2 canonical registration and consumer-compatible scope')
 ok(job['source_sha256']==g.SOURCE and job['package_manifest_sha256']==ms and job['scientific_trials']==0 and not job['final_states_opened'],'original source identity and scientific hold in actual new row')
 for n,isheld in [('held_identity.json',True),('released_identity.json',False)]:
  fact=facts[n];ok(fact['returncode']==0 and fact['fields']==g.fields(fact['stdout']),'original scontrol raw parsed '+n)
  g.validate_new_identity(job,bundle,fact['fields'],isheld);ok(True,'exact actual resource/name/comment/held status '+n)
 dispatch=capture(R/X/'held_dispatch_record.json','held_dispatch_record.json','47dc4866ac0cf3ae61fcbba113a27f68952412332ffc4bfbfdc116b3bf604384')
 reservation=capture(R/X/'reservation.json','reservation.json','6f4619f0066715d58cb32974e5e48d114c889fdfd0ba6ab869b53b75101664f1')
 e.validate_dispatch(dispatch,reservation,auth,authsha,JID,h(R/X/'reservation.json'));ok(True,'actual runtime unchanged dispatch validator accepts exact held record/reservation')
 ok(dispatch['state_after_sha256']==held['state_sha256'] and dispatch['actual_sbatch_argv']==argv and dispatch['source_files']=={k:v for k,v in expected.items() if not k.endswith('/package_manifest.json')},'held record source closure, original argv and CAS')
 ids=[str(j['job_id']) for j in after['registered_jobs']];ok(len(ids)==len(set(ids))==303,'unique all-project registry IDs')
 ok([j for j in after['registered_jobs'] if str(j['job_id'])!=JID]==before['registered_jobs'],'all302 historical registration rows unchanged by Goal transaction')
 actual=[j for j in after['registered_jobs'] if str(j['job_id'])==JID][0]
 for key,v in job.items():ok(actual.get(key)==v,'registered original field unchanged '+key)
 ok(done['state_sha256']==h(D/'facts/state_at_transaction_committed.json') and done['job_id']==JID and done['status']=='submitted_once_registered_then_released' and done['automatic_retry'] is False,'original committed state SHA and one-shot outcome')
 ok(after['pending_submission'] is None and after['autonomous_training_v1'].get('pending_submission') is None and after['autonomous_training_v1']['reserved_GPU_slots']==0,'pending cleared only in final commit, reservation0')
 controller=g.controller();rows=controller.parse_sacct(post['observation']['raw_sacct'],set(ids))
 ok(rows==post['observation']['rows'] and set(rows)==set(ids),'all303 raw accounting rows independently reparsed without new query')
 initial=controller.parse_sacct(post['observation']['initial_raw_sacct'],set(ids))
 ok(set(initial)==set(rows),'initial and confirmed accounting cover same unique registry')
 for jid,row in initial.items():
  if row['status'] not in {'PENDING','RUNNING','CONFIGURING','COMPLETING','SUSPENDED','RESIZING'}:ok(row==rows[jid],'stable actual terminal confirmation '+jid)
 for q in post['observation']['queries']:ok(q['returncode']==0,'saved query success '+q['argv'][0])
 ok(post['derived']['occupied']==[JID] and post['derived']['reserved_GPU_slots']==0 and post['lease']['lease_available_measured'],'actual all-mode capacity1 and released controller lease measured')
 formal=[str(j['job_id']) for j in after['registered_jobs'] if j.get('experiment')=='formal_main_v2']
 cost=sum(rows[j]['gpus']*rows[j]['elapsed_seconds'] for j in formal)
 ok(len(formal)==273 and cost==1992263==post['derived']['allocated_formal_GPU_seconds'],'273 formal allocations real total1992263GPU seconds once')
 ok(rows['3054409']['status']=='COMPLETED' and rows['3054409']['elapsed_seconds']==326 and rows['3054409']['gpus']==1,'saved Object completion326GPU seconds distinct from scientific acceptance')
 ok(rows[JID]['status']=='PENDING' and rows[JID]['elapsed_seconds']==0 and actual['elapsed_seconds']==0 and actual['gpus']==1,'saved Goal pending0seconds still requests one GPU slot')
 ok(sum(rows[j]['gpus']*rows[j]['elapsed_seconds'] for j in ['3053440','3054127'])==1643,'historical Goal803+840 retained once')
 oldprogress=copy.deepcopy(before['formal_main_progress']);newprogress=copy.deepcopy(after['formal_main_progress'])
 for v in [oldprogress,newprogress]:v.get('parallel_execution',{}).pop('registered_requested_active_GPU_jobs',None)
 ok(oldprogress==newprogress,'scientific progress unchanged by actual Goal transaction')
 for source in originals:ok(h(Path(source['path']))==source['sha256'],'frozen original fact unchanged '+source['path'])
 write('actual_checks.json',dict(status='passed',checks=checks,original_files=originals,scope='published_source_and_saved_transaction_facts_only',new_Slurm_queries=0,no_runtime_output_read=True,CPU_suite_repeated=False))
 review=dict(schema='formal_main_v2',kind='Goal_full200_actual_publication_and_dispatch_independent_review',status='passed_actual_publication_original_ACK_single_release',reviewed_by='independent',blockers=[],source13_R_P_verified=True,actual_P_metadata_source_capacity_verified=True,actual_GPU_runtime_accepted=False,
  scope='published13_sources_actualP_auth_admission_and_frozen_original_ACK_transaction_only',independent_checks=len(checks),checks_sha256=h(D/'actual_checks.json'),
  job_id=JID,original_ACK='3054717\n',unique_submissions=1,unique_release_attempts=1,resubmissions=0,repeated_releases=0,first_accounting_lag_failure_retained=True,
  state_at_transaction_commit_sha256=done['state_sha256'],latest_mutable_state_not_compared=True,
  actual_P_capture_sha256=h(R/B/'Goal_actual_P_capture.json'),authorization_sha256=authsha,admission_sha256=h(R/X/'dispatch_admission.json'),
  saved_observation=dict(path=str((A/'post_release_observation.json').relative_to(R)),sha256=h(A/'post_release_observation.json'),utc=post['utc'],status='PENDING',elapsed_GPU_seconds=0,occupied_GPU_jobs=1,formal_allocations=273,formal_GPU_seconds=cost,cost_final=False),
  original_source173_proof_inherited=dict(path='.local/downstream_runtime_independent_20261021T0110/Goal_dispatch/final_independent_review.json',sha256=h(R/'.local/downstream_runtime_independent_20261021T0110/Goal_dispatch/final_independent_review.json')),
  old_Goal200_HOLD=True,new_scientific_trials_accepted=0,final_sealed=True,remaining_gate='Future actual full200 raw consumer/observer/gate/runtime terminal and independent review; no scientific adoption from submission or metadata.',
  no_runtime_output_read=True,CPU_suite_repeated=False,new_Slurm_queries=0,new_GPU_submissions_by_auditor=0,state_written=False,canonical_or_P_written=False)
 write('independent_review.json',review)
 print(json.dumps(dict(status=review['status'],checks=len(checks),review_sha256=h(D/'independent_review.json'))))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write('audit_failure.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks=checks,production_mutation=False));raise
