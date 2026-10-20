"""Independent original reviewer invocation on real canonical stable nonweight pull; no root publication."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,types,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/four_development_independent_20261020T1644'
PULL={'path':'results/formal_main_v2/pulls/20261020T174830Z_45bc1fa22551/receipt.json','sha256':'f92b3cbe59584160b698c32b192b395284238dd8e0249151d1029f9d13c038cd'}
RP='scripts/ops/formal_action_deployment_v1/reviewer.py';RH='9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd'
inputs={}
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,pin=None):
 p=Path(p);assert p.is_file() and not p.is_symlink();b=p.read_bytes();h=sha(b);assert pin is None or h==pin,(str(p),h,pin);inputs[str(p)]={'sha256':h,'bytes':len(b)};return b
def js(p,pin=None):return json.loads(read(p,pin))
def put(name,v):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True);b=(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
start=time.monotonic();cpu=time.process_time()
try:
 pull=js(R/PULL['path'],PULL['sha256']);assert pull['status']=='verified_nonweight_snapshot' and pull['weights_copied'] is False and pull['sealed_initial_states_copied'] is False
 call=js(D/'original_reviewer_calls_candidate.json','61052863e5d880e0bafeb7d6d6eb7dba70eee2e20799d9602fb89cc64cf58d25');snap=js(R/call['registered_jobs_snapshot']['path'],call['registered_jobs_snapshot']['sha256']);ids=set(call['jobs'])
 assert len(pull['files'])==99 and ids<=set(pull['requested_job_ids'])
 rows=[x for x in pull['files'] if ids&set(x['job_ids'])];assert len(rows)==48
 for row in rows:
  assert row['local_path']==str(R/row['relative']) and row['path']==str(P/row['relative'])
  local=read(R/row['relative'],row['sha256']);remote=read(P/row['relative'],row['sha256']);assert local==remote and len(local)==row['bytes']
 mod=types.ModuleType('_independent_four_original_terminal');mod.__file__=str(R/RP);mod.__package__='';sys.modules[mod.__name__]=mod;exec(compile(read(R/RP,RH),mod.__file__,'exec'),mod.__dict__)
 outcomes={}
 for jid,c in call['jobs'].items():
  try:
   report=mod.review(R,job=c['job'],invocation_ref=c['invocation_ref'],pull_ref=PULL,registered_jobs=snap['registered_jobs'],expected_contract_ref=c['expected_contract_ref'])
   assert report['scientific_complete'] and report['completed_trials']==report['expected_trials']==200
   assert report['cost']['current_gpu_seconds']==report['cost']['all_attempt_gpu_seconds']==c['job']['elapsed_seconds']
   ref=put('original_review_candidates/'+jid+'.json',report)
   outcomes[jid]={'status':'passed_original_raw_review_privately','candidate_review':ref,'scientific_complete':True,'trials':200,'allocated_GPU_seconds':report['cost']['current_gpu_seconds'],'root_publication':False,'consumer_replay_pending_root_publication':True}
  except Exception as e:
   ref=put('original_review_failures/'+jid+'.json',{'status':'failed','job_id':jid,'error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'pull':PULL,'no_retry':True,'scientific_acceptance':False})
   outcomes[jid]={'status':'failed','failure':ref,'scientific_acceptance':False};print(json.dumps({'job_id':jid,'failed':str(e)}),flush=True)
  print(json.dumps({'job_id':jid,'status':outcomes[jid]['status']}),flush=True)
 summary=put('original_review_candidates_index.json',{'schema':'formal_main_v2','kind':'independent_original_action_reviewer_invocations','status':'passed' if all(x['status']=='passed_original_raw_review_privately' for x in outcomes.values()) else 'failed','reviewer':{'path':RP,'sha256':RH},'pull':PULL,'jobs':outcomes,'real_P_R_equal_files':len(rows),'review_candidates_not_root_publication':True,'private_candidate_shape_note':'Original API returns kind=root_downstream_review/reviewed_by=root. Saved only privately as candidate: root must perform its own review and explicitly publish. No root authorization asserted by this agent.','consumer_replay_pending_root_publication':True,'input_hashes':inputs,'sealed_final_values_read':False,'checkpoint_bytes_read':False,'new_GPU_jobs':0,'state_Git_Slurm_mutations':False,'CPU_wall_seconds':time.monotonic()-start,'CPU_process_seconds':time.process_time()-cpu})
 print(json.dumps({'summary':summary,'status':'passed' if all(x['status']=='passed_original_raw_review_privately' for x in outcomes.values()) else 'failed'}))
except BaseException as e:
 ref=put('original_reviewer_harness_failure_v1.json',{'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'inputs':inputs});print(json.dumps(ref));raise
