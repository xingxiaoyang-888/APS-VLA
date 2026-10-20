"""Root only: one fixed Goal t0 engineering probe; no science release or retry."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,fcntl,hashlib,importlib.util,json,re,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
S=P/'snapshots/formal_main_v2_run_564be0995e'
BASE='results/formal_main_v2/engineering/goal_t0_probe_20261020T1418'
OUT='results/formal_main_v2/preflight/heartbeat_20261020T2330/Goal_t0_dispatch'
STATE='results/experiment_supervisor/state.json'
STAGE='goal_t0_probe_20261020T1418_attempt01'
AUTH=BASE+'/root_authorization.json'
NAME='cti-goal-t0-probe'
CONFIG_SHA='773594fc7ccaeb51d44b348283634dcb6461945d503893fcdb33ce3b12e118ff'
ENTRY_SHA='4d0eec76dddf7574521231911c29e0df8dbbeb372910d615c00914451a1cb92c'
SOURCES={'probe.py':ENTRY_SHA,'config.json':CONFIG_SHA,'original_loading_prefix.py':'bf579f705c07c5ec8a13ef1feced7d2cc13d799b2f61e86a48d73e3b6507c709','candidate.slurm':'6fae7f5ccc9c79d4c3a93b9807c55be7603aa947184d9d6c3dd579d11deda89b'}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def require(ok,msg):
 if not ok:raise RuntimeError(msg)
def read(p):return json.loads(p.read_bytes())
def utc():return datetime.now(timezone.utc).isoformat()
def norefsymlink(p):
 for x in (p,*p.parents):require(not x.is_symlink(),'symlink forbidden: '+str(x))
 return p
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=sha(p))
def immutable(p,data):
 norefsymlink(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(data,sort_keys=True,indent=2)+'\n').encode());f.flush();__import__('os').fsync(f.fileno())
def module(rel,pin,name):
 p=norefsymlink(R/rel);require(sha(p)==pin,'module identity drift')
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def job_fields(text):
 return {m.group(1):m.group(2).strip() for m in re.finditer(r'(?:^|\s)([A-Za-z][A-Za-z0-9_]*)=(.*?)(?=\s[A-Za-z][A-Za-z0-9_]*=|$)',text.strip())}
def verify_held_or_released(fields,jid,token,held):
 for k,v in {'JobId':jid,'JobName':NAME,'Comment':token,'Requeue':'0','TimeLimit':'00:30:00','Partition':'L40','Account':'p_p15016'}.items():require(fields.get(k)==v,'scontrol identity '+k)
 require(fields.get('TresPerNode') in ('gres/gpu:l40:1','gres/gpu:1'),'GPU request differs')
 require(fields.get('ExcNodeList')=='gpu4020','node exclusion differs')
 if held:require(fields.get('JobState')=='PENDING' and fields.get('Reason')=='JobHeldUser','job is not safely held')
 else:require(fields.get('JobState') in ('RUNNING','PENDING','CONFIGURING') and fields.get('Reason')!='JobHeldUser','release not confirmed')
def submit_once(c,g,slurm,auth_sha,review_ref):
 """All mutation remains under one shared writer-lock transaction."""
 require(re.fullmatch('[a-f0-9]{64}',auth_sha) is not None,'bad authorization SHA')
 require(Path.cwd().resolve()==R,'control workspace required')
 review_path=norefsymlink(R/review_ref['path']);require(review_path.is_relative_to(R/'.local/goal_t0_dispatch_independent_20261020T1530'),'independent dispatch namespace differs')
 require(sha(review_path)==review_ref['sha256'],'dispatch review changed');rv=read(review_path)
 require(rv['status']=='passed' and rv['entrypoint_sha256']==sha(Path(__file__)) and not rv.get('blockers'),'dispatch independent gate missing')
 for name,h in SOURCES.items():require(sha(norefsymlink(P/BASE/'source'/name))==h,'published source differs '+name)
 require(sha(norefsymlink(R/AUTH))==sha(norefsymlink(P/AUTH))==auth_sha,'authorization source/target differs')
 a=read(R/AUTH);require(a['schema']=='formal_main_v2' and a['kind']=='root_bounded_engineering_probe_authorization' and a['status']=='approved' and a['reviewed_by']=='root','root gate')
 require(a['config_sha256']==CONFIG_SHA and a['entrypoint_sha256']==ENTRY_SHA and a['maximum_gpu_jobs']==1 and a['maximum_wall_seconds']==1800 and a['counts_against_8_GPU_slots'] is True,'exact bounded scope')
 require(a['scientific_release'] is False and a['original_goal_failure_retained'] is True and a['automatic_retry'] is False,'science HOLD/retry differs')
 require(a['best_effort_application_timeout_not_hard_bound'] is True and a['does_not_replay_original_200_trial_history'] is True,'known limitations missing')
 for role in ['root_review','independent_review']:
  rr=a[role];rp=norefsymlink(Path(rr['path']));require(rp.is_relative_to(P/BASE),'probe review namespace')
  require(sha(rp)==rr['sha256'],'probe review differs');v=read(rp)
  require(v['status']=='passed' and v['entrypoint_sha256']==ENTRY_SHA and v['config_sha256']==CONFIG_SHA,'probe review gate')
 require(a['root_review']!=a['independent_review'],'independent review must differ')
 token='cti-goal-t0-probe-v1:'+auth_sha
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  statep=R/STATE;before=sha(statep);state=read(statep);old=copy.deepcopy(state);ctl=state['autonomous_training_v1']
  require(state['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None,'pending/reservation/hold already present')
  require(not any(j.get('stage_key')==STAGE or j.get('name')==NAME for j in state['registered_jobs']),'probe already registered')
  require(not (P/BASE/'attempt01').exists() and not (R/OUT/'pending.json').exists() and not (R/OUT/'submission_result.json').exists(),'probe already attempted')
  owner=read(R/'results/formal_main_v2/autonomous_training/run_v1/owner.json')
  require(owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538','controller owner differs')
  lease=norefsymlink(Path(owner['lock']));require(lease==R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock','lease path')
  with lease.open('rb') as f:
   held=False
   try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
   except BlockingIOError:held=True
  require(held,'controller lease not held')
  obs=slurm.observe(state['registered_jobs']);cap=c.capacity(state['registered_jobs'],obs,'3034538')
  require(not cap['unknown'] and not cap['findings'] and len(cap['occupied'])+1<=8,'capacity/identity hold')
  require(obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0,'controller not healthy')
  for jid in cap['occupied']:
   j=next(x for x in state['registered_jobs'] if str(x['job_id'])==jid);g.check_observed_identity(j,obs['rows'][jid],obs['queue'].get(jid),c.TERMINAL)
  # Exact published original wrapper metadata check. No tensors or GPU execution.
  pre=slurm.run([sys.executable,'-B',str(P/BASE/'source/probe.py'),'--config',str(P/BASE/'source/config.json'),'--config-sha256',CONFIG_SHA])
  immutable(R/OUT/'preflight.json',dict(returncode=pre.returncode,stdout=pre.stdout,stderr=pre.stderr,utc=utc()))
  require(pre.returncode==0 and json.loads(pre.stdout)['status']=='cpu_prepared_not_GPU_run','actual P prepare failed')
  reservation=dict(schema='formal_main_v2',kind='root_engineering_GPU_slot_reservation',status='approved_for_exact_probe',controller_job_id='3034538',stage_key=STAGE,reserved_slots=1,capacity_limit_all_GPU_modes=8,authorization=ref(R/AUTH),dispatch_review=review_ref,automatic_retry=False,maximum_wall_seconds=1800,application_timeout_best_effort=True,scientific_release=False,utc=utc())
  immutable(R/OUT/'reservation.json',reservation);resref=ref(R/OUT/'reservation.json')
  argv=['sbatch','--hold','--parsable','--no-requeue','--exclude=gpu4020','--comment='+token,'--job-name='+NAME,'--account=p_p15016','--qos=cpu-500_core-l40-8_card-a800-8_card','--partition=L40','--nodes=1','--ntasks=1','--cpus-per-task=7','--gres=gpu:l40:1','--mem=64G','--time=00:30:00','--chdir='+str(P),'--export=ALL,ROOT_AUTHORIZATION='+str(P/AUTH)+',ROOT_AUTHORIZATION_SHA256='+auth_sha,str(P/BASE/'source/candidate.slurm')]
  pending=dict(kind='root_bounded_engineering_submission_v1',stage_key=STAGE,request_token=token,status='intent_persisted_before_sbatch',created_utc=utc(),authorization=ref(R/AUTH),actual_sbatch_argv=argv,automatic_retry=False,reservation=resref)
  immutable(R/OUT/'scheduler_before.json',dict(owner=owner,observation=obs,capacity=cap,state_before_sha256=before))
  immutable(R/OUT/'pending.json',pending)
  state['pending_submission']=copy.deepcopy(pending);ctl['reserved_GPU_slots']=1;ctl['reservation_root_record']=resref
  c.atomic_json(statep,state,before);before=sha(statep)
  # After this point any exception leaves durable pending; never clear, resend, cancel, or retry.
  result=slurm.submit(argv)
  immutable(R/OUT/'submission_result.json',dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,utc=utc()))
  require(result.returncode==0 and re.fullmatch(r'[0-9]+(?:;[A-Za-z0-9_.-]+)?\s*',result.stdout) is not None,'unknown submission: reconcile exact comment only')
  jid=result.stdout.strip().split(';')[0];require(not any(str(x['job_id'])==jid for x in state['registered_jobs']),'duplicate ACK job ID')
  pending.update(status='acknowledged_held_job_not_released',job_id=jid);state['pending_submission']=copy.deepcopy(pending)
  c.atomic_json(statep,state,before);before=sha(statep)
  q=slurm.run(['scontrol','show','job','-o',jid]);immutable(R/OUT/'held_identity.json',dict(returncode=q.returncode,stdout=q.stdout,stderr=q.stderr,utc=utc()))
  require(q.returncode==0,'held identity unavailable');verify_held_or_released(job_fields(q.stdout),jid,token,True)
  job=dict(job_id=jid,name=NAME,experiment='formal_main_v2',mode='engineering',stage_key=STAGE,suite='libero_goal',visual_tokens=256,training_seed=17,status='PENDING',gpus=1,source_root=str(S),source_sha256='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e',run_root=str(P/BASE/'attempt01'),invocation=AUTH,invocation_sha256=auth_sha,submitted_utc=pending['created_utc'],maximum_attempts=1,automatic_retry=False,wall_limit_seconds=1800,scientific_trials=0,final_states_opened=False,purpose='Bounded Goal task2/index42 t0 engineering diagnosis; original200 remain HOLD',downstream_gateway=dict(version='root-bounded-engineering-v1',request_token=token,actual_sbatch_argv=argv,automatic_retry=False),root_reservation=resref,dispatch_review=review_ref)
  immutable(R/OUT/'job_record.json',job);state['registered_jobs'].append(job)
  ctl['reserved_GPU_slots']=0;ctl['reservation_consumed_by_job']=jid;ctl.setdefault('engineering_probe_reservations_consumed',[]).append(dict(job_id=jid,reservation=resref))
  pending['status']='registered_held_pending_release';state['pending_submission']=copy.deepcopy(pending)
  require(state['formal_main_progress']==old['formal_main_progress'] and ctl['blocked_pairs']==old['autonomous_training_v1']['blocked_pairs'] and state['current_round_cost']==old['current_round_cost'],'unrelated scientific/state drift')
  c.atomic_json(statep,state,before);before=sha(statep)
  release=slurm.run(['scontrol','release',jid]);immutable(R/OUT/'release_command.json',dict(returncode=release.returncode,stdout=release.stdout,stderr=release.stderr,utc=utc()))
  require(release.returncode==0,'release uncertain: retain known pending')
  q=slurm.run(['scontrol','show','job','-o',jid]);immutable(R/OUT/'released_identity.json',dict(returncode=q.returncode,stdout=q.stdout,stderr=q.stderr,utc=utc()))
  require(q.returncode==0,'release identity unavailable');fields=job_fields(q.stdout);verify_held_or_released(fields,jid,token,False)
  job['status']=fields['JobState'];state['pending_submission']=None
  ctl['occupied_job_ids']=list(dict.fromkeys([*cap['occupied'],jid]))
  c.atomic_json(statep,state,before)
  receipt=dict(schema='formal_main_v2',kind='root_single_engineering_dispatch',status='registered_and_release_verified',job_id=jid,request_token=token,authorization=ref(R/AUTH),dispatch_review=review_ref,job_record=ref(R/OUT/'job_record.json'),reserved_GPU_slots=0,occupied_before=len(cap['occupied']),maximum_gpu_occupancy=len(cap['occupied'])+1,scientific_release=False,original200_still_HOLD=True,utc=utc(),state_after_sha256=sha(statep))
  immutable(R/OUT/'receipt.json',receipt);return receipt

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--authorization-sha256',required=True);ap.add_argument('--dispatch-review',required=True);ap.add_argument('--dispatch-review-sha256',required=True);ap.add_argument('--submit',action='store_true');ap.add_argument('--root-reviewed-submit',action='store_true');a=ap.parse_args()
 require(a.submit and a.root_reviewed_submit,'explicit two-part root action required')
 c=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','goalprobe1530ctl')
 g=module('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','goalprobe1530gw')
 print(json.dumps(submit_once(c,g,c.Slurm(timeout=60),a.authorization_sha256,dict(path=a.dispatch_review,sha256=a.dispatch_review_sha256)),sort_keys=True))
if __name__=='__main__':main()
