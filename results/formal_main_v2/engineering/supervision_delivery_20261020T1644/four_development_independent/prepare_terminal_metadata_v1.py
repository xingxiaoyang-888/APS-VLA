"""Prepare exact, CPU-only terminal review invocations from immutable registration/scheduler evidence."""
from pathlib import Path
import json,hashlib,types,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/four_development_independent_20261020T1644'
REVIEWER='scripts/ops/formal_action_deployment_v1/reviewer.py';RPIN='9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd'
CONSUMER='scripts/ops/formal_action_deployment_v1/consumer.py';CPIN='16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034'
JOBS={'3050870':('libero_spatial',17,2276),'3050890':('libero_spatial',41,2185),'3050901':('libero_object',17,2253),'3050916':('libero_object',41,1994)}
inputs={};checks=0
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(x,msg):
 global checks
 if not x:raise ValueError(msg)
 checks+=1
def read(path,pin=None):
 p=Path(path);ck(p.is_file() and not p.is_symlink(),'regular file '+str(p));b=p.read_bytes();h=sha(b);ck(pin is None or h==pin,'hash '+str(p));inputs[str(p)]={'sha256':h,'bytes':len(b)};return b
def js(path,pin=None):return json.loads(read(path,pin))
def put(name,v):
 p=D/name;p.parent.mkdir(exist_ok=True,parents=True);b=(json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
try:
 snap=js(D/'root_scheduler_snapshot.json','a57ed6af5489fe255ed2777e0b8c13800360cb62a23542b9963beadebdccb93d');st=js(D/'registered_state_snapshot.json','8af2399dd6ed01c401d91e41e19673e0a7995f3e32c2c370142719054fc153fe')
 src=js(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');ck(len(src['files'])==173,'source173')
 for rel,hh in src['files'].items():read(R/rel,hh);read(S/rel,hh)
 m=types.ModuleType('_four_dev_independent_reviewer');m.__file__=str(R/REVIEWER);m.__package__='';sys.modules[m.__name__]=m;exec(compile(read(R/REVIEWER,RPIN),m.__file__,'exec'),m.__dict__)
 ev=m.Evidence(R);read(R/CONSUMER,CPIN)
 rows=snap['scheduler']['rows'];registered=[]
 for old in st['registered_jobs']:
  jid=str(old.get('job_id'))
  if old.get('experiment')!='formal_main_v2' or jid not in rows:continue
  a=rows[jid]
  if a['status'] not in {'COMPLETED','FAILED','CANCELLED','TIMEOUT','PREEMPTED','OUT_OF_MEMORY','NODE_FAIL','BOOT_FAIL','DEADLINE','REVOKED'}:continue
  j=dict(old)
  for k in ['status','exit_code','elapsed_seconds','gpus','node','allocation']:j[k]=a[k]
  registered.append(j)
 calls={};plans={}
 for jid,(suite,seed,elapsed) in JOBS.items():
  matches=[j for j in registered if str(j['job_id'])==jid];ck(len(matches)==1,'one job '+jid);j=matches[0]
  ck(j['status']=='COMPLETED' and j['exit_code']=='0:0' and j['gpus']==1 and j['elapsed_seconds']==elapsed,'terminal '+jid)
  ck(j['suite']==suite and j['mode']=='development' and j['execution_version']=='formal-downstream-action-v1','scope '+jid)
  ck(j['method_ids']==['A64_seed'+str(seed),'B64_seed'+str(seed)] and j['prior_job_ids']==[] and j['resume'] is False,'pair methods '+jid)
  i=ev.read_ref({'path':j['invocation'],'sha256':j['invocation_sha256']})
  original,effective,contract,runtime=m.validate_envelope(ev,j,i,j['action_execution_contract'])
  ck(i['stop_after'] is None and i['stage']=='development' and i['final_values_read_locally'] is False,'full development '+jid)
  ck(i['source_root']==str(S) and i['source_sha256']==src['source_sha256'],'source identity '+jid)
  gate=j['downstream_gateway'];ck(gate['automatic_retry'] is False and gate['request_token']=='cti-downstream-gateway-v1:'+gate['authorization']['sha256'],'token '+jid)
  ack=js(R/'results/formal_main_v2/downstream_gateway'/gate['authorization']['sha256']/'sbatch_result.json')
  ck(ack['returncode']==0 and ack['stdout'].strip()==jid,'exact ACK '+jid)
  auth=ev.read_ref(gate['authorization']);ck(auth['maximum_attempts']==1,'one attempt '+jid)
  calls[jid]={'job':j,'invocation_ref':{'path':j['invocation'],'sha256':j['invocation_sha256']},'expected_contract_ref':j['action_execution_contract'],'pull_ref':'ROOT_MUST_SUPPLY_VERIFIED_ORIGINAL_PULL','registered_jobs_snapshot':'.local/four_development_independent_20261020T1644/terminal_jobs_snapshot.json'}
  plans[jid]={'suite':suite,'seed':seed,'budget':64,'trial_count':200,'source_provenance':i['source_provenance'],'contract':j['action_execution_contract'],'scientific_plan':j['scientific_plan'],'runtime_readiness':j['runtime_readiness'],'invocation':calls[jid]['invocation_ref'],'published_metadata_source_envelope_verified':True,'actual_raw_review_complete':False,'selected_checkpoint_bytes_read':False}
 ev.unchanged();total=sum(JOBS[j][2] for j in JOBS);ck(total==8708,'allocated cost total')
 for rel,hh in ev.files.items():read(R/rel,hh)
 regref=put('terminal_jobs_snapshot.json',{'schema':'formal_main_v2','kind':'private_immutable_terminal_jobs_for_independent_raw_review','registered_jobs':registered,'scheduler_snapshot':{'path':'results/formal_main_v2/preflight/heartbeat_20261021T0044/Object256s23_reservation_activation.json','sha256':'a57ed6af5489fe255ed2777e0b8c13800360cb62a23542b9963beadebdccb93d'},'registration_snapshot_sha256':'8af2399dd6ed01c401d91e41e19673e0a7995f3e32c2c370142719054fc153fe','no_fresh_scheduler_queries':True})
 callsref=put('original_reviewer_calls_candidate.json',{'reviewer':{'path':REVIEWER,'sha256':RPIN},'consumer':{'path':CONSUMER,'sha256':CPIN},'project':str(R),'registered_jobs_snapshot':regref,'jobs':calls,'scope':'Invocation draft only; not executed raw reviews. Root must supply actual verified canonical pull. Private candidates do not authorize publication or scientific integration.'})
 report=put('prepared_metadata_review.json',{'status':'passed_metadata_only','checks':checks,'jobs':plans,'call_draft':callsref,'source173_R_S_unchanged':True,'allocated_GPU_seconds_existing':total,'new_GPU_jobs':0,'raw_trajectory_review_pending':True,'consumer_replay_pending':True,'state_Git_Slurm_mutations':False,'inputs':inputs,'source_closure':ev.files})
 print(json.dumps({'status':'passed_metadata_only','report':report,'calls':callsref,'terminal_snapshot':regref,'checks':checks}))
except BaseException as e:
 p=put('prepare_metadata_failure.json',{'status':'failed','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc(),'inputs':inputs});print(json.dumps(p));raise
