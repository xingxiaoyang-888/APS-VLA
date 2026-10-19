"""Independent, read-only check of the named unconsumed reservation.
No Gateway.run, submit, state/Slurm mutation, tensor/model load or final payload.
"""
from pathlib import Path
from copy import deepcopy
import datetime, hashlib, importlib.util, json, sys, traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/spatial_cuda_reservation_audit_1621'
AUTH={'path':'configs/experiments/formal_main_v2_cuda_single_recovery_3028522_v1.json','sha256':'7411a2e5e0d7e2123eea8bfea4c2bbaccb037d54b09697180340a597e3cfb18a'}
GATEWAY='.local/cuda_recovery_autonomous_1940/gateway.py'
GATEWAY_SHA='c97b66100a0a21a722b17e32129b7a220fac7b2b2cb8b9cc9678b88f605476c3'
PAIR='libero_spatial_k64_seed23'
STAGE='libero_spatial_train_k64_seed23'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for data in iter(lambda:f.read(8<<20),b''):h.update(data)
 return h.hexdigest()
def put(name,value):
 p=D/name
 with p.open('x',encoding='utf-8') as f:f.write(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n')
 return {'path':p.relative_to(R).as_posix(),'sha256':digest(p)}
def require(value,msg):
 if not value:raise ValueError(msg)
def load(path,name,checksum):
 require(digest(path)==checksum,'source SHA differs '+str(path))
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def review():
 start=datetime.datetime.now(datetime.timezone.utc).isoformat()
 g=load(R/GATEWAY,'independent_reservation_gateway',GATEWAY_SHA)
 auth,ae=g.validate_authorization(R,AUTH)
 c=g.load(R/g.CONTROLLER,'independent_reservation_controller',g.CONTROLLER_SHA)
 e=g.e
 raw=(R/g.STATE).read_bytes();state=json.loads(raw);state_sha=hashlib.sha256(raw).hexdigest()
 require((R/g.STATE).read_bytes()==raw,'state changed during initial read')
 jobs=state['registered_jobs'];ctl=state['autonomous_training_v1']
 require(state.get('pending_submission') is None and 'pending_submission' in state,'pending submission remains')
 require(ctl['activation']==auth['controller_activation'] and ctl['activation_sha256']==auth['controller_activation']['sha256'] and ctl['controller_job_id']==auth['controller_job_id'],'controller owner changed')
 require(ctl.get('root_submission_hold') is None,'another root submission hold')
 require(ctl.get('reserved_GPU_slots')==0,'existing active reservation needs separate root handling')
 require(AUTH['sha256'] not in ctl.get('cuda_recovery_reservations_consumed',{}),'authorization was already consumed')
 require(PAIR not in ctl.get('completed_pairs',{}),'target pair already complete')
 blocked=ctl.get('blocked_pairs',{}).get(PAIR)
 require(blocked and blocked['failed_job_ids']==['3028522'] and blocked.get('automatic_retry') is False,'original failed block missing/changed')
 own=[j for j in jobs if j.get('experiment')=='formal_main_v2' and j.get('stage_key')==STAGE]
 require([j['job_id'] for j in own]==['3024716','3025205','3028522'],'target pair history advanced or changed')
 require(max(own,key=lambda j:j['submitted_utc'])['job_id']=='3028522','newer target pair job exists')
 require(not any(j.get('startup_recovery',{}).get('authorization')==AUTH for j in jobs),'authorization already registered')
 require(not (R/'results/formal_main_v2/startup_recoveries/3028522'/AUTH['sha256']).exists(),'prior submission transaction exists')
 tracking=state['formal_main_progress']['parallel_execution']['pair_tracking'][PAIR]
 live=c.Slurm().observe(jobs)
 require(set(live['rows'])=={str(j['job_id']) for j in jobs},'missing actual registered-job accounting')
 caps=c.capacity(jobs,live,auth['controller_job_id'])
 require(not caps['unknown'] and not caps['findings'],'scheduler uncertainty')
 require(PAIR not in caps['active_pairs'],'target pair already active')
 require(all(live['rows'][j['job_id']]['status'] in c.TERMINAL for j in own),'target history active')
 cid=auth['controller_job_id'];cj=next(j for j in jobs if str(j['job_id'])==cid)
 require(cj['gpus']==0 and live['rows'][cid]['gpus']==0 and live['rows'][cid]['status']=='RUNNING','controller not actual running CPU0')
 require(live['rows']['3028522']['status']=='FAILED' and live['rows']['3028522']['exit_code']=='1:0' and live['rows']['3028522']['elapsed_seconds']==73,'failed identity/cost changed')
 # Every scheduler query only names registered IDs. Raw accounting is retained.
 query_ref=put('registered_scheduler_observation.json',{'created_utc':start,'registered_jobs':jobs,'state_sha256':state_sha,
  'snapshot':live,'capacity':caps,'Slurm_mutations':False})
 activation=ae.ref(auth['controller_activation'])
 for key in ('backend','worker','execution_adapter','launcher','CPU_service_wrapper'):
  ae.watch(activation[key]['path'],activation[key]['sha256'])
 require(activation['controller_sha256']==g.CONTROLLER_SHA and activation['known_abnormal_jobs_held']==['3028460','3028468','3028522'],'activation identity/held failures changed')
 # The exact immutable failure auditor is used directly, with its original
 # archive reconstruction. No change to an active-job projection or old gate.
 science=e.RecoveryScience(R);proofs={};proof_records=[]
 publication=ae.ref(auth['canonical_publication'])
 for jid,case in e.CASES.items():
  job=next(j for j in jobs if j['job_id']==jid)
  proof=science.failure.require_saved(science.e,job=job)
  path=science.failure.proof_relative(job)
  require(science.e.watch(path,case[5])==case[5],'canonical fixed proof SHA differs')
  require(next(x for x in publication['proofs'] if x['job_id']==jid)['sha256']==case[5],'canonical publication differs')
  proof_records.append({'job_id':jid,'reference':{'path':path,'sha256':case[5]},
   'original_require_saved_reconstruction':True,'original_failed_status':proof['failed_status'],
   'completed_by_arm':proof['completed_by_arm'],'next_sample_cursor':proof['next_sample_cursor'],
   'failed_GPU_seconds':proof['failed_allocation_gpu_seconds'],'historical_proof_recovery_authorization':proof['root_recovery_authorization']})
  proofs[jid]=proof
 proof=proofs['3028522']
 require(proof['completed_by_arm']=={'A':1000,'B':1000} and proof['next_sample_cursor']=={'A':8000,'B':8000},'boundary/cursor changed')
 require(proof['current_allocation_new_updates']==0 and proof['current_allocation_arm_initializations']==0,'failed allocation advanced training')
 previous=science.e.ref(proof['previous_boundary_review'])
 require(previous['status']=='passed' and previous['completed_by_arm']==proof['completed_by_arm'] and previous['server_resume_checks']==proof['server_resume_checks'],'previous reviewed checkpoint identity differs')
 failed=own[-1];original=science.e.read(failed['invocation'],failed['invocation_sha256'])
 require(original['segment_end']==1500 and original['argv'][-1]=='--resume','original target/resume changed')
 values=dict(zip(original['argv'][:-1:2],original['argv'][1:-1:2]))
 require(values['--stop-after-updates']=='1500' and values['--max-wall-seconds']=='12600','execution target changed')
 inventory=science.e.read(science.failure.SOURCE,science.failure.SOURCE_PIN)
 require(len(inventory['files'])==173 and inventory['source_sha256']==e.SOURCE_SHA,'frozen source identity')
 for rel,pin in inventory['files'].items():science.e.watch(rel,pin)
 reg=science.e.read(e.REG,e.REG_SHA)
 pair=next(x for x in reg['pairs'] if (x['suite'],x['visual_tokens'],x['seed'])==('libero_spatial',64,23))
 config=science.e.read(pair['path'],pair['sha256'])
 require(config['training']['updates']==5000 and config['training']['effective_batch']==8 and config['tokens_per_camera']==32,'formal scientific schedule changed')
 require(config['selection']['updates']==list(range(0,5001,500)) and config['future']['horizon']==8 and config['future']['weight_B']==0.1,'validation/future settings changed')
 require(config['gate']['alpha_start']==2 and config['gate']['alpha_end']==0.1,'gate schedule changed')
 nextinv=f'results/formal_main_v2/invocations/{STAGE}_attempt04.json'
 require(not (R/nextinv).exists() and not (e.P/nextinv).exists(),'next invocation already published')
 for path,pin in original['watched_files'].items():science.e.watch(science.failure.local_server(path),pin)
 # This narrow object is only NativeIO's read-only input view. It is NOT a
 # prepared production plan or approval. No new invocation is constructed.
 wrapper,wrappersha=e.WRAPPERS['libero_spatial'];science.e.watch(wrapper,wrappersha)
 io_view={'proof':proof,'inventory':inventory,'remote_watched':dict(original['watched_files']),
  'wrapper':str(e.S/wrapper),'wrapper_sha256':wrappersha,'fresh':False,'invocation_relative':nextinv}
 checked=e.NativeIO().preflight(io_view)
 require(checked['model_loaded'] is False and checked['final_states_opened'] is False,'preflight scope violation')
 for item in checked['server_resume_checks']:
  require(item['stable_during_hash'] is True,'resume bytes unstable')
 checked['scope']='original NativeIO byte/path checks only; no RecoveryScience.prepare admission and no production invocation'
 checked['optimizer_rng_or_tensor_deserialized']=False
 io_ref=put('original_native_io_readonly_check.json',checked)
 science.e.unchanged();ae.unchanged()
 endraw=(R/g.STATE).read_bytes();end=json.loads(endraw);endctl=end['autonomous_training_v1']
 endown=[j for j in end['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('stage_key')==STAGE]
 require(endown==own and end.get('pending_submission') is None,'target history or pending changed during review')
 for key in ('activation','activation_sha256','controller_job_id','owner_id','reserved_GPU_slots','reservation_root_record','root_submission_hold','cuda_recovery_reservations_consumed'):
  require(endctl.get(key)==ctl.get(key),'controller/reservation changed during review '+key)
 require(endctl.get('blocked_pairs',{}).get(PAIR)==blocked,'target failed block changed')
 require(AUTH['sha256'] not in endctl.get('cuda_recovery_reservations_consumed',{}),'authorization consumed during review')
 state_view={'state_sha256_before':state_sha,'state_sha256_after':hashlib.sha256(endraw).hexdigest(),
  'registry_count_before':len(jobs),'registry_count_after':len(end['registered_jobs']),
  'controller':{k:ctl.get(k) for k in ('activation','activation_sha256','controller_job_id','owner_id','reserved_GPU_slots','reservation_root_record','root_submission_hold','cuda_recovery_reservations_consumed')},
  'failed_pair_block':blocked,'pair_history':own,'pair_tracking':tracking,
  'target_identity_fields_unchanged_during_review':True,'state_write_performed':False}
 state_ref=put('state_identity_observation.json',state_view)
 result={'schema':'formal_main_v2','kind':'spatial_cuda_reservation_independent_review','status':'PASS_reservation_preparation_only',
  'review_role':'independent','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'authorization':AUTH,'root_reservation':auth['root_reservation'],'failed_job_id':'3028522','pair_key':PAIR,
  'root_reservation_is_valid_unconsumed_but_not_active':True,'blocked_history_preserved':True,
  'completed_by_arm':proof['completed_by_arm'],'next_sample_cursor':proof['next_sample_cursor'],
  'authorized_next_segment':1500,'full_training_schedule':5000,'effective_batch':8,'single_new_attempt_limit':1,
  'controller_job_id':cid,'actual_controller_CPU0_running':True,'actual_GPU_occupancy':len(caps['occupied']),
  'actual_same_pair_active_jobs':caps['active_pairs'].get(PAIR,[]),'canonical_failure_reviews':proof_records,
  'resume_checks':checked['server_resume_checks'],'native_io_check':io_ref,'scheduler_observation':query_ref,'state_observation':state_ref,
  'files':dict(sorted({**science.e.hashes,**ae.hashes,GATEWAY:GATEWAY_SHA,g.CONTROLLER:g.CONTROLLER_SHA}.items())),
  'review_script_sha256':digest(Path(__file__)),
  'checks_not_run':{'RecoveryScience.prepare':'not called; original active-count gate correctly waits for less than eight GPU jobs; no projected/fake free slot',
   'Gateway.run':'not called','GPU_restore':'not run','optimizer_RNG_tensor_deserialization':'not run'},
  'scope':{'checkpoint_bytes_hashed':True,'checkpoint_payloads_deserialized':False,'actual_GPU_restore_succeeded':False,
   'reservation_activated':False,'production_invocation_published':False,'Slurm_submitted_or_mutated':False,
   'state_written':False,'P_written':False,'Git_written':False,'scientific_settings_changed':False,
   'sealed_state_values_read':False,'final_release':False,'continuous5000_admission_granted':False},
  'remaining_conditions':['Root must activate this exact one-slot reservation under the shared writer lock/CAS, respecting any intervening reservation or pending transaction',
   'Do not cancel healthy jobs; wait until the real all-registered-job observation yields a free GPU slot',
   'Immediately before any one-shot submit rerun the original full gateway typed authorization, capacity, RecoveryScience.prepare, NativeIO, fresh accounting and durable pending transaction',
   'Any unknown or duplicate submission remains fail-closed; retain FAILED3028522 and all failure/replay cost',
   'After the bounded 1000-to1500 attempt, root/raw and independent recovery review is still required; this receipt proves no GPU tensor restoration']}
 return result
try:
 result=review();ref=put('independent_review.json',result)
 print(json.dumps({'status':result['status'],'GPU_occupied':result['actual_GPU_occupancy'],'refs':len(result['files']),'receipt':ref},sort_keys=True))
except BaseException as exc:
 ref=put('failed_review.json',{'status':'blocked','error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'script_sha256':digest(Path(__file__))})
 print(json.dumps(ref));raise
