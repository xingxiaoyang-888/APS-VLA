"""Independent read-only audit of Object64 job3044844 original-ACK reconciliation.
Writes only its own server audit directory. No production imports or scheduler commands.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,fcntl,hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
OUT=R/'.local/independent_object3044844_0333'
AUTH='6619bd4e9a8e75b76200bca401a861bc5c6c1180a54c37cf739da18f55ea019c'
AR={'path':'configs/experiments/formal_main_v2_object64_cuda_continuous_3044017_v1.json','sha256':AUTH}
AD='results/formal_main_v2/continuous_admissions/3044017/'+AUTH
RECEIPT='results/formal_main_v2/preflight/heartbeat_20261020T1133/Object3044844_pending_reconciliation.json'
PAIR='libero_object_k64_seed23';JID='3044844'
TOKEN='cti-object64-continuous-v1:'+AUTH
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

def audit():
 auth=js(AR['path'],AUTH)
 pre=js(AD+'/preflight.json','12acb51f399e47e8daaf37ffc15bc7cd2e56deea2e1e17b41472c9c0229bfca0')
 ack=js(AD+'/sbatch_result.json','fda1a64763b13df89255e56cbc3f2b29a860c3cd9f92e3bc3bc9c145e231cdd9')
 fail=js(AD+'/failed_transaction.json','8b6958884dd8bbdfef3aa9b338c49e620a1543968abf23e776a6062795fa5955')
 rec=js(RECEIPT,'1b9d5580870d2943dd0565081d53950e4e740f6e555def890f7386861d3e0455')
 ident=js(AD+'/submission_identity.json','3f9feacf0f47025b139359d6497ea60d06e88effcac8b754697bac2ffeafef2a')
 commit=js(AD+'/committed.json','f463dfa80d89f8288ef53758d47652ad62e24ac74398c6728c4aab0061aeef97')
 job=js('results/formal_main_v2/submissions/'+JID+'.json')
 ck(auth['pair_key']==PAIR and auth['status']=='approved_exact_once_500_to5000' and auth['reviewed_by']=='root','exact root authority')
 ck(auth['completed_before']=={'A':500,'B':500} and auth['cursor_before']=={'A':4000,'B':4000},'authorized initial update/cursor')
 ck(auth['historical_GPU_seconds']==5210 and auth['target_updates_per_arm']==5000 and auth['single_new_attempt'] and not auth['automatic_retry'],'fixed continuation target and retained cost')
 for key in ['root_review','independent_review','root_recovery_review','independent_recovery_review','canonical_failure_review','terminal_pull','controller_activation','normal_execution_authorization','node_exclusion']:
  ref=auth[key];js(ref['path'],ref['sha256'])
 for path,pin in auth['gateway_files'].items():read(path,pin)
 reconcile=read('.local/reconcile_object64_pending_0333.py','ab25dc6ea54d2aba0a2ba313d047e7c613b383f2e3c20b7e2df688c0649b3dc8').decode()
 ast_tree=ast.parse(reconcile)
 ck(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {'submit','run_once','sbatch','cancel'} for n in ast.walk(ast_tree)),'reconciliation has no submit/cancel call')
 ck("with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock')" in reconcile and 'c.atomic_json(statepath,state,before)' in reconcile,'writer lock and CAS in executed source')
 ck("assert state==expected and state['autonomous_training_v1']==old['autonomous_training_v1']" in reconcile,'executed exact allowed-state-delta assertion')
 ck("assert h(statepath)==before" in reconcile,'state unchanged before root write')
 for tail,entry,pin,code in [
  ('submit','.local/submit_object64_continuation_0333.py','ec96bdf5cb1fe9b9ff7db52266de92bfc4f098c69fc4e6c19ab66df8cb063b52',1),
  ('reconcile','.local/reconcile_object64_pending_0333.py','ab25dc6ea54d2aba0a2ba313d047e7c613b383f2e3c20b7e2df688c0649b3dc8',0)]:
  lines=[json.loads(x) for x in read('results/formal_main_v2/control_transport/heartbeat_0333_object64_'+tail+'.jsonl').splitlines()]
  ck(len(lines)==2 and lines[0]['entrypoint']==entry and lines[0]['entrypoint_sha256']==pin and lines[-1]['returncode']==code and lines[-1]['source173_and_entrypoint_unchanged'] is True,'exact transport execution '+tail)
  read(entry,pin)
 submit_source=read('.local/submit_object64_continuation_0333.py').decode()
 ck(submit_source.count('subprocess.run(')==1 and not any(isinstance(n,(ast.While,ast.For)) for n in ast.walk(ast.parse(submit_source))),'one submission invocation without retry loop')
 ck(ack['returncode']==0 and ack['stdout']=='3044844\n' and ack['stderr']=='','single unambiguous original ACK')
 ck(fail['status']=='stopped_no_automatic_retry' and fail['error']=='post-submit accounting incomplete','original accounting visibility failure retained')
 ck(rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0 and rec['automatic_retry'] is False,'reconciliation status has no new submission')
 pending=rec['pending_before']
 ck(pending['known_job_id']==JID and pending['status']=='submitted_identifier_observed' and pending['retry_permitted'] is False,'original known pending retained before reconciliation')
 ck(pending['authorization']==AR and pending['audit_relative']==AD and pending['request_token']==TOKEN,'pending authority/token exact')
 ck(pre['authorization']==AR and pre['pair_key']==PAIR and pre['historical_GPU_seconds']==5210 and pre['controller_block_cleared'] is False,'preflight identity and failure cost')
 for key,f in [('original_preflight','preflight.json'),('original_ACK','sbatch_result.json'),('original_failure','failed_transaction.json')]:
  ck(rec[key]['path']==AD+'/'+f and rec[key]['sha256']==evidence[AD+'/'+f],'reconciliation binds '+key)
 ck(job==rec['job']==commit['job'],'registered submission/receipt/commit same job')
 ck(job['job_id']==JID and job['suite']=='libero_object' and job['visual_tokens']==64 and job['training_seed']==23 and job['segment_end']==5000 and job['gpus']==1,'registered exact matrix cell')
 ck(commit['status']=='submitted_once_reconciled_after_accounting_delay' and not commit['automatic_retry'] and not commit['controller_admission_changed'],'commit exact once, no controller exception clearing')
 ck(commit['root_reconciliation']==ident['root_pending_reconciliation']=={'path':RECEIPT,'sha256':evidence[RECEIPT]},'transaction binds root reconciliation')
 ck(ident['observation']==rec['scheduler'] and ident['actual_scontrol_detail']==rec['actual_scontrol_detail'],'transaction retains exact scheduler and scontrol')
 invrel=pre['invocation_relative'];invraw=read(invrel,'f494c0f2377d59a59fa1ed2b6ea061c20dc4e63ebb81e834ef5603d02cde0446')
 ck(invraw==read(P/invrel),'R and P invocation exact bytes')
 inv=json.loads(invraw)
 ck(inv==pre['invocation'] and pre['invocation_sha256']==pending['invocation_sha256']==job['invocation_sha256']==evidence[invrel],'invocation SHA chain')
 oldinv=js('results/formal_main_v2/invocations/libero_object_train_k64_seed23_attempt02.json','312d66e1932e92111ea6d324709454f6c2e987ebf9a59e7f9cb6933dcf645895')
 expected=copy.deepcopy(oldinv);expected['registered_utc']=inv['registered_utc'];expected['segment_end']=5000
 for flag,old,new in [('--stop-after-updates','500','5000'),('--max-wall-seconds','12600','169200')]:
  ck(expected['argv'].count(flag)==1 and expected['argv'][expected['argv'].index(flag)+1]==old,'original execution option '+flag)
  expected['argv'][expected['argv'].index(flag)+1]=new
 expected['continuous_admission']=inv['continuous_admission']
 ck(inv==expected and inv['argv'][-1]=='--resume' and inv['entrypoint']=='scripts/run_formal_future.py','only approved execution target/wall/metadata changed')
 ca=inv['continuous_admission']
 ck(ca['completed_before']=={'A':500,'B':500} and ca['sample_cursor_before']=={'A':4000,'B':4000} and ca['validation_updates']==list(range(0,5001,500)) and ca['checkpoint_every_updates']==50,'full schedule, 11 validation nodes and resume start metadata')
 ck(ca['resume_checks_before']==pre['server_preflight']['server_resume_checks'],'initial exact server resume hashes inherited')
 ck(ca['prior_job_ids']==['3028468','3044017'] and ca['historical_GPU_seconds']==5210,'failure and original recovery retained')
 ck([x['sha256'] for x in ca['resume_checks_before']]==['53dbaf269aba7214e42cd1284f88af1ede1f9b0cad2990638440a797cd323624','80bce26076d69c29c8b0888040a6f3326b71f293575842bac04af756daba4df6'],'exact prior A/B resume bytes bound')
 argv=ack['actual_sbatch_argv']
 ck(argv==pre['actual_sbatch_argv']==pending['actual_sbatch_argv']==job['startup_recovery']['actual_sbatch_argv']==job['continuous_admission']['actual_sbatch_argv'],'sbatch argv single-chain consistency')
 wrapper='scripts/server/formal_asset_main.slurm';wpin='9d54e0486a078a8358c8443bb92db8c8096d9ac3988eff693fa69b250d97c36a'
 ck(argv[-1]==str(P/wrapper),'original Object metadata wrapper invoked')
 for base in (R,P):read(base/wrapper,wpin)
 expected_export='--export=ALL,SOURCE_ROOT='+str(S)+',INVOCATION='+str(P/invrel)+',INVOCATION_SHA256='+evidence[invrel]
 ck(expected_export in argv and '--comment='+TOKEN in argv and '--time=48:00:00' in argv and '--no-requeue' in argv and '--exclude=gpu4020' in argv and '--chdir='+str(P) in argv,'exact runtime export, time and token')
 for rel,pin in inv['runtime_compatibility']['files'].items():
  for base in (R,P):read(base/rel,pin)
 inventory=js('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 ck(len(inventory['files'])==173 and inventory['source_sha256']==inv['source_sha256']==auth['source_sha256'],'scientific source inventory identity')
 for rel,pin in inventory['files'].items():
  ck(fh(R/rel)==pin and fh(S/rel)==pin,'R/S frozen scientific byte identity '+rel)
 cfg=js('configs/experiments/formal_main_v2/libero_object_k64_seed23.json')
 ck(cfg['training']['updates']==5000 and cfg['training']['effective_batch']==8 and cfg['tokens_per_camera']==32 and cfg['future']['horizon']==8 and cfg['future']['weight_B']==0.1 and cfg['selection']['updates']==list(range(0,5001,500)),'unchanged registered scientific settings')
 prejobs=pre['full_registered_jobs'];postjobs=prejobs+[job]
 beforecap=parse_snapshot(pre['scheduler_observation'],prejobs,'before')
 aftercap=parse_snapshot(rec['scheduler'],postjobs,'after')
 ck(beforecap==pre['capacity'] and aftercap==rec['capacity'],'independently reconstructed capacities')
 ck(len(beforecap['occupied'])==7 and len(aftercap['occupied'])==8 and pre['reserved_slots_preserved']==0,'available unreserved slot before and max8 after')
 ck(PAIR not in beforecap['active_pairs'] and aftercap['active_pairs'][PAIR]==[JID],'no duplicate active pair')
 ck([jid for jid,q in rec['scheduler']['queue'].items() if q['comment']==TOKEN]==[JID],'unique exact token in saved full registered queue')
 ck(rec['scheduler']['rows']['3038735']['status']=='COMPLETED','freed Goal256 seed41 slot was truly terminal')
 ck(rec['scheduler']['rows']['3028468']['status']=='FAILED' and rec['scheduler']['rows']['3028468']['elapsed_seconds']==69 and rec['scheduler']['rows']['3044017']['elapsed_seconds']==5141,'historical failure and recovery accounting retained')
 detail=rec['actual_scontrol_detail']
 ck(detail['returncode']==0 and not detail['stderr'] and detail['argv']==['scontrol','show','job','-o',JID],'actual saved scontrol success')
 fields=dict(x.split('=',1) for x in detail['stdout'].split() if '=' in x)
 for key,value in {'JobId':JID,'JobName':'cti-formal','JobState':'RUNNING','Comment':TOKEN,'Command':str(P/wrapper),'WorkDir':str(P),'TimeLimit':'2-00:00:00','Requeue':'0','Restarts':'0','ExcNodeList':'gpu4020','NodeList':'gpu4017','StdOut':str(P/'results/slurm/cti-formal_3044844.out'),'StdErr':str(P/'results/slurm/cti-formal_3044844.err')}.items():
  ck(fields.get(key)==value,'actual scheduler field '+key)
 ck(fields['TresPerNode']=='gres:gpu:l40:1','actual one-GPU request')
 ck(pre['controller_owner']==rec['controller_owner'],'controller owner unchanged through submission')
 owner=rec['controller_owner'];liveowner=js(owner['path'],owner['sha256'])
 ck(liveowner==owner['owner'] and liveowner['owner_id']=='6b3beba5cdeb41df9d749b0b2054d485' and liveowner['coordinator_job_id']=='3034538','current owner identity')
 ck(rec['scheduler']['rows']['3034538']['status']=='RUNNING' and rec['scheduler']['rows']['3034538']['gpus']==0 and rec['scheduler']['rows']['3034538']['node']==liveowner['hostname'],'saved controller actual CPU0 and hostname')
 with Path(liveowner['lock']).open('rb') as lease:
  try:fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:held=True
  else:fcntl.flock(lease,fcntl.LOCK_UN);held=False
 ck(held,'controller lifecycle lease still held')
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
  state_raw=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(state_raw)
  ck(state['pending_submission'] is None,'pending cleared only after exact corroboration')
  ids=[str(j['job_id']) for j in state['registered_jobs']]
  ck(ids==[str(j['job_id']) for j in postjobs] and len(ids)==len(set(ids)),'current registry exact old-plus-one IDs')
  volatile={'status','elapsed_seconds','exit_code','node','allocation'}
  for expected,current in zip(postjobs,state['registered_jobs']):
   ck({k:v for k,v in current.items() if k not in volatile}=={k:v for k,v in expected.items() if k not in volatile},'immutable registry identity '+str(current['job_id']))
  matching=[j for j in state['registered_jobs'] if j.get('stage_key')=='libero_object_train_k64_seed23']
  ck([j['job_id'] for j in matching]==['3028468','3044017',JID],'exact three historical/continuation pair jobs')
  block=state['autonomous_training_v1']['blocked_pairs'][PAIR]
  ck(block=={'automatic_retry':False,'decision':'blocked','failed_job_ids':['3028468'],'history_sha256':'ff9b325f730fd4acd417d45938e4c8b91397302f872caa255d02eea00f46dcb2','reason':'failed_unknown_or_active_history_requires_root_repair'},'original blocked history still exact')
  ck(state['autonomous_training_v1']['owner_id']==liveowner['owner_id'] and state['autonomous_training_v1']['reserved_GPU_slots']==0 and state['autonomous_training_v1']['root_submission_hold'] is None,'controller admission and reservation preserved')
  tracking=state['formal_main_progress']['parallel_execution']['pair_tracking'][PAIR]
  ck(tracking['active_job_id']==JID and tracking['segment_target']==5000 and tracking['continuous_admission']==AR,'current active pair tracking exact')
  ck(state['formal_main_progress']['completed_final_trials']==0 and state['formal_main_progress']['test_opened'] is False and state['formal_main_progress']['global_release_created'] is False,'final remains sealed')
  ck((R/'results/experiment_supervisor/state.json').read_bytes()==state_raw,'read-only consistent state under shared writer lock')
  state_sha=hashlib.sha256(state_raw).hexdigest()
  fcntl.flock(lock,fcntl.LOCK_UN)
 return {'schema':'formal_main_v2','kind':'object64_continuous_pending_reconciliation_independent_review','version':'independent-object3044844-0333-v1','status':'passed','blockers':[],'job_id':JID,'pair_key':PAIR,'root_reconciliation':{'path':RECEIPT,'sha256':evidence[RECEIPT]},'authorization':AR,'checks_passed':len(checks),'checks':checks,'evidence_sha256':evidence,'observed_state_sha256':state_sha,'saved_scheduler_observation_utc':rec['utc'],'independently_reconstructed_GPU_jobs_before':7,'independently_reconstructed_GPU_jobs_after':8,'one_original_submission_ACK':JID,'new_slurm_calls_by_independent_auditor':0,'new_GPU_jobs_by_independent_auditor':0,'production_writes_by_independent_auditor':0,'current_controller_lease_held':True,'scientific_source_R_and_S_173_rehashed':True,'state_delta_verification':'Pinned executed reconciliation source restricts delta to one registered job, pending clear, active pair tracking and cost. Exact source asserts full-state equality to this expected delta under original writer lock and CAS; successful transport execution is retained. Current immutable registry and block checked independently. No full before/after state snapshot recomputation claimed.','limitations':['This is submission/pending reconciliation evidence, not optimizer/RNG GPU restoration or completed training acceptance.','Live resume files are allowed to advance after submission; exact initial resume SHA checks are bound through original audited preflight, not claimed as current immutable checkpoint files.','No new scheduler polling; saved original raw sacct/squeue/scontrol independently reconstructed.','Absence of duplicate submissions is concluded from the sole reviewed submit call, original ACK, immutable transaction, and full registered queue/registry; no unrelated cluster jobs inspected.'],'notes':['Legacy object64seed23_continuous_ready status may remain as prior readiness metadata until root heartbeat summary updates; active registry/pair tracking identify3044844.'],'utc':datetime.now(timezone.utc).isoformat()}
try:report=audit()
except BaseException as exc:
 report={'schema':'formal_main_v2','kind':'object64_continuous_pending_reconciliation_independent_review','status':'failed','blockers':[type(exc).__name__+': '+str(exc)],'checks_passed':len(checks),'checks':checks,'evidence_sha256':evidence,'traceback':traceback.format_exc(),'utc':datetime.now(timezone.utc).isoformat()}
report['audit_source']={'path':str(Path(__file__).relative_to(R)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
dest=OUT/'independent_review.json'
with dest.open('x') as f:json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'status':report['status'],'checks_passed':len(checks),'report':str(dest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'blockers':report['blockers']}))
if report['status']!='passed':sys.exit(1)
