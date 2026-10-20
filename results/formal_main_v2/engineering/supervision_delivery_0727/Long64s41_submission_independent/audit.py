"""Independent read-only admission and reconciliation audit for Long64 seed41 registered development shard, 0727 UTC supervision.
Uses preserved scheduler observations. Writes only this server audit directory.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,copy,fcntl,hashlib,json,shlex,sys,traceback
from collections import Counter
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
OUT=R/'.local/independent_long64s41_submission_0727'
B='results/formal_main_v2/preflight/heartbeat_20261020T1527'
RUNS=[{"budget":64,"seed":41,"auth":"a45db8af1bee86142cf80df416c5bf27b734f493448eb5ee429c92947b48c244","job_id":"3047443","stage":"libero_10_development_b426228fe9d2fd0a","prior_job_id":"3047163","prior_auth":"775b318f5534c67f41c828aed5592d3bc1c0403e4989cdcfc95aaa7d3b207573","before_slots":5,"reservation_slots":5,"submit_time":"2026-10-20T15:32:14","reserve_receipt_path":"results/formal_main_v2/preflight/heartbeat_20261020T1527/Long64seed41_reservation_activation.json","reserve_receipt_sha":"860a141313ded20f5d5c54b899dfa379e4e47f207d55d2975d421b0b1c07ffa8","reconcile_receipt_sha":"545f30007044f407dd19bd25a9c9732ecc064ec0cf1c6195db55495c6713baf4","failure_type":"post-submit accounting incomplete","root_steps":{"reserve":{"entry":".local/reserve_Long64seed41_0727.py","sha256":"26d99fd3d56d034f2ade7debc644b1798a5207dca22bedd8d121c0b8f324645a","returncode":0,"log":"results/formal_main_v2/control_transport/heartbeat_0727_reserve_long64s41.jsonl","log_sha":"17020a32b78ffcef7dde3ca162256a169f847f99fd5edda3832532b61b4c83a5"},"submit":{"entry":".local/dispatch_long64seed41_0727.py","sha256":"cca04177564ad07e24bcbf99cb7829f0367769f0cbd748aea6e6a345e6fbad2b","returncode":1,"log":"results/formal_main_v2/control_transport/heartbeat_0727_dispatch_long64s41.jsonl","log_sha":"4d3ac35c4fd3769457fbfcee38334eb68cea211c63e430606e30ca915e79e7b6"},"pending_reconciliation":{"entry":".local/reconcile_long64s41_pending_0727.py","sha256":"f7a5a253f8ecbace3a05cf72b456d3832b5e1f90f1575d11853a1e74b48da2d2","returncode":0,"log":"results/formal_main_v2/control_transport/heartbeat_0727_reconcile_long64s41_pending.jsonl","log_sha":"a0fe8989010ae21c4c9a69310f6d19f4161a9b670c5214eaeeb529cfdc0bf4f8"}}}]
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

def audit_one(run,initial):
 seed=run['seed'];budget=run['budget'];AUTH=run['auth'];JID=run['job_id'];STAGE=run['stage']
 D='results/formal_main_v2/execution/long_remaining16_action_v1_1827/k'+str(budget)+'_seed'+str(seed)
 AR={'path':D+'/submission_authorization.json','sha256':AUTH}
 AD='results/formal_main_v2/downstream_gateway/'+AUTH
 TOKEN='cti-downstream-gateway-v1:'+AUTH
 RECEIPT=B+'/Long'+JID+'_pending_reconciliation.json'
 auth=js(AR['path'],AUTH)
 reservepath=run['reserve_receipt_path']
 reserve=js(reservepath,run['reserve_receipt_sha'])
 rec=js(RECEIPT,run['reconcile_receipt_sha'])
 pre=proof(rec['original_preflight']);ack=proof(rec['original_ACK']);fail=proof(rec['original_failure'])
 obs=js(AD+'/submitted_job_observation.json');commit=js(AD+'/committed.json')
 job=js('results/formal_main_v2/submissions/'+JID+'.json')
 ck(auth['status']=='approved_for_exactly_one_registered_downstream_submission' and auth['maximum_attempts']==1 and not auth['automatic_retry'] and not auth['final_release_authorized_by_gateway'],'exact single-stage root authority')
 for key in ['independent_review','gap_review','controller','controller_activation','planner']:read(auth[key]['path'],auth[key]['sha256'])
 for path,pin in auth['gateway_files'].items():read(path,pin)
 plan=proof(auth['plan']);science=proof(auth['scientific_plan']);prepared=proof(auth['prepared_invocation']);ready=proof(auth['runtime_readiness']);reservation=proof(auth['root_reservation'])
 intent=copy.deepcopy(auth);intent.pop('root_reservation')
 ck(reservation['authorization_intent_sha256']==hashlib.sha256(canon(intent)).hexdigest() and reservation['authorization_path']==AR['path'],'dedicated reservation exact authority intent')
 ck(reservation['reserved_slots']==1 and reservation['capacity_limit_all_GPU_modes']==8 and reservation['old_CUDA_reservation_must_not_be_reused'] is True and reservation['stage_key']==STAGE,'dedicated one-GPU development reservation')
 ck(reserve['authorization']==AR and reserve['reservation']==auth['root_reservation'] and reserve['new_GPU_submissions']==[] and reserve['new_trials']==0 and reserve['planned_trials']==200,'root activation only reserved, not submitted')
 consumed=reserve['prior_exact_downstream_reservation_consumed']
 ck(consumed['job_id']==run['prior_job_id'] and consumed['request_token']=='cti-downstream-gateway-v1:'+run['prior_auth'] and consumed['reservation']!=auth['root_reservation'],'prior consumed reservation not reused')
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
 ck(json.loads(raw)==prepared and prepared['method_ids']==['A'+str(budget)+'_seed'+str(seed),'B'+str(budget)+'_seed'+str(seed)] and prepared['stage']=='development' and prepared['suite']=='libero_10' and prepared['resume'] is False and prepared['prior_job_ids']==[],'fresh exact Long matched budget and seed A/B development')
 ck(pre['invocation_relative']==invrel and pre['invocation_sha256']==evidence[invrel] and pre['plan']==auth['plan'] and pre['prepared_invocation']==auth['prepared_invocation'],'preflight prepared identity')
 ck(pre['runtime_preflight']['missing_publications']==[] and pre['runtime_preflight']['output_exists'] is False,'pre-submission actual publication and fresh output')
 for rel,pin in prepared['support_files'].items():
  read(rel,pin);read(P/rel,pin)
 for rel,pin in ready['runtime_publication_files'].items():read(rel,pin);read(P/rel,pin)
 invpath=Path(prepared['execution_manifest']);manifest_rel=str(invpath.relative_to(P));manifest=js(manifest_rel,prepared['execution_manifest_sha256'])
 ck(read(P/manifest_rel)==read(manifest_rel),'execution manifest R/P exact')
 ck(manifest['split']=='development' and manifest['suite']=='libero_10' and manifest['environment']=={'environment_seed':0,'runtime_seed':17,'wait_steps':10,'action_chunk':8,'max_steps':520},'fixed Long development environment')
 ck([m['identity']['method_id'] for m in manifest['methods']]==['A'+str(budget)+'_seed'+str(seed),'B'+str(budget)+'_seed'+str(seed)],'only registered matched two methods')
 panel=js(manifest['development_panel'],manifest['development_panel_sha256'])
 ck(panel['split']=='development' and len(panel['states'])==100 and len(panel['task_catalog'])==10 and set(Counter(x['task_id'] for x in panel['states']).values())=={10},'100 developer initial states, 10 per task')
 ck(len({(x['task_id'],x['trial_id']) for x in panel['states']})==100,'unique task/initial-state clusters')
 selected=[]
 for method in manifest['methods']:
  ident=method['identity'];ck(ident['training_seed']==seed and ident['visual_tokens']==budget and ident['training_complete'] and not ident['future_head_deployed'],'same completed matched-seed checkpoint and deployed no future head')
  checkpoint=Path(method['checkpoint']);h=fh(checkpoint);ck(h==ident['checkpoint_sha256'],'actual selected checkpoint bytes '+ident['method_id'])
  receipt_raw=read(method['receipt'],prepared['watched_files'][str(P/method['receipt'])])
  ck(evidence[method['receipt']]==prepared['root_evidence_sha256'][method['receipt']],'deployment receipt raw bytes bound by frozen plan '+ident['method_id'])
  ck(receipt_raw==read(P/method['receipt']),'deployment receipt R/P byte equality '+ident['method_id'])
  ck(hashlib.sha256(canon(json.loads(receipt_raw))).hexdigest()==ident['deployment_receipt_sha256'],'deployment receipt canonical identity signature '+ident['method_id'])
  selected.append({'method_id':ident['method_id'],'path':str(checkpoint),'sha256':h,'deployment_receipt_raw_sha256':evidence[method['receipt']],'deployment_receipt_canonical_sha256':ident['deployment_receipt_sha256']})

 for oid,omethods in [('3043709',['A128_seed23','B128_seed23']),('3045322',['A128_seed41','B128_seed41']),('3047152',['A256_seed41','B256_seed41']),('3047156',['A64_seed17','B64_seed17']),('3047163',['A64_seed23','B64_seed23'])]:
  oldjob=next(x for x in pre['registered_jobs'] if x['job_id']==oid)
  ck(oldjob['method_ids']==omethods and oldjob['stage_key']!=STAGE,'earlier registered Long shard not repeated '+oid)
  oldinv=js(oldjob['invocation'],oldjob['invocation_sha256']);oldmanifest=js(Path(oldinv['execution_manifest']),oldinv['execution_manifest_sha256'])
  ck(oldmanifest['development_panel_sha256']==manifest['development_panel_sha256'],'same development clusters across seeds/budgets '+oid)
  ck(reserve['scheduler']['rows'][oid]['status']=='COMPLETED' and reserve['scheduler']['rows'][oid]['exit_code']=='0:0','old completed shard preserved '+oid)
 ackraw=ack['stdout'];ck(ack['returncode']==0 and ackraw==JID+'\n' and ack['stderr']=='','single exact original Slurm ACK')
 ck(fail['status']=='stopped_requires_root_reconciliation_no_retry' and fail['error']==run['failure_type'] and fail['automatic_retry'] is False,'exact original submission failure preserved without relabeling')
 pending=rec['pending_before']
 ck(pending['known_job_id']==JID and pending['status']=='submitted_identifier_observed' and pending['automatic_retry'] is False and pending['authorization']==AR and pending['request_token']==TOKEN and pending['audit_relative']==AD,'exact original known pending')
 ck(job==rec['job']==commit['job'] and job['method_ids']==['A'+str(budget)+'_seed'+str(seed),'B'+str(budget)+'_seed'+str(seed)] and job['stage_key']==STAGE,'one new registered stage identity')
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
 ck(len(reserve['capacity']['occupied'])==run['reservation_slots'] and len(pre['capacity']['occupied'])==run['before_slots'] and len(rec['capacity']['occupied'])==run['before_slots']+1,'one actual slot consumed without exceeding eight')
 reservation_to_pre_lost=set(reserve['capacity']['occupied'])-set(pre['capacity']['occupied'])
 ck(not(set(pre['capacity']['occupied'])-set(reserve['capacity']['occupied'])),'no unrelated new GPU between reservation and submit')
 for oldid in reservation_to_pre_lost:
  oldrow=pre['scheduler_observation']['rows'][oldid]
  ck(oldrow['status']=='COMPLETED' and oldrow['exit_code']=='0:0','reservation to submit decrease explained by successful completion '+oldid)
 ck([jid for jid,q in rec['scheduler']['queue'].items() if q['comment']==TOKEN]==[JID],'only one exact active token')
 ck(rec['scheduler']['rows']['3042627']['status']=='COMPLETED' and rec['scheduler']['rows']['3046779']['status']=='COMPLETED','freed Object256 seed23 training and Long256 seed17 development jobs actually terminal')
 detail=rec['actual_scontrol_detail'];ck(detail['returncode']==0 and not detail['stderr'],'saved actual scontrol success')
 fields=dict(x.split('=',1) for x in detail['stdout'].split() if '=' in x)
 for key,value in {'JobId':JID,'JobName':'cti-formal-downstream','JobState':'RUNNING','Comment':TOKEN,'WorkDir':str(P),'TimeLimit':'04:00:00','Requeue':'0','Restarts':'0','ExcNodeList':'gpu4020','NodeList':rec['scheduler']['rows'][JID]['node'],'TresPerNode':'gres:gpu:l40:1'}.items():ck(fields.get(key)==value,'actual scheduler identity '+key)
 ck(fields['SubmitTime']==run['submit_time'],'actual Slurm submit time bound separately from frozen prepared registration timestamp')

 for suffix in ['reserve','submit','pending_reconciliation']:
  step=run['root_steps'][suffix];entry=step['entry'];pin=step['sha256'];code=step['returncode']
  src=read(entry,pin).decode();logs=[json.loads(x) for x in read(step['log'],step['log_sha']).splitlines()]
  starts=[x for x in logs if x['event']=='control_start'];ends=[x for x in logs if x['event']=='control_end']
  ck(len(starts)==len(ends)==1 and starts[0]['entrypoint']==entry and starts[0]['entrypoint_sha256']==pin and ends[0]['returncode']==code and ends[0]['source173_and_entrypoint_unchanged'],'exact executed root source '+str(seed)+' '+suffix)
  if suffix=='submit':
   ck(src.count('subprocess.run(')==2 and src.count("argv+['--submit','--root-reviewed-submit']")==1 and not any(isinstance(n,(ast.For,ast.While)) for n in ast.walk(ast.parse(src))),'one preflight and one submit without retry loop '+str(seed))
  else:
   ck(not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {'submit','cancel','sbatch'} for n in ast.walk(ast.parse(src))),'no scheduler mutation in root '+str(seed)+' '+suffix)
   ck('with c.exclusive_lock' in src and 'c.atomic_json(' in src,'shared writer lock and CAS '+str(seed)+' '+suffix)
   if suffix=='pending_reconciliation':
    ck('assert s==expected' in src,'executed exact state-delta assertion '+str(seed))
    ck("caps=g.reconcile_submission(c,jobs,snapshot,job,token,auth['controller_job_id'],corroboration)" in src,'unchanged gateway full reconciliation invoked '+str(seed))
 if 'diagnostic' in run:
  dr=run['diagnostic'];diag=proof(dr['receipt'])
  ck(rec['pending_name_diagnostic']==dr['receipt'] and rec['original_failure_type']==fail['error'] and rec['all_current_names_revalidated_by_unchanged_gateway'] is True,'name-difference recovery precisely bound to diagnostic')
  ck(diag['original_ACK']==rec['original_ACK'] and diag['original_failure']==rec['original_failure'] and diag['state_unchanged'] is True and diag['new_submissions']==0,'diagnostic retained original ACK/failure without mutation')
  diagcap=parse_snapshot(diag['observation'],postjobs,'name-difference diagnosis')
  ck(diag['name_mismatches']==[] and diagcap['occupied']==rec['capacity']['occupied'],'independent complete diagnostic registry names and capacity')
  dd=diag['scontrol'];df=dict(x.split('=',1) for x in dd['stdout'].split() if '=' in x)
  ck(dd['returncode']==0 and not dd['stderr'] and df['JobId']==JID and df['JobName']==job['name'] and df['Comment']==TOKEN and df['WorkDir']==str(P),'saved diagnostic exact job identity corroboration')
  dsrc=read(dr['entry'],dr['entry_sha']).decode();dlogs=[json.loads(x) for x in read(dr['log'],dr['log_sha']).splitlines()]
  ds=[x for x in dlogs if x['event']=='control_start'];de=[x for x in dlogs if x['event']=='control_end']
  ck(len(ds)==len(de)==1 and ds[0]['entrypoint']==dr['entry'] and ds[0]['entrypoint_sha256']==dr['entry_sha'] and de[0]['returncode']==0 and de[0]['source173_and_entrypoint_unchanged'],'successful exact diagnostic source')
  ck('assert h(sp)==before' in dsrc and 'c.atomic_json(' not in dsrc and not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {'submit','cancel','sbatch'} for n in ast.walk(ast.parse(dsrc))),'diagnostic read-only state and Slurm inspection')
 ck(rec['controller_owner']==reserve['controller_owner']==initial['controller_owner'],'owner stable in reservation/reconciliation '+str(seed))
 for snap,label,jobs in [(reserve['scheduler'],'reservation',prejobs),(pre['scheduler_observation'],'preflight',prejobs),(rec['scheduler'],'reconciled',postjobs)]:
  sec=sum(snap['rows'][str(j['job_id'])]['elapsed_seconds']*snap['rows'][str(j['job_id'])]['gpus'] for j in jobs if j.get('experiment')=='formal_main_v2')
  if label=='reservation':ck(sec==reserve['allocated_GPU_seconds'] and sec/3600==reserve['allocated_GPU_hours'],'all registered allocation costs independently summed '+str(seed))
 ck(rec['final_release_authorized'] is False and not reserve['final_release'],'submission grants no final release '+str(seed))
 return dict(seed=seed,budget=budget,job=job,authorization=AR,reservation=auth['root_reservation'],reserve_receipt={'path':reservepath,'sha256':evidence[reservepath]},root_reconciliation=rootref,prior_consumed=consumed,prejobs=prejobs,postjobs=postjobs,pre_capacity=pre['capacity'],post_capacity=rec['capacity'],controller_owner=rec['controller_owner'],scheduler=rec['scheduler'],pre_scheduler=pre['scheduler_observation'],selected=selected,failure_type=fail['error'],submit_time=fields['SubmitTime'],prepared_utc=prepared['registered_utc'],saved_utc=rec['utc'],source_sha256=prepared['source_sha256'],panel_sha256=manifest['development_panel_sha256'])
def audit():
 for path,pin in [('src/cti_vla/evaluation/teacher_diagnostics.py','0d27ee32f1ef8b1a409758416fd3177dfeb1624a2f6f9dd5b9955b53ab06bdfd'),('src/cti_vla/evaluation/formal_runtime.py','4029b0ddd1b6059f9f3586cd21aadd76fd15b516f79b201313a0291a2d64a8f8'),('scripts/formal_execution_manifests.py','614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89')]:read(path,pin)
 initial=js(B+'/initial_observation.json','8d3b24312f445cd867f3657a5e492118af29d8244520b8c02ec5f962c3e52d22')
 rows=[audit_one(run,initial) for run in RUNS]
 first,last=rows[0],rows[-1]
 volatile={'status','elapsed_seconds','exit_code','node','allocation'}
 def imm(j):return {k:v for k,v in j.items() if k not in volatile}
 for previous,current in zip(rows,rows[1:]):
  ck([imm(j) for j in previous['postjobs']]==[imm(j) for j in current['prejobs']],'next preflight immutable registry exactly previous committed registry')
  ck(current['prior_consumed']==dict(job_id=previous['job']['job_id'],reservation=previous['reservation'],request_token='cti-downstream-gateway-v1:'+previous['authorization']['sha256']),'next reservation binds actual prior committed ID and receipt')
  disappeared=set(previous['post_capacity']['occupied'])-set(current['pre_capacity']['occupied'])
  gained=set(current['pre_capacity']['occupied'])-set(previous['post_capacity']['occupied'])
  ck(not gained,'no unrelated active-job additions between serialized control transactions')
  for jid in disappeared:
   obs=current['pre_scheduler']['rows'][jid]
   ck(obs['status']=='COMPLETED' and obs['exit_code']=='0:0','additional free slot from actual successful completion '+jid)
 ck(first['prior_consumed']['reservation']==initial['reservation_root_record'],'first reservation follows actual previously consumed reservation')
 ck(all(x['panel_sha256']=='46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268' for x in rows),'all shards share fixed 100 initial-state clusters')
 ck(parse_snapshot(initial['observation'],first['prejobs'],'initial')==initial['capacity'],'independent initial raw snapshot')
 ck(len(initial['capacity']['occupied'])==5,'initial observation has five occupied GPU slots')
 initial_lost=set(initial['capacity']['occupied'])-set(first['pre_capacity']['occupied'])
 ck(not(set(first['pre_capacity']['occupied'])-set(initial['capacity']['occupied'])),'no unregistered occupancy increase before first submission')
 for jid in initial_lost:
  obs=first['pre_scheduler']['rows'][jid];ck(obs['status']=='COMPLETED' and obs['exit_code']=='0:0','initial slot decrease solely successful completion '+jid)
 ck(all(len(x['post_capacity']['occupied'])==len(x['pre_capacity']['occupied'])+1<=8 for x in rows),'each admission consumes one real slot within eight')
 ck(len({x['job']['job_id'] for x in rows})==len(rows) and len({x['job']['stage_key'] for x in rows})==len(rows),'all new job and stage identities distinct')
 final_snapshot=last['scheduler']
 for jid in initial['capacity']['occupied']:
  obs=final_snapshot['rows'][jid]
  ck(obs['status'] in {'RUNNING','PENDING','CONFIGURING','COMPLETING','SUSPENDED','COMPLETED'} and (obs['status']!='COMPLETED' or obs['exit_code']=='0:0'),'healthy initial GPU job not cancelled or failed '+jid)
 inventory=js('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 ck(len(inventory['files'])==173 and all(inventory['source_sha256']==x['source_sha256'] for x in rows),'173-file scientific source inventory')
 for rel,pin in inventory['files'].items():ck(fh(R/rel)==pin and fh(S/rel)==pin,'frozen R/S identity '+rel)
 owner=js('results/formal_main_v2/autonomous_training/run_v1/owner.json')
 ck(owner==initial['controller_owner']==first['controller_owner']==last['controller_owner'],'controller owner unchanged across the admission')
 for row in rows:
  c=row['scheduler']['rows']['3034538'];ck(c['status']=='RUNNING' and c['gpus']==0 and c['node']==owner['hostname'],'preserved actual CPU0 controller '+str(row['seed']))
 with Path(owner['lock']).open('rb') as lease:
  try:fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:held=True
  else:fcntl.flock(lease,fcntl.LOCK_UN);held=False
 ck(held,'controller lifetime lease still held')
 with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
  fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
  rawstate=(R/'results/experiment_supervisor/state.json').read_bytes();state=json.loads(rawstate);ctl=state['autonomous_training_v1']
  ck(state['pending_submission'] is None,'all original pending ACKs reconciled')
  ck([imm(j) for j in state['registered_jobs']]==[imm(j) for j in last['postjobs']],'current immutable registry equals prior registry plus exact new shards')
  ck(ctl['reserved_GPU_slots']==0 and ctl['reservation_root_record']==last['reservation'] and ctl['root_submission_hold'] is None,'last exclusive reservation consumed with no leftover reservation')
  for row in rows:
   auth=row['authorization']['sha256'];jid=row['job']['job_id']
   ck(ctl['downstream_reservations_consumed'][auth]==dict(job_id=jid,reservation=row['reservation'],request_token='cti-downstream-gateway-v1:'+auth),'exact one-time consumption '+jid)
   ck(sum(j.get('stage_key')==row['job']['stage_key'] for j in state['registered_jobs'])==1,'stage registered exactly once '+jid)
   ck(ctl['root_reservation_activation_history'].count(row['reserve_receipt'])==1,'activation linked once '+jid)
   prior=row['prior_consumed'];priorauth=prior['request_token'].split(':',1)[1]
   ck(ctl['downstream_reservations_consumed'][priorauth]==prior,'prior consumption history preserved '+jid)
  ck(ctl['blocked_pairs']==initial['blocked_pairs'] and ctl['owner_id']==owner['owner_id'],'historical CUDA blocks and controller owner preserved')
  ck(state['formal_main_progress']['completed_final_trials']==0 and not state['formal_main_progress']['test_opened'] and not state['formal_main_progress']['global_release_created'],'final states remain sealed')
  ck((R/'results/experiment_supervisor/state.json').read_bytes()==rawstate,'current state read consistent under shared lock')
  state_sha=hashlib.sha256(rawstate).hexdigest();fcntl.flock(lock,fcntl.LOCK_UN)
 return dict(schema='formal_main_v2',kind='Long64_seed41_development_submission_independent_review_0727',status='passed',blockers=[],checks_passed=len(checks),checks=checks,evidence_sha256=evidence,observed_state_sha256=state_sha,jobs=[dict(seed=x['seed'],budget=x['budget'],job_id=x['job']['job_id'],authorization=x['authorization'],root_reconciliation=x['root_reconciliation'],original_failure_type=x['failure_type'],reservation=x['reservation'],selected_checkpoints=x['selected'],before_GPU_slots=len(x['pre_capacity']['occupied']),after_GPU_slots=len(x['post_capacity']['occupied']),actual_submit_Asia_Shanghai=x['submit_time'],prepared_registration_UTC=x['prepared_utc'],saved_scheduler_UTC=x['saved_utc']) for x in rows],capacity_sequence=[dict(before=len(x['pre_capacity']['occupied']),after=len(x['post_capacity']['occupied'])) for x in rows],planned_trials=200*len(rows),unique_initial_state_clusters=100,new_trials_completed_by_this_review=0,previous_completed_development_jobs_preserved=['3043709','3045322','3047152','3047156','3047163'],independent_new_scheduler_queries=0,independent_new_GPU_jobs=0,production_state_git_slurm_mutations=False,state_delta_verification='Pinned successfully executed root reconciliation sources assert exact allowed deltas under writer lock and CAS; immutable registry, dedicated reservation consumption, prior histories and current failure blocks independently checked. No recomputation from complete before/after state snapshots claimed.',limitations=['Admission/reconciliation only; not trial completion or success-rate acceptance.','Saved raw sacct/squeue/scontrol evidence reconstructed without new GPU queries.','All shards and prior budgets reuse the same 100 development initial-state clusters.','Receipt canonical JSON identity and frozen file raw SHA verified separately.','Prepared registration timestamps remain historical metadata; actual submit time taken from saved scontrol.'],utc=datetime.now(timezone.utc).isoformat())
try:report=audit()
except BaseException as exc:report=dict(schema='formal_main_v2',kind='Long64_seed41_development_submission_independent_review_0727',status='failed',blockers=[type(exc).__name__+': '+str(exc)],checks_passed=len(checks),checks=checks,evidence_sha256=evidence,traceback=traceback.format_exc(),utc=datetime.now(timezone.utc).isoformat())
report['audit_source']={'path':str(Path(__file__).relative_to(R)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
dest=OUT/'independent_review.json'
with dest.open('x') as f:json.dump(report,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(dict(status=report['status'],checks_passed=len(checks),report=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),blockers=report['blockers'])))
if report['status']!='passed':sys.exit(1)
