"""Independent read-only admission/reconciliation audit, Long128 seed41 job3045322.
Uses preserved scheduler observations; writes only its own server audit directory.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,fcntl,hashlib,json,shlex,sys,traceback
from collections import Counter
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
OUT=R/'.local/independent_long128s41_0428'
AUTH='a2104c3cb1d96dd0d8ddd5bf9c0a9b2a19dc04d5cbf8e6fae8d69d9dea6b0730'
D='results/formal_main_v2/execution/long_remaining16_action_v1_1827/k128_seed41'
AR={'path':D+'/submission_authorization.json','sha256':AUTH}
AD='results/formal_main_v2/downstream_gateway/'+AUTH
B='results/formal_main_v2/preflight/heartbeat_20261020T1228'
RECEIPT=B+'/Long3045322_pending_reconciliation.json'
JID='3045322';TOKEN='cti-downstream-gateway-v1:'+AUTH
STAGE='libero_10_development_428eafaeb10a5ce3'
checks=[]; evidence={}
def ck(ok,name):
 if not ok:raise AssertionError(name)
 checks.append(name)
def read(path,pin=None):
 p=Path(path)
 if not p.is_absolute():p=R/p
 raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
 if pin:ck(h==pin,'pin:'+str(p.relative_to(R)) if p.is_relative_to(R) else 'pin:'+str(p))
 evidence[str(p.relative_to(R)) if p.is_relative_to(R) else str(p)]=h
 return raw
def js(path,pin=None):return json.loads(read(path,pin))
def fh(path):
 p=Path(path);before=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 after=p.stat()
 ck((before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns),'stable_file:'+str(p))
 return h.hexdigest()
def parse_snapshot(snap,jobs,label):
 ids=[str(j['job_id']) for j in jobs]
 ck(len(ids)==len(set(ids)),label+': unique registry')
 rows={}
 for line in snap['raw_sacct'].splitlines():
  parts=line.split('|');ck(len(parts)==8,label+': raw accounting shape')
  jid,status,exitcode,elapsed,allocation,node,name,comment=parts
  ck(jid not in rows,label+': unique accounting ID')
  gpu=[x.split('=',1)[1] for x in allocation.split(',') if x.startswith('gres/gpu=')]
  ck(len(gpu)<=1,label+': unambiguous GPU allocation')
  rows[jid]=dict(job_id=jid,status=status,exit_code=exitcode,elapsed_seconds=int(elapsed),allocation=allocation,gpus=int(gpu[0]) if gpu else 0,node=node,scheduler_name=name,scheduler_comment=comment)
 ck(rows==snap['rows'],label+': independent raw accounting reconstruction')
 ck(set(rows)==set(ids),label+': every registered job exactly accounted')
 queue={}
 for line in snap['raw_squeue'].splitlines():
  jid,status,comment=line.split('|',2);ck(jid not in queue,label+': unique queue ID')
  queue[jid]=dict(status=status,comment=comment)
 ck(queue==snap['queue'] and set(queue)<=set(ids),label+': independent raw queue reconstruction')
 terminal={'COMPLETED','FAILED','CANCELLED','TIMEOUT','PREEMPTED','OUT_OF_MEMORY','NODE_FAIL','BOOT_FAIL','DEADLINE','REVOKED'}
 occupied=[];pairs={}
 for job in jobs:
  jid=str(job['job_id']);row=rows[jid]
  ck(row['scheduler_name']==job['name'],label+': job name '+jid)
  if row['status'] in terminal:
   ck(jid not in queue,label+': terminal absent from queue '+jid)
   continue
  ck(row['status'] in {'RUNNING','PENDING','CONFIGURING','COMPLETING','SUSPENDED'} and jid in queue and queue[jid]['status']==row['status'],label+': active state unambiguous '+jid)
  if job.get('gpus')==0:
   ck(row['gpus']==0,label+': registered CPU0 actual allocation '+jid)
   continue
  ck(job.get('gpus')==1 and row['gpus']==1,label+': independent one-GPU allocation '+jid)
  occupied.append(jid)
  if job.get('mode')=='train':
   pk=job['suite']+'_k'+str(job['visual_tokens'])+'_seed'+str(job['training_seed'])
   pairs.setdefault(pk,[]).append(jid)
 ck(all(len(x)==1 for x in pairs.values()),label+': one active job per pair')
 return dict(occupied=occupied,active_pairs=pairs,unknown=[],findings=[])

def canon(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def proof(ref):return js(ref['path'],ref['sha256'])
def audit():
 read('.local/independent_long128s41_0428/failed_attempt01.json','1713aeda5cd552ddce9d8e247c80b6be88bd7c057d088ddd47ab01b61bbf2e6c')
 for path,pin in [('src/cti_vla/evaluation/teacher_diagnostics.py','0d27ee32f1ef8b1a409758416fd3177dfeb1624a2f6f9dd5b9955b53ab06bdfd'),('src/cti_vla/evaluation/formal_runtime.py','4029b0ddd1b6059f9f3586cd21aadd76fd15b516f79b201313a0291a2d64a8f8'),('scripts/formal_execution_manifests.py','614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89')]:read(path,pin)
 auth=js(AR['path'],AUTH)
 reserve=js(B+'/Long128seed41_reservation_activation.json','62297e08e9cb945651f123239dad0b13c68360578b0e335fa1e13d946383f487')
 initial=js(B+'/initial_observation.json')
 pre=js(AD+'/preflight.json','4ddda8b1fb32ccc411f1e1e2dfc45539f57434a85591c18f51db875697a4eb5d')
 ack=js(AD+'/sbatch_result.json','bac669cd22d6bf59207b4dbdc7275febbfa7cb16e6e25ce62483e819d11fcb35')
 fail=js(AD+'/failed_transaction.json','0c402f3fb3ed30bd70103550dc51adf80141a32acf3d7d83a978e2785c4ff6aa')
 rec=js(RECEIPT,'ac21ef6e5beb48417f595b9f0e112dd280810e55f4cf57d763cad84706ee8ea7')
 obs=js(AD+'/submitted_job_observation.json','988839d6ccaaac58365d139c33046f1eea1f28aad02b9cbdcd17de45d2cda8a2')
 commit=js(AD+'/committed.json','6af330f2db244b6c769e5cdba9d8d6d02e9b73a2c5ed459c4598f9d5e8c4acf1')
 job=js('results/formal_main_v2/submissions/'+JID+'.json')
 ck(auth['status']=='approved_for_exactly_one_registered_downstream_submission' and auth['maximum_attempts']==1 and not auth['automatic_retry'] and not auth['final_release_authorized_by_gateway'],'exact single-stage root authority')
 for key in ['independent_review','gap_review','controller','controller_activation','planner']:read(auth[key]['path'],auth[key]['sha256'])
 for path,pin in auth['gateway_files'].items():read(path,pin)
 plan=proof(auth['plan']);science=proof(auth['scientific_plan']);prepared=proof(auth['prepared_invocation']);ready=proof(auth['runtime_readiness']);reservation=proof(auth['root_reservation'])
 intent=copy.deepcopy(auth);intent.pop('root_reservation')
 ck(reservation['authorization_intent_sha256']==hashlib.sha256(canon(intent)).hexdigest() and reservation['authorization_path']==AR['path'],'dedicated reservation exact authority intent')
 ck(reservation['reserved_slots']==1 and reservation['capacity_limit_all_GPU_modes']==8 and reservation['old_CUDA_reservation_must_not_be_reused'] is True and reservation['stage_key']==STAGE,'dedicated one-GPU development reservation')
 ck(reserve['authorization']==AR and reserve['reservation']==auth['root_reservation'] and reserve['new_GPU_submissions']==[] and reserve['new_trials']==0 and reserve['planned_trials']==200,'root activation only reserved, not submitted')
 consumed=reserve['prior_exact_CUDA_reservation_consumed']
 ck(consumed['job_id']=='3044017' and consumed['failed_job_id']=='3028468' and consumed['reservation']==initial['reservation_root_record'] and consumed['reservation']!=auth['root_reservation'],'old consumed CUDA reservation not reused')
 proof(reserve['prior_root_acceptance']);proof(consumed['reservation'])
 ck(ready['effective_plan']==auth['plan'] and ready['scientific_plan']==auth['scientific_plan'] and ready['plan_sha256']==plan['plan_sha256'],'readiness exact current plans')
 ck(ready['allowed_stages']==['development'] and ready['expected_trials']==200 and ready['unique_development_initial_states']==100 and not ready['final_evaluation_enabled'],'only registered 200-trial development scope')
 for role in ['root_review','independent_review']:
  rv=proof(ready[role])
  ck(rv['status']=='passed' and rv['effective_plan']==auth['plan'] and rv['scientific_plan']==auth['scientific_plan'] and rv['plan_sha256']==plan['plan_sha256'] and rv['production_chain_complete'] is True,'nested '+role+' bound')
 for ref in ready['component_reviews'].values():proof(ref)
 contract=proof(prepared['action_execution_contract'])
 for path,pin in contract['GPU_acceptance'].items():read(path,pin)
 ck(contract['final_evaluation_enabled'] is False and contract['scientific_settings_changed'] is False,'accepted action execution only, no scientific change')
 for v,name in [(plan,'effective'),(science,'scientific')]:
  ck(v['plan_sha256']==hashlib.sha256(canon({k:x for k,x in v.items() if k!='plan_sha256'})).hexdigest(),name+' plan content signature')
 inner=science['invocation'];outer=plan['invocation']
 ck(set(plan)==set(science) and all(plan[k]==science[k] for k in science if k not in {'invocation','publish_files','plan_sha256'}),'same resource/output scientific plan')
 mutable={'version','entrypoint','wrapper','wrapper_sha256','support_files','watched_files','root_evidence_sha256'}
 additions={'action_execution_contract','scientific_plan','scientific_plan_sha256'}
 ck(set(outer)==set(inner)|additions and all(outer[k]==v for k,v in inner.items() if k not in mutable),'outer action execution envelope preserves scientific invocation')
 ck(prepared=={**outer,'registered_utc':prepared['registered_utc'],'plan_sha256':plan['plan_sha256'],'runtime_readiness':auth['runtime_readiness']},'prepared invocation exact effective plan')
 invrel=plan['invocation_relative'];raw=read(invrel,auth['prepared_invocation']['sha256'])
 ck(raw==read(P/invrel)==read(auth['prepared_invocation']['path']),'R/P/prepared invocation bytes exact')
 ck(json.loads(raw)==prepared and prepared['method_ids']==['A128_seed41','B128_seed41'] and prepared['stage']=='development' and prepared['suite']=='libero_10' and prepared['resume'] is False and prepared['prior_job_ids']==[],'fresh exact Long128 seed41 A/B development')
 ck(pre['invocation_relative']==invrel and pre['invocation_sha256']==evidence[invrel] and pre['plan']==auth['plan'] and pre['prepared_invocation']==auth['prepared_invocation'],'preflight prepared identity')
 ck(pre['runtime_preflight']['missing_publications']==[] and pre['runtime_preflight']['output_exists'] is False,'pre-submission actual publication and fresh output')
 for rel,pin in prepared['support_files'].items():
  read(rel,pin);read(P/rel,pin)
 for rel,pin in ready['runtime_publication_files'].items():read(rel,pin);read(P/rel,pin)
 invpath=Path(prepared['execution_manifest']);manifest_rel=str(invpath.relative_to(P));manifest=js(manifest_rel,prepared['execution_manifest_sha256'])
 ck(read(P/manifest_rel)==read(manifest_rel),'execution manifest R/P exact')
 ck(manifest['split']=='development' and manifest['suite']=='libero_10' and manifest['environment']=={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':520},'fixed Long development environment')
 ck([m['identity']['method_id'] for m in manifest['methods']]==['A128_seed41','B128_seed41'],'only registered matched two methods')
 panel=js(manifest['development_panel'],manifest['development_panel_sha256'])
 ck(panel['split']=='development' and len(panel['states'])==100 and len(panel['task_catalog'])==10 and set(Counter(x['task_id'] for x in panel['states']).values())=={10},'100 developer initial states, 10 per task')
 ck(len({(x['task_id'],x['trial_id']) for x in panel['states']})==100,'unique task/initial-state clusters')
 selected=[]
 for method in manifest['methods']:
  ident=method['identity'];ck(ident['training_seed']==41 and ident['visual_tokens']==128 and ident['training_complete'] and not ident['future_head_deployed'],'same completed seed41 checkpoint and deployed no future head')
  checkpoint=Path(method['checkpoint']);h=fh(checkpoint);ck(h==ident['checkpoint_sha256'],'actual selected checkpoint bytes '+ident['method_id'])
  receipt_raw=read(method['receipt'],prepared['watched_files'][str(P/method['receipt'])])
  ck(evidence[method['receipt']]==prepared['root_evidence_sha256'][method['receipt']],'deployment receipt raw bytes bound by frozen plan '+ident['method_id'])
  ck(receipt_raw==read(P/method['receipt']),'deployment receipt R/P byte equality '+ident['method_id'])
  ck(hashlib.sha256(canon(json.loads(receipt_raw))).hexdigest()==ident['deployment_receipt_sha256'],'deployment receipt canonical identity signature '+ident['method_id'])
  selected.append({'method_id':ident['method_id'],'path':str(checkpoint),'sha256':h,'deployment_receipt_raw_sha256':evidence[method['receipt']],'deployment_receipt_canonical_sha256':ident['deployment_receipt_sha256']})
 oldjob=next(x for x in pre['registered_jobs'] if x['job_id']=='3043709')
 ck(oldjob['method_ids']==['A128_seed23','B128_seed23'] and oldjob['stage_key']!=STAGE,'earlier seed23 shard not selected again')
 oldinv=js(oldjob['invocation'],oldjob['invocation_sha256']);oldmanifest=js(Path(oldinv['execution_manifest']),oldinv['execution_manifest_sha256'])
 ck(oldmanifest['development_panel_sha256']==manifest['development_panel_sha256'],'same 100 development states across seeds, not new independent states')
 ck(reserve['scheduler']['rows']['3043709']['status']=='COMPLETED','earlier seed23 shard remains complete')
 ackraw=ack['stdout'];ck(ack['returncode']==0 and ackraw=='3045322\n' and ack['stderr']=='','single exact original Slurm ACK')
 ck(fail['status']=='stopped_requires_root_reconciliation_no_retry' and fail['error']=='post-submit accounting incomplete' and fail['automatic_retry'] is False,'original accounting delay preserved')
 pending=rec['pending_before']
 ck(pending['known_job_id']==JID and pending['status']=='submitted_identifier_observed' and pending['automatic_retry'] is False and pending['authorization']==AR and pending['request_token']==TOKEN and pending['audit_relative']==AD,'exact original known pending')
 ck(job==rec['job']==commit['job'] and job['method_ids']==['A128_seed41','B128_seed41'] and job['stage_key']==STAGE,'one new registered stage identity')
 ck(job['downstream_gateway']['authorization']==AR and job['downstream_gateway']['request_token']==TOKEN,'job binds authority/token')
 ck(rec['new_submissions']==0 and rec['automatic_retry'] is False and rec['exact_reservation_consumed']==auth['root_reservation'],'no resubmit, exact dedicated reservation consumed')
 ck(commit['status']=='submitted_once_reconciled_after_accounting_delay' and commit['reservation_consumed'] is True and commit['automatic_retry'] is False,'one reconciled commit')
 rootref={'path':RECEIPT,'sha256':evidence[RECEIPT]}
 ck(commit['root_reconciliation']==rootref and obs['root_pending_reconciliation']==rootref and obs['observation']==rec['scheduler'],'transaction binds exact root receipt and raw scheduler')
 for key,filename in [('original_preflight','preflight.json'),('original_ACK','sbatch_result.json'),('original_failure','failed_transaction.json')]:
  ck(rec[key]=={'path':AD+'/'+filename,'sha256':evidence[AD+'/'+filename]},'exact '+key+' provenance')
 argv=ack['actual_sbatch_argv']
 ck(argv==pre['actual_sbatch_argv']==pending['actual_sbatch_argv']==job['downstream_gateway']['actual_sbatch_argv'],'submission argv one chain')
 for opt in ['--no-requeue','--exclude=gpu4020','--comment='+TOKEN,'--job-name=cti-formal-downstream','--gres=gpu:l40:1','--time=04:00:00','--chdir='+str(P)]:ck(opt in argv,'fixed sbatch option '+opt)
 wrap=shlex.split(argv[argv.index('--wrap')+1]);ck(wrap[:2]==['bash','-lc'] and len(wrap)==3,'exact wrapped command encoding')
 lines=wrap[2].splitlines();execargs=shlex.split(lines[-1])
 ck(execargs==['exec','srun','/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python','-B',str(P/prepared['wrapper']),'--invocation',str(P/invrel),'--invocation-sha256',evidence[invrel]],'actual wrapper argv and invocation checksum')
 ck('cd '+str(S) in lines and 'export PYTHONPATH='+str(S/'src')+' PYTHONDONTWRITEBYTECODE=1' in lines,'frozen source working environment')
 prejobs=pre['registered_jobs'];postjobs=prejobs+[job]
 for snapshot,claimed,label,jobs in [(reserve['scheduler'],reserve['capacity'],'reservation',prejobs),(pre['scheduler_observation'],pre['capacity'],'pre-submit',prejobs),(rec['scheduler'],rec['capacity'],'post-submit',postjobs)]:
  ck(parse_snapshot(snapshot,jobs,label)==claimed,'independent raw capacity '+label)
 ck(len(reserve['capacity']['occupied'])==len(pre['capacity']['occupied'])==7 and len(rec['capacity']['occupied'])==8,'one real free slot, 7 training plus one development')
 ck([jid for jid,q in rec['scheduler']['queue'].items() if q['comment']==TOKEN]==[JID],'only one exact active token')
 ck(rec['scheduler']['rows']['3039981']['status']=='COMPLETED','Goal128 seed23 freed slot is actually terminal')
 detail=rec['actual_scontrol_detail'];ck(detail['returncode']==0 and not detail['stderr'],'saved actual scontrol success')
 fields=dict(x.split('=',1) for x in detail['stdout'].split() if '=' in x)
 for key,value in {'JobId':JID,'JobName':'cti-formal-downstream','JobState':'RUNNING','Comment':TOKEN,'WorkDir':str(P),'TimeLimit':'04:00:00','Requeue':'0','Restarts':'0','ExcNodeList':'gpu4020','NodeList':'gpu4001','TresPerNode':'gres:gpu:l40:1'}.items():ck(fields.get(key)==value,'actual scheduler identity '+key)
 ck(fields['SubmitTime']=='2026-10-20T12:32:12','actual Slurm submit time differs appropriately from frozen prepared registration timestamp')
 for suffix,entry,pin,code in [
 ('reserve','.local/reserve_Long128seed41_0428.py','453d0c7f44e6d4d39b2ffbb27b7f9dfe12dc72501b3d781e6a2120169078df3b',0),
 ('submit','.local/dispatch_long128seed41_0428.py','dcd14ce0ddfe2825527e7dd180c6070325c90a2708d72adfaaf7bcc661bd6681',1),
 ('pending_reconciliation','.local/reconcile_long128s41_pending_0428.py','2b8f6fd53612ef1f0daa07c8a73e0e70a47c264bb148443ccc910efadef6d8ef',0)]:
  src=read(entry,pin).decode();logs=[json.loads(x) for x in read('results/formal_main_v2/control_transport/heartbeat_0428_long_'+suffix+'.jsonl').splitlines()]
  starts=[x for x in logs if x['event']=='control_start'];ends=[x for x in logs if x['event']=='control_end']
  ck(len(starts)==len(ends)==1 and starts[0]['entrypoint']==entry and starts[0]['entrypoint_sha256']==pin and ends[0]['returncode']==code and ends[0]['source173_and_entrypoint_unchanged'],'exact executed root source '+suffix)
  if suffix=='submit':
   ck(src.count('subprocess.run(')==2 and src.count("argv+['--submit','--root-reviewed-submit']")==1 and not any(isinstance(n,(ast.For,ast.While)) for n in ast.walk(ast.parse(src))),'one read-only preflight plus one submit, no retry loop')
  else:
   ck(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {'submit','cancel','sbatch'} for n in ast.walk(ast.parse(src))),'no scheduler mutation in root '+suffix)
   ck('with c.exclusive_lock' in src and 'c.atomic_json(' in src,'shared writer lock and CAS '+suffix)
   if suffix=='pending_reconciliation':ck('assert s==expected' in src,'executed exact expected state-delta assertion')
 inventory=js('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 ck(len(inventory['files'])==173 and inventory['source_sha256']==prepared['source_sha256'],'source inventory identity')
 for rel,pin in inventory['files'].items():ck(fh(R/rel)==pin and fh(S/rel)==pin,'173 frozen R/S identity '+rel)
 owner=js('results/formal_main_v2/autonomous_training/run_v1/owner.json')
 ck(owner==rec['controller_owner']==reserve['controller_owner']==initial['controller_owner'],'owner unchanged through reservation and reconciliation')
 ck(rec['scheduler']['rows']['3034538']['status']=='RUNNING' and rec['scheduler']['rows']['3034538']['gpus']==0 and rec['scheduler']['rows']['3034538']['node']==owner['hostname'],'actual controller CPU0')
 with Path(owner['lock']).open('rb') as lease:
  try:fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:held=True
  else:fcntl.flock(lease,fcntl.LOCK_UN);held=False
 ck(held,'controller lifetime lease held')
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
  rawstate=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(rawstate);ctl=state['autonomous_training_v1']
  ck(state['pending_submission'] is None,'known pending fully reconciled')
  ck([str(x['job_id']) for x in state['registered_jobs']]==[str(x['job_id']) for x in postjobs],'current registry exact previous plus one')
  volatile={'status','elapsed_seconds','exit_code','node','allocation'}
  for expected,current in zip(postjobs,state['registered_jobs']):ck({k:v for k,v in expected.items() if k not in volatile}=={k:v for k,v in current.items() if k not in volatile},'immutable registry '+str(current['job_id']))
  ck(len([x for x in state['registered_jobs'] if x.get('stage_key')==STAGE])==1,'stage registered exactly once')
  ck(ctl['downstream_reservations_consumed'][AUTH]=={'job_id':JID,'reservation':auth['root_reservation'],'request_token':TOKEN} and ctl['reserved_GPU_slots']==0 and ctl['reservation_root_record']==auth['root_reservation'],'only dedicated Long reservation consumed')
  ck(ctl['cuda_recovery_reservations_consumed']['0f8c1eab2e196c544bbf1302d440085abf052bc0bbc32a6dc3d9377bcdb0aec0']==consumed,'old Object reservation history preserved')
  ck(ctl['blocked_pairs']==initial['blocked_pairs'] and ctl['owner_id']==owner['owner_id'] and ctl['root_submission_hold'] is None,'unrelated failure blocks and owner unchanged')
  ck({'path':B+'/Long128seed41_reservation_activation.json','sha256':evidence[B+'/Long128seed41_reservation_activation.json']} in ctl['root_reservation_activation_history'],'new activation linked once in history')
  ck(state['formal_main_progress']['completed_final_trials']==0 and not state['formal_main_progress']['test_opened'] and not state['formal_main_progress']['global_release_created'],'final remains sealed')
  ck((R/'results/experiment_supervisor/state.json').read_bytes()==rawstate,'current state consistent under read lock')
  state_sha=hashlib.sha256(rawstate).hexdigest();fcntl.flock(lock,fcntl.LOCK_UN)
 return {'schema':'formal_main_v2','kind':'Long128_seed41_development_submission_independent_review','version':'independent-Long128s41-0428-v1','status':'passed','blockers':[],'job_id':JID,'stage_key':STAGE,'authorization':AR,'root_reconciliation':rootref,'checks_passed':len(checks),'checks':checks,'evidence_sha256':evidence,'observed_state_sha256':state_sha,'selected_checkpoint_hashes_independently_checked':selected,'planned_trials':200,'unique_initial_states':100,'new_trials_completed_by_this_review':0,'previous_seed23_job_preserved':'3043709','all_registered_GPU_before':7,'all_registered_GPU_after':8,'actual_submission_time_Asia_Shanghai':fields['SubmitTime'],'prepared_registration_utc_is_not_actual_submit_time':prepared['registered_utc'],'saved_scheduler_observation_utc':rec['utc'],'independent_new_scheduler_queries':0,'independent_new_GPU_jobs':0,'production_state_git_slurm_mutations':False,'audit_repair':'Attempt01 auditor confused canonical JSON identity with raw file SHA. Failure retained; attempt02 independently verifies both frozen-plan raw SHA and original canonical-signature semantics. No project code or scientific artifacts changed.','state_delta_verification':'Pinned successful reconciliation source asserts exact allowed delta under shared writer lock and CAS. Current immutable registry, dedicated consumption, historical Object reservation and failure blocks independently checked. No full before/after state snapshot recomputation claimed.','limitations':['Admission and submission reconciliation only, not 200-trial completion or success-rate acceptance.','Saved original sacct/squeue/scontrol independently reconstructed without additional live GPU polling.','The shared 100 development initial states are reused across seeds and do not count as new independent initial states.','The older prepared invocation timestamp remains frozen; actual execution submission time is taken from saved Slurm scontrol.'],'utc':datetime.now(timezone.utc).isoformat()}
try:report=audit()
except BaseException as exc:report={'schema':'formal_main_v2','kind':'Long128_seed41_development_submission_independent_review','status':'failed','blockers':[type(exc).__name__+': '+str(exc)],'checks_passed':len(checks),'checks':checks,'evidence_sha256':evidence,'traceback':traceback.format_exc(),'utc':datetime.now(timezone.utc).isoformat()}
report['audit_source']={'path':str(Path(__file__).relative_to(R)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
dest=OUT/'independent_review.json'
with dest.open('x') as f:json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'status':report['status'],'checks_passed':len(checks),'report':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'blockers':report['blockers']}))
if report['status']!='passed':sys.exit(1)
