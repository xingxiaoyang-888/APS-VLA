"""Single explicit root admission to5000; not an autonomous failure retry loop."""
from pathlib import Path
import argparse, copy, fcntl, hashlib, importlib.util, json, os, re, sys, uuid
sys.dont_write_bytecode=True
ADMISSION_SHA='88241a5a0a14f83ab63f378fe135d50f3b72629a57aaef87b09e113b795215bd'
def load(path,pin,name):
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('pinned module differs: '+str(path))
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);exec(compile(raw,str(path),'exec'),m.__dict__);return m
a=load(Path(__file__).with_name('admission.py'),ADMISSION_SHA,'_once_continuation_admission')
require=a.require;sha=a.digest;canonical=a.canonical
CONTROLLER='scripts/ops/formal_autonomous_training_v1/controller.py'
CONTROLLER_SHA='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
IDENTITY='scripts/ops/formal_action_deployment_v1/gateway.py'
IDENTITY_SHA='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
def immutable(path,raw):
 p=a.direct(path);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.partial')
 with tmp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 try:os.link(tmp,p)
 finally:tmp.unlink()
 fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)
def record(path,value):immutable(path,canonical(value))
def source_files():
 return {a.CANON+'gateway.py':sha(Path(__file__).read_bytes()),a.CANON+'admission.py':ADMISSION_SHA}
def validate_authorization(root,ref):
 e=a.Evidence(root);v=e.ref(ref)
 expected=dict(schema='formal_main_v2',kind='root_cuda_recovered_continuous_admission_authorization',version=a.VERSION,
  status='approved_exact_once_1500_to5000',reviewed_by='root',pair_key=a.PAIR,failed_job_id='3028522',recovery_job_id='3043399',
  completed_before={'A':1500,'B':1500},cursor_before={'A':12000,'B':12000},historical_GPU_seconds=a.HISTORICAL_SECONDS,target_updates_per_arm=5000,
  resume=True,single_new_attempt=True,automatic_retry=False,soft_wall_seconds=169200,allocation_time='48:00:00',
  excluded_nodes=['gpu4020'],preserve_existing_reservations=True,consume_reservation=False,controller_admission_changed=False,
  scientific_settings_changed=False,final_release_authorized=False,control_root=str(a.R),runtime_root=str(a.P),
  source_sha256=a.SOURCE_SHA,controller_activation=a.ACTIVATION,normal_execution_authorization=a.AUTHORIZATION,node_exclusion=a.NODE,
  gateway_files=source_files(),reviewer_publication={a.REVIEWER:a.REVIEWER_SHA,a.FAILURE:a.FAILURE_SHA},**a.proof_refs(v))
 require(all(v.get(k)==value for k,value in expected.items()),'exact new typed root continuation authorization required')
 require(re.fullmatch('[1-9][0-9]*',v.get('controller_job_id','')),'controller job missing')
 for rel,h in {**v['gateway_files'],**a.DEPENDENCIES,CONTROLLER:CONTROLLER_SHA,IDENTITY:IDENTITY_SHA}.items():e.watch(rel,h)
 for proof in (*a.proof_refs(v).values(),a.ACTIVATION,a.AUTHORIZATION,a.NODE):e.ref(proof)
 require(e.ref(a.NODE).get('status')=='reviewed_for_future_explicit_requests','node exclusion not approved')
 ind=e.ref(v['independent_review'])
 require(ind.get('schema')=='formal_main_v2' and ind.get('kind')=='spatial_cuda_continuous_admission_independent_CPU_review'
  and ind.get('status')=='passed_CPU_review' and ind.get('blockers')==[] and ind.get('files')==v['gateway_files'],'independent current-source CPU review required')
 e.unchanged();return v,e
def controller_owner(root,state,snapshot,auth):
 control=state['autonomous_training_v1'];work=Path(root)/'results/formal_main_v2/autonomous_training/run_v1'
 ownerpath=a.direct(work/'owner.json');lease=a.direct(work/'controller.lease.lock')
 before=a.stable(ownerpath);owner=json.loads(ownerpath.read_bytes())
 require(a.stable(ownerpath)==before,'controller owner changed while reading')
 require(owner.get('version')=='cti-autonomous-training-controller-v1' and owner.get('owner_id')==control.get('owner_id')
  and owner.get('activation_sha256')==a.ACTIVATION['sha256'] and owner.get('coordinator_job_id')==auth['controller_job_id']
  and owner.get('lease')=='fcntl_flock_held_for_process_lifetime' and owner.get('lock')==str(lease),'controller owner identity differs')
 require(owner.get('hostname')==snapshot['rows'][auth['controller_job_id']]['node'],'controller owner hostname differs')
 require(lease.is_file(),'controller lease missing')
 with lease.open('rb') as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:pass
  else:
   fcntl.flock(f,fcntl.LOCK_UN);raise ValueError('controller lease is not held')
 require(a.stable(ownerpath)==before,'controller owner changed during lease check')
 return {'path':ownerpath.relative_to(root).as_posix(),**before,'owner':owner,'lease_confirmed_held':True}
def capacity_gate(c,d,state,snapshot,auth,e):
 require('pending_submission' in state and state['pending_submission'] is None,'unresolved global pending')
 jobs=state['registered_jobs'];ids=[str(j['job_id']) for j in jobs]
 require(len(ids)==len(set(ids)) and all(re.fullmatch('[1-9][0-9]*',x) for x in ids),'registry IDs invalid')
 require(set(snapshot['rows'])==set(ids) and set(snapshot['queue'])<=set(ids),'all registered accounting required')
 control=state.get('autonomous_training_v1',{})
 require(control.get('activation')==a.ACTIVATION and control.get('activation_sha256')==a.ACTIVATION['sha256']
  and control.get('controller_job_id')==auth['controller_job_id'],'controller identity differs')
 require(control.get('root_submission_hold') is None,'root hold active')
 reserved=control.get('reserved_GPU_slots',0)
 require(type(reserved) is int and 0<=reserved<=8,'reservation count invalid')
 if reserved:e.ref(control.get('reservation_root_record'))
 caps=c.capacity(jobs,snapshot,auth['controller_job_id'])
 require(not caps['unknown'] and not caps['findings'],'unknown/inconsistent scheduler: '+json.dumps(caps))
 require(len(caps['occupied'])+reserved+1<=8,'no unreserved GPU capacity; never consume Spatial reservation')
 require(a.PAIR not in caps['active_pairs'],'pair already active')
 cpus=[str(j['job_id']) for j in jobs if type(j.get('gpus')) is int and j['gpus']==0 and snapshot['rows'][str(j['job_id'])]['gpus']==0]
 require(auth['controller_job_id'] in cpus and snapshot['rows'][auth['controller_job_id']]['status']=='RUNNING','running controller CPU0 unconfirmed')
 for job in jobs:
  jid=str(job['job_id']);d.check_observed_identity(job,snapshot['rows'][jid],snapshot['queue'].get(jid),c.TERMINAL)
 for job in a.history(state):
  row=snapshot['rows'][job['job_id']]
  require(all(row.get(k)==job[k] for k in ('status','exit_code','elapsed_seconds','gpus')),'retained actual allocation differs')
 require(a.PAIR in control.get('blocked_pairs',{}),'expected retained exception block absent')
 return caps,cpus
def sbatch_argv(plan,ref):
 inv=plan['invocation'];raw=canonical(inv);h=sha(raw);token='cti-spatial-continuous-v1:'+ref['sha256']
 require(inv['segment_end']==5000 and inv['argv'][-1:] == ['--resume'] and plan['wrapper']==str(a.S/a.SLURM),'wrong continuation execution')
 exports='ALL,SOURCE_ROOT='+str(a.S)+',INVOCATION='+str(a.P/plan['invocation_relative'])+',INVOCATION_SHA256='+h
 return ['sbatch','--parsable','--no-requeue','--time=48:00:00','--exclude=gpu4020','--chdir='+str(a.P),'--output='+str(a.P/'results/slurm/%x_%j.out'),'--error='+str(a.P/'results/slurm/%x_%j.err'),'--comment='+token,'--export='+exports,plan['wrapper']],raw,h,token
def parse_ack(result,ids):
 require(result.returncode==0,'sbatch outcome uncertain')
 m=re.fullmatch(r'([1-9][0-9]*)(?:;[A-Za-z0-9_.-]+)?\n?',result.stdout)
 require(m is not None,'ambiguous sbatch ACK');jid=m.group(1);require(jid not in ids,'old job ID ACK');return jid
class Gateway:
 """Transaction layout derived from reviewed CUDA gateway c97b6610; no loop."""
 def __init__(self,root,c,d,slurm,science,io,authorization,ref,auth_evidence):
  self.root=Path(root);self.c=c;self.d=d;self.slurm=slurm;self.science=science;self.io=io;self.auth=authorization;self.ref=ref;self.e=auth_evidence
  self.path=self.root/a.STATE;self.audit=self.root/'results/formal_main_v2/spatial_continuous_admissions/3043399'/ref['sha256']
 def cas(self,state):
  self.c.atomic_json(self.path,state,self.expected);self.expected=self.c.file_sha(self.path)
 def job(self,jid,plan,invsha,argv,token):
  inv=plan['invocation']
  return dict(job_id=jid,name='cti-formal',experiment='formal_main_v2',mode='train',stage_key=a.STAGE,suite='libero_spatial',
   visual_tokens=64,training_seed=23,segment_end=5000,status='SUBMITTED',gpus=1,source_root=str(a.S),source_sha256=a.SOURCE_SHA,
   run_root=str(a.P/a.OUT),invocation=plan['invocation_relative'],invocation_sha256=invsha,submitted_utc=inv['registered_utc'],
   purpose='Root one-time continuous continuation after reviewed original-target CUDA recovery',
   continuous_admission={**copy.deepcopy(inv['continuous_admission']),'actual_sbatch_argv':argv,'request_token':token},
   startup_recovery=dict(kind='cuda_recovered_continuation_scheduler_metadata',version=a.VERSION,phase='continuous_after_original_target_recovery',
    authorization=self.ref,request_token=token,actual_sbatch_argv=argv))
 def run(self,*,submit=False):
  lock=self.path.parent/'.writer.lock';require(lock.is_file(),'shared lock must already exist')
  with self.c.exclusive_lock(lock):
   self.expected=self.c.file_sha(self.path);state=self.c.read_json(self.path);baseline=copy.deepcopy(state)
   require(self.c.file_sha(self.path)==self.expected,'state changed during read')
   require(not self.audit.exists(),'previous request footprint exists; no reattempt')
   snap=self.slurm.observe(state['registered_jobs']);caps,cpus=capacity_gate(self.c,self.d,state,snap,self.auth,self.e)
   owner=controller_owner(self.root,state,snap,self.auth)
   plan=self.science.prepare(state,self.auth,self.ref);argv,raw,invsha,token=sbatch_argv(plan,self.ref)
   require(not (self.root/plan['invocation_relative']).exists(),'unregistered published invocation; hold')
   live=self.io.preflight(plan);self.science.e.unchanged();self.e.unchanged()
   fresh=self.slurm.observe(state['registered_jobs']);caps,cpus=capacity_gate(self.c,self.d,state,fresh,self.auth,self.e)
   require(controller_owner(self.root,state,fresh,self.auth)==owner,'controller ownership changed')
   require(state==baseline and self.c.file_sha(self.path)==self.expected,'state drift before pending')
   result=dict(schema='formal_main_v2',kind='cuda_continuous_admission_preflight',version=a.VERSION,status='read_only_verified_not_submitted',
    authorization=self.ref,pair_key=a.PAIR,full_registered_jobs=state['registered_jobs'],scheduler_observation=fresh,capacity=caps,confirmed_CPU0=cpus,
    reserved_slots_preserved=state['autonomous_training_v1'].get('reserved_GPU_slots',0),original_history=plan['prior_jobs'],historical_GPU_seconds=a.HISTORICAL_SECONDS,
    invocation_relative=plan['invocation_relative'],invocation_sha256=invsha,invocation=plan['invocation'],actual_sbatch_argv=argv,
    server_preflight=live,controller_owner=owner,state_sha256=self.expected,read_evidence_sha256={**self.science.e.hashes,**self.e.hashes},controller_block_cleared=False)
   if not submit:return result
   self.audit.mkdir(parents=True,exist_ok=False);record(self.audit/'preflight.json',result)
   pending=dict(schema='formal_main_v2',kind='cuda_continuous_admission_pending',version=a.VERSION,stage_key=a.STAGE,pair_key=a.PAIR,
    status='prepared_before_invocation_publication',authorization=self.ref,request_token=token,invocation=plan['invocation_relative'],
    invocation_sha256=invsha,actual_sbatch_argv=argv,target_updates=5000,requested_gpus=1,retry_permitted=False,audit_relative=self.audit.relative_to(self.root).as_posix())
   state['pending_submission']=pending;self.cas(state)
   try:
    immutable(self.root/plan['invocation_relative'],raw);self.io.publish(plan,raw,immutable)
    # Checkpoint/source inputs are rechecked after publication, before sbatch.
    self.io.recheck(plan)
    self.science.e.unchanged();self.e.unchanged()
    require(self.c.file_sha(self.path)==self.expected,'CAS drift before sbatch')
    answer=self.slurm.submit(argv)
    record(self.audit/'sbatch_result.json',dict(returncode=answer.returncode,stdout=answer.stdout,stderr=answer.stderr,actual_sbatch_argv=argv))
    jid=parse_ack(answer,{str(j['job_id']) for j in state['registered_jobs']})
    pending.update(status='submitted_identifier_observed',known_job_id=jid);self.cas(state)
    job=self.job(jid,plan,invsha,argv,token);jobs=state['registered_jobs']+[job]
    observation=self.slurm.observe(jobs)
    corroboration=self.d.corroborate_new_job(self.slurm,job,observation)
    postcaps=self.d.reconcile_submission(self.c,jobs,observation,job,token,self.auth['controller_job_id'],corroboration)
    require(len(postcaps['occupied'])+state['autonomous_training_v1'].get('reserved_GPU_slots',0)<=8,'post-submit reservation capacity differs')
    require(controller_owner(self.root,state,observation,self.auth)==owner,'controller ownership changed after ACK')
    record(self.audit/'submission_identity.json',dict(observation=observation,corroboration=corroboration))
    record(self.root/f'results/formal_main_v2/submissions/{jid}.json',job)
    state['registered_jobs'].append(job);state['pending_submission']=None
    state['current_round_cost']['registered_jobs']=sum(j.get('experiment')=='formal_main_v2' for j in state['registered_jobs'])
    tracking=state['formal_main_progress']['parallel_execution']['pair_tracking']
    require(a.PAIR in tracking,'pair tracking absent')
    tracking[a.PAIR].update(active_job_id=jid,segment_target=5000,continuous_admission=self.ref)
    state['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(caps['occupied'])+1
    require(state['registered_jobs'][:-1]==baseline['registered_jobs'],'historical registry mutated')
    require(state['autonomous_training_v1']==baseline['autonomous_training_v1'],'controller/reservation/block mutation')
    self.cas(state)
    record(self.audit/'committed.json',dict(status='submitted_once',job=job,state_sha256=self.expected,automatic_retry=False,
      reservations_consumed=False,controller_admission_changed=False))
    return dict(status='submitted_once',job=job,state_sha256=self.expected)
   except BaseException as exc:
    try:record(self.audit/'failed_transaction.json',dict(status='stopped_no_automatic_retry',error_type=type(exc).__name__,error=str(exc),state_sha256=self.c.file_sha(self.path)))
    except BaseException:pass
    raise
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--authorization',required=True);p.add_argument('--authorization-sha256',required=True)
 p.add_argument('--gateway-sha256',required=True);p.add_argument('--submit',action='store_true');p.add_argument('--root-reviewed-submit',action='store_true');args=p.parse_args()
 require(Path.cwd().resolve()==a.R,'only server control root');require(sha(Path(__file__).read_bytes())==args.gateway_sha256,'gateway SHA differs')
 require(args.submit==args.root_reviewed_submit,'two explicit submit flags required')
 ref={'path':args.authorization,'sha256':args.authorization_sha256};auth,e=validate_authorization(a.R,ref)
 c=load(a.R/CONTROLLER,CONTROLLER_SHA,'_continuous_controller');d=load(a.R/IDENTITY,IDENTITY_SHA,'_continuous_identity')
 print(json.dumps(Gateway(a.R,c,d,c.Slurm(),a.Science(a.R),a.NativeIO(),auth,ref,e).run(submit=args.submit),sort_keys=True))
if __name__=='__main__':main()
