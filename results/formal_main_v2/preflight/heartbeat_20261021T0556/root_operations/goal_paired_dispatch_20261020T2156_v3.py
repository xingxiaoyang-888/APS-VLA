"""Root-only exact paired-input Goal engineering dispatch; one newly reviewed attempt, no training restart."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,fcntl,hashlib,importlib.util,json,os,re,sys,shutil
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
PKG='scripts/ops/formal_goal_paired_input_gate_v1';BASE='results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156';OUT='results/formal_main_v2/preflight/heartbeat_20261021T0556/Goal_paired_dispatch';STATE='results/experiment_supervisor/state.json';AUTH=BASE+'/root_authorization.json';STAGE='goal_paired_input_gate_20261020T2156';NAME='cti-goal-paired-input'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def utc():return datetime.now(timezone.utc).isoformat()
def require(ok,msg):
 if not ok:raise RuntimeError(msg)
def safe(p):
 p=Path(p);require(p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents)),'nonlink exact path required');return p
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p))
def immutable(p,x):
 safe(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(x,sort_keys=True,indent=2,allow_nan=False)+chr(10)).encode());f.flush();os.fsync(f.fileno())
def module(n,pin,name):
 p=safe(R/n);require(h(p)==pin,'module SHA mismatch');sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def fields(text):
 pairs=[part.split('=',1) for part in text.split() if '=' in part];require(len(pairs)==len({key for key,value in pairs}),'duplicate Slurm fields');return dict(pairs)
def actual_identity(f,jid,token,held):
 for k,v in {'JobId':jid,'JobName':NAME,'Comment':token,'Requeue':'0','TimeLimit':'00:30:00','Partition':'L40','Account':'p_p15016','ExcNodeList':'gpu4020','NumCPUs':'7','MinMemoryNode':'64G','Command':str(P/PKG/'run.slurm'),'WorkDir':str(S),'Restarts':'0','QOS':'cpu-500_core-l40-8_card-a800-8_card'}.items():require(f.get(k)==v,'actual Slurm identity differs '+k)
 require(f.get('TresPerNode')=='gres:gpu:l40:1','GPU request differs')
 if held:require(f.get('JobState')=='PENDING' and f.get('Reason')=='JobHeldUser','safe held job required')
 else:require(f.get('JobState') in ('RUNNING','PENDING','CONFIGURING') and f.get('Reason')!='JobHeldUser','release not confirmed')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--authorization-sha256',required=True);ap.add_argument('--dispatch-review',required=True);ap.add_argument('--dispatch-review-sha256',required=True);ap.add_argument('--submit',action='store_true');a=ap.parse_args();require(a.submit,'explicit root submit required');require(Path.cwd().resolve()==R,'control root required')
 c=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','g58dispatchctl');g=module('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','g58dispatchgw');slurm=c.Slurm(timeout=60)
 rp=safe(R/a.dispatch_review);require(rp.is_relative_to(R/'.local/goal_paired_independent_20261020T2156'),'dispatch review scope');require(h(rp)==a.dispatch_review_sha256,'dispatch review changed');rv=read(rp)
 require(rv['status']=='passed' and rv['entrypoint_sha256']==h(Path(__file__)) and not rv.get('blockers'),'independent dispatch gate missing');dr=ref(rp)
 require(re.fullmatch('[a-f0-9]{64}',a.authorization_sha256) and h(safe(R/AUTH))==h(safe(P/AUTH))==a.authorization_sha256,'root authorization bytes differ');auth=read(R/AUTH)
 mf=PKG+'/package_manifest.json';require(h(safe(R/mf))==h(safe(P/mf))==auth['package_manifest_sha256'],'package manifest identity differs');package=read(R/mf)
 require(set(package['files'])=={PKG+'/'+n for n in ['entry.py','observer_v3.py','ast_observer_v2.py','paired_input_gate_v1.py','ast_gate_v2.py','config.json','prefix58.json','run.slurm']},'exact eight-file source closure required')
 for n,pin in package['files'].items():require(h(safe(R/n))==h(safe(P/n))==pin,'published package changed '+n)
 entry=module(PKG+'/entry.py',auth['entrypoint_sha256'],'g58dispatchentry');entry.validate_config(read(P/PKG/'config.json'));entry.validate_authorization(auth,h(P/PKG/'config.json'),h(P/mf),h(P/PKG/'entry.py'))
 for role in ['root','independent']:
  r=auth[role+'_review'];rp=P/BASE/(role+'_readiness.json');require(r['path']==str(rp) and re.fullmatch('[a-f0-9]{64}',r['sha256']) and h(safe(rp))==r['sha256'],'exact CPU review pin missing');entry.check_review(read(rp),role,h(P/mf),h(P/PKG/'config.json'))
 token='cti-goal-paired-input-v1:'+a.authorization_sha256
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  sp=R/STATE;before=h(sp);s=read(sp);old=copy.deepcopy(s);ctl=s['autonomous_training_v1'];f=s['formal_main_progress']
  require(s['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None,'pending/reservation/hold exists')
  require(f['root_and_independent_completed_arms']==72 and len(ctl['completed_pairs'])==36 and not ctl['blocked_pairs'],'training not complete')
  require(not f['test_opened'] and not f['global_release_created'] and f['completed_final_trials']==0,'final seal differs')
  require(not any(j.get('stage_key')==STAGE or j.get('name')==NAME for j in s['registered_jobs']),'prefix diagnostic already registered')
  require(not any((R/OUT/n).exists() for n in ['pending.json','submission_result.json','receipt.json']) and not (P/BASE/'attempt01').exists() and not (P/BASE/'held_dispatch_record.json').exists(),'one diagnostic already attempted')
  owner=read(R/'results/formal_main_v2/autonomous_training/run_v1/owner.json');require(owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538','controller owner differs')
  lease=safe(Path(owner['lock']));require(lease==R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock','lease differs')
  with lease.open('rb') as stream:
   held=False
   try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(stream,fcntl.LOCK_UN)
   except BlockingIOError:held=True
  require(not held,'completed controller lease unexpectedly held')
  obs=slurm.observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,'3034538')
  require(not cap['unknown'] and not cap['findings'] and len(cap['occupied'])+1<=8,'capacity or scheduler identity hold')
  active_registered={str(j['job_id']):j for j in s['registered_jobs'] if str(j['job_id']) in cap['occupied']}
  require(not any(j.get('suite')=='libero_goal' or 'goal' in j.get('stage_key','').lower() or '/libero_goal/' in j.get('run_root','') or j.get('name','').startswith('cti-goal-') for j in active_registered.values()),'another Goal development/engineering/training job is active; one pair one job across all modes')
  cj=obs['rows']['3034538'];require(cj['status']=='COMPLETED' and cj['exit_code']=='0:0' and cj['gpus']==0,'controller did not exit normally')
  for j in s['registered_jobs']:
   jid=str(j['job_id']);g.check_observed_identity(j,obs['rows'][jid],obs['queue'].get(jid),c.TERMINAL)
  require(obs['rows']['3049679']['status']=='COMPLETED' and obs['rows']['3049679']['exit_code']=='0:0','original Goal Slurm disposition differs')
  require(obs['rows']['3053440']['status']=='COMPLETED' and obs['rows']['3053440']['exit_code']=='0:0' and obs['rows']['3053440']['elapsed_seconds']==803,'prior prefix58 engineering disposition differs')
  require(f['Goal_prefix58_engineering_registration']['status']=='completed_diagnostic_not_reproduced_scientific_HOLD' and f['Goal_prefix58_engineering_registration']['maximum_attempts']==1,'original one-shot prefix58 remains closed; no automatic retry')
  require(h(safe(R/'results/formal_main_v2/preflight/heartbeat_20261020T2218/3049679_root_review_failure_20261020T1418.json'))=='49b226c91f99cd9fd3584ab645992244794f4d720e0128d9ab693e82bcca6793','original Goal failure receipt changed')
  goal_status=[x for x in f['nonLong_development_submissions_1317'] if str(x.get('job_id'))=='3049679'];require(len(goal_status)==1 and goal_status[0]['terminal_review_status']=='HOLD_initial_observation_mismatch','original Goal scientific HOLD missing')
  require('3049679' not in f.get('new_action_development_verified_by_job',{}),'original Goal200 incorrectly accepted')
  free_bytes=shutil.disk_usage(P).free;require(free_bytes>=4363621114,'insufficient P space for complete all-query recording plus margin')
  immutable(R/OUT/'storage_at_dispatch.json',dict(required_free_including_1GiB_margin=4363621114,actual_free_bytes=free_bytes,source_bound_sha256='46d3af434e0496574dab46c09ccf5bf79d56708a85e10f68dddd7f631ccc41a7',cross_process_reservation=False,recording_reduced=False,utc=utc()))
  inv,wrapper,ctx,legacy=entry.prepare_original();immutable(R/OUT/'preflight.json',dict(status='original_wrapper_and_selected_checkpoint_bytes_verified_CPU_only',original_invocation=entry.ref(entry.ORIGINAL),source_package=ref(R/mf),final_values_read=False,GPU_execution=False,utc=utc()))
  reservation=dict(schema='formal_main_v2',kind='root_goal_prefix58_GPU_slot_reservation',status='approved_for_exact_prefix58',stage_key=STAGE,authorization=dict(path=str(P/AUTH),sha256=a.authorization_sha256),reserved_slots=1,capacity_limit_all_GPU_modes=8,maximum_wall_seconds=1800,automatic_retry=False,scientific_release=False,root_dispatch_review=dr,utc=utc())
  immutable(R/OUT/'reservation.json',reservation);immutable(P/BASE/'reservation.json',reservation);resref=ref(R/OUT/'reservation.json')
  argv=['sbatch','--hold','--parsable','--no-requeue','--exclude=gpu4020','--comment='+token,'--job-name='+NAME,'--account=p_p15016','--qos=cpu-500_core-l40-8_card-a800-8_card','--partition=L40','--nodes=1','--ntasks=1','--cpus-per-task=7','--gres=gpu:l40:1','--mem=64G','--time=00:30:00','--chdir='+str(S),'--export=ALL,CTI_PAIRED_INPUT_AUTH_SHA256='+a.authorization_sha256,str(P/PKG/'run.slurm')]
  pending=dict(kind='root_bounded_engineering_submission_v1',stage_key=STAGE,request_token=token,status='intent_persisted_before_sbatch',created_utc=utc(),authorization=ref(R/AUTH),actual_sbatch_argv=argv,automatic_retry=False,reservation=resref)
  immutable(R/OUT/'scheduler_before.json',dict(owner=owner,observation=obs,capacity=cap,state_before_sha256=before,controller_lease_released=True));immutable(R/OUT/'pending.json',pending)
  s['pending_submission']=copy.deepcopy(pending);ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=resref;c.atomic_json(sp,s,before);before=h(sp)
  result=slurm.submit(argv);immutable(R/OUT/'submission_result.json',dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,utc=utc()))
  require(result.returncode==0 and re.fullmatch(r'[0-9]+(?:;[A-Za-z0-9_.-]+)?\s*',result.stdout),'unknown sbatch: reconcile exact token without resend')
  jid=result.stdout.strip().split(';')[0];require(not any(str(x['job_id'])==jid for x in s['registered_jobs']),'duplicate ACK ID');pending.update(status='acknowledged_held_job_not_released',job_id=jid);s['pending_submission']=copy.deepcopy(pending);c.atomic_json(sp,s,before);before=h(sp)
  q=slurm.run(['scontrol','show','job','-o',jid]);immutable(R/OUT/'held_identity.json',dict(returncode=q.returncode,stdout=q.stdout,stderr=q.stderr,utc=utc()));require(q.returncode==0,'held identity unavailable');actual_identity(fields(q.stdout),jid,token,True)
  job=dict(job_id=jid,name=NAME,experiment='formal_main_v2',mode='engineering',stage_key=STAGE,suite='libero_goal',visual_tokens=256,training_seed=17,status='PENDING',gpus=1,source_root=str(S),source_sha256='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e',run_root=str(P/BASE/'attempt01'),invocation=AUTH,invocation_sha256=a.authorization_sha256,submitted_utc=pending['created_utc'],maximum_attempts=1,automatic_retry=False,wall_limit_seconds=1800,scientific_trials=0,final_states_opened=False,purpose='Bounded passive paired-input diagnostic on the fixed first58 Goal prefix; not an exact old replay; all Goal science remains HOLD',downstream_gateway=dict(version='root-goal-paired-input-engineering-v1',request_token=token,actual_sbatch_argv=argv,automatic_retry=False),root_reservation=resref,dispatch_review=dr)
  immutable(R/OUT/'job_record.json',job);s['registered_jobs'].append(job);ctl['reserved_GPU_slots']=0;ctl['reservation_consumed_by_job']=jid;ctl.setdefault('engineering_probe_reservations_consumed',[]).append(dict(job_id=jid,reservation=resref));pending['status']='registered_held_pending_release';s['pending_submission']=copy.deepcopy(pending)
  require(f==old['formal_main_progress'] and ctl['completed_pairs']==old['autonomous_training_v1']['completed_pairs'] and s['current_round_cost']==old['current_round_cost'],'unrelated science/cost changed');c.atomic_json(sp,s,before);before=h(sp)
  dispatch=dict(schema='formal_main_v2',kind='root_goal_prefix58_held_dispatch',status='held_registered_before_release',stage_key=STAGE,job_id=jid,authorization=dict(path=str(P/AUTH),sha256=a.authorization_sha256),request_token=token,capacity_limit_all_GPU_modes=8,reserved_slots=1,maximum_attempts=1,new_submissions=1,no_requeue=True,scientific_release=False,resources=entry.RESOURCES,occupied_job_ids=[*cap['occupied'],jid],state_after_sha256=before,reservation=dict(path=str(P/BASE/'reservation.json'),sha256=h(P/BASE/'reservation.json')))
  entry.validate_dispatch(dispatch,reservation,auth,a.authorization_sha256,jid,h(P/BASE/'reservation.json'));immutable(R/OUT/'held_dispatch_record.json',dispatch);immutable(P/BASE/'held_dispatch_record.json',dispatch)
  rel=slurm.run(['scontrol','release',jid]);immutable(R/OUT/'release_command.json',dict(returncode=rel.returncode,stdout=rel.stdout,stderr=rel.stderr,utc=utc()));require(rel.returncode==0,'release uncertain: pending retained')
  q=slurm.run(['scontrol','show','job','-o',jid]);immutable(R/OUT/'released_identity.json',dict(returncode=q.returncode,stdout=q.stdout,stderr=q.stderr,utc=utc()));require(q.returncode==0,'release identity unknown');f2=fields(q.stdout);actual_identity(f2,jid,token,False)
  job['status']=f2['JobState'];s['pending_submission']=None;ctl['occupied_job_ids']=[*cap['occupied'],jid];c.atomic_json(sp,s,before)
  result=dict(schema='formal_main_v2',status='registered_and_release_verified',job_id=jid,request_token=token,authorization=ref(R/AUTH),dispatch_review=dr,job_record=ref(R/OUT/'job_record.json'),reserved_GPU_slots=0,occupied_before=len(cap['occupied']),maximum_gpu_occupancy=len(cap['occupied'])+1,scientific_release=False,Goal_original200_HOLD=True,all_new_Goal_science_HOLD=True,utc=utc(),state_after_sha256=h(sp));immutable(R/OUT/'receipt.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
