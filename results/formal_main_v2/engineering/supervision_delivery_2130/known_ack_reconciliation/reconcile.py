"""One known-ack reconciliation only. Never sends a Slurm mutation."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
import argparse,copy,errno,fcntl,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=R/'.local/downstream_pending_reconcile_2130'
JOB='3043709';GATEWAY_SHA='8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a'
AUTH={'path':'results/formal_main_v2/execution/long_remaining16_action_v1_1827/k128_seed23/submission_authorization.json','sha256':'6e574361d66aaba7869b536082d9c605106bdaf2ec428f3ccb46ea986c8ef37a'}
INV='results/formal_main_v2/invocations/libero_10_development_ea4e52de3babd049_attempt01.json';INV_SHA='2bf41d87718038e41f35d52b90506a3e973a7270869278157fb953d8238a7f84'
AUDIT='results/formal_main_v2/downstream_gateway/'+AUTH['sha256'];OWNER='results/formal_main_v2/autonomous_training/run_v1/owner.json';OWNER_SHA='2ba2100d6f20e8a00f7853e193d1546b3d7c4195f174c75d54605ec504e33bc2';OWNER_ID='6b3beba5cdeb41df9d749b0b2054d485';LEASE='results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock'
PINS={'preflight.json':'48fbfc52f482a790d283a7e7f2033ec981771af748152a7092da4b9ed7a02f11','sbatch_result.json':'24cfb9362989ae65c5628b2ead90ae635db79ff997a5c9f144d2c43d44e124c2','failed_transaction.json':'e24132ccb84a72385d2346a8cc52f225a59770de197ef08c7d8c808a7aebb643'}
def require(v,m):
 if not v:raise ValueError(m)
def canon(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':')).encode()
def digest(b):return hashlib.sha256(b).hexdigest()
def load(p,pin,name):
 raw=p.read_bytes();require(digest(raw)==pin,'source SHA differs: '+str(p));sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(raw,str(p),'exec'),m.__dict__);return m

def dependencies():
 g=load(R/'scripts/ops/formal_action_deployment_v1/gateway.py',GATEWAY_SHA,'reconcile2130_gateway');c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'reconcile2130_controller')
 a,e,plan,science,inv=g.validate_authorization(R,AUTH)
 refs={}
 def read(rel,pin):
  row=g.stable(R/rel);require(row['sha256']==pin,'original evidence SHA differs');refs[rel]=row;return json.loads((R/rel).read_bytes())
 pre=read(AUDIT+'/preflight.json',PINS['preflight.json']);ack=read(AUDIT+'/sbatch_result.json',PINS['sbatch_result.json']);failure=read(AUDIT+'/failed_transaction.json',PINS['failed_transaction.json'])
 require(failure['error']=='post-submit accounting incomplete' and failure['automatic_retry'] is False,'different failure phase')
 raw=(R/a['prepared_invocation']['path']).read_bytes();require(digest(raw)==INV_SHA and json.loads(raw)==inv,'prepared invocation differs')
 for base in (R,P):require(g.stable(base/INV)['sha256']==INV_SHA,'published actual invocation differs')
 for n,h in pre['read_evidence_sha256'].items():e.watch(n,h)
 for n,h in inv['support_files'].items():require(g.stable(P/n)['sha256']==h,'actual runtime source differs')
 require(pre['plan']==a['plan'] and pre['scientific_plan']==a['scientific_plan'] and pre['prepared_invocation']==a['prepared_invocation'],'original preflight references differ')
 bundle=dict(plan=plan,invocation=inv,invocation_bytes=raw)
 token='cti-downstream-gateway-v1:'+AUTH['sha256'];argv=g.submission_argv(bundle,token)
 require(pre['request_token']==token and pre['actual_sbatch_argv']==argv==ack['actual_sbatch_argv'],'original argv/token differs')
 require(pre['invocation_relative']==INV and pre['invocation_sha256']==INV_SHA,'original preflight invocation differs')
 require(pre['status']=='read_only_checks_passed_not_submitted' and pre['legacy_refresh_called'] is False and pre['scientific_settings_changed'] is False,'invalid original preparation')
 require(not pre['capacity']['unknown'] and not pre['capacity']['findings'] and len(pre['capacity']['occupied'])<8,'original pre-submit capacity failed')
 require(g.parse_ack(SimpleNamespace(**{k:ack[k] for k in ('returncode','stdout','stderr')}),{str(j['job_id']) for j in pre['registered_jobs']})==JOB,'exact acknowledgement differs')
 runner=g.Gateway(R,c,None,None,None,a,AUTH,e);job=runner._job(JOB,bundle,token,argv)
 e.unchanged();return dict(g=g,c=c,auth=a,evidence=e,plan=plan,invocation=inv,bundle=bundle,preflight=pre,ack=ack,failure=failure,job=job,token=token,argv=argv,refs=refs)

def validate_state(state,ctx,owner):
 a=ctx['auth'];pre=ctx['preflight'];inv=ctx['invocation'];ctl=state.get('autonomous_training_v1',{});jobs=state['registered_jobs'];ids=[str(j['job_id']) for j in jobs]
 require(len(ids)==len(set(ids)) and JOB not in ids,'duplicate or already registered job')
 require(ids==[str(j['job_id']) for j in pre['registered_jobs']],'registered ID set/order changed since original preflight')
 mutable={'status','exit_code','elapsed_seconds','allocation','node'}
 for old,new in zip(pre['registered_jobs'],jobs):require({k:v for k,v in old.items() if k not in mutable}=={k:v for k,v in new.items() if k not in mutable},'historical job identity changed')
 expected=dict(schema='formal_main_v2',kind='formal_downstream_server_pending',version=ctx['g'].VERSION,status='submitted_identifier_observed',stage_key=inv['stage_key'],invocation=INV,invocation_sha256=INV_SHA,plan_sha256=ctx['plan']['plan_sha256'],authorization=AUTH,request_token=ctx['token'],actual_sbatch_argv=ctx['argv'],requested_gpus=1,utc=inv['registered_utc'],automatic_retry=False,audit_relative=AUDIT,known_job_id=JOB)
 require(state.get('pending_submission')==expected,'pending transaction differs; never clear unrelated pending')
 require(ctl.get('activation')==a['controller_activation'] and ctl.get('activation_sha256')==a['controller_activation']['sha256'] and ctl.get('controller_job_id')==a['controller_job_id']=='3034538','controller activation/job identity differs')
 require(ctl.get('owner_id')==owner.get('owner_id')==OWNER_ID and owner.get('coordinator_job_id')=='3034538' and owner.get('activation_sha256')==a['controller_activation']['sha256'],'owner identity differs')
 require(owner.get('lock')==str(R/LEASE) and owner.get('lease')=='fcntl_flock_held_for_process_lifetime','owner lease contract differs')
 require(ctl.get('root_submission_hold') is None,'root hold active')
 require(type(ctl.get('reserved_GPU_slots')) is int and ctl['reserved_GPU_slots']==1 and ctl.get('reservation_root_record')==a['root_reservation'],'exact owned Long reservation missing')
 require(AUTH['sha256'] not in ctl.get('downstream_reservations_consumed',{}),'authorization already consumed')
 require(not any(j.get('invocation')==INV or j.get('stage_key')==inv['stage_key'] for j in jobs),'stage/invocation already registered')
 return True

def lease_evidence(g):
 row=g.stable(R/OWNER);require(row['sha256']==OWNER_SHA,'controller owner file changed');owner=json.loads((R/OWNER).read_bytes());p=g.no_links(R/LEASE);require(p.is_file(),'lease file missing')
 with p.open('rb') as f:
  try:fcntl.flock(f,fcntl.LOCK_SH|fcntl.LOCK_NB)
  except BlockingIOError:held=True
  else:fcntl.flock(f,fcntl.LOCK_UN);held=False
 require(held,'controller lifetime exclusive lease not held')
 return owner,dict(owner_sha256=row['sha256'],owner=owner,lease_path=str(p),lease_inode=p.stat().st_ino,exclusive_lock_confirmed_contended=True)

def proposed_state(state,ctx,owner,snapshot,corroboration=None):
 validate_state(state,ctx,owner);g=ctx['g'];c=ctx['c'];jobs=[*state['registered_jobs'],ctx['job']]
 caps=g.reconcile_submission(c,jobs,snapshot,ctx['job'],ctx['token'],ctx['auth']['controller_job_id'],corroboration)
 require(snapshot['rows'][JOB]['gpus']==1 and snapshot['rows'][JOB]['node']=='gpu4001','known job allocation/node identity differs')
 cpu=snapshot['rows']['3034538'];require(cpu['status']=='RUNNING' and cpu['gpus']==0 and cpu['node']==owner['hostname'],'controller not actual RUNNING CPU0 on owner host')
 out=copy.deepcopy(state);out['registered_jobs'].append(copy.deepcopy(ctx['job']));out['pending_submission']=None
 cost=out.setdefault('current_round_cost',{});cost['registered_jobs']=sum(j.get('experiment')==g.ROUND for j in jobs);cost['allocated_gpu_seconds']=sum(snapshot['rows'][str(j['job_id'])]['elapsed_seconds']*snapshot['rows'][str(j['job_id'])]['gpus'] for j in jobs if j.get('experiment')==g.ROUND);cost['allocated_gpu_hours']=cost['allocated_gpu_seconds']/3600
 ctl=out['autonomous_training_v1'];ctl['reserved_GPU_slots']=0;ctl.setdefault('downstream_reservations_consumed',{})[AUTH['sha256']]=dict(job_id=JOB,reservation=ctx['auth']['root_reservation'],request_token=ctx['token'])
 out.setdefault('formal_main_progress',{}).setdefault('parallel_execution',{})['registered_requested_active_GPU_jobs']=len(caps['occupied'])
 # Whitelist exact writes; all current controller/owner/history fields survive.
 normalized=copy.deepcopy(out);normalized['registered_jobs']=copy.deepcopy(state['registered_jobs']);normalized['pending_submission']=copy.deepcopy(state['pending_submission']);normalized['current_round_cost']=copy.deepcopy(state.get('current_round_cost',{}));normalized['formal_main_progress']=copy.deepcopy(state.get('formal_main_progress',{}));normalized['autonomous_training_v1']['reserved_GPU_slots']=state['autonomous_training_v1']['reserved_GPU_slots'];normalized['autonomous_training_v1']['downstream_reservations_consumed']=copy.deepcopy(state['autonomous_training_v1'].get('downstream_reservations_consumed',{}))
 require(normalized==state,'unrelated state/controller change')
 before=copy.deepcopy(state.get('formal_main_progress',{}));after=copy.deepcopy(out['formal_main_progress']);after.get('parallel_execution',{}).pop('registered_requested_active_GPU_jobs',None);before.get('parallel_execution',{}).pop('registered_requested_active_GPU_jobs',None);require(before==after,'unrelated progress changed')
 cb={k:v for k,v in state.get('current_round_cost',{}).items() if k not in {'registered_jobs','allocated_gpu_seconds','allocated_gpu_hours'}};ca={k:v for k,v in cost.items() if k not in {'registered_jobs','allocated_gpu_seconds','allocated_gpu_hours'}};require(cb==ca,'unrelated cost fields changed')
 return out,caps

def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--candidate-sha256',required=True);ap.add_argument('--commit',action='store_true');ap.add_argument('--root-reviewed-reconcile',action='store_true');ap.add_argument('--output-name',required=True);args=ap.parse_args(argv)
 require(args.commit==args.root_reviewed_reconcile,'two explicit root commit flags required');require(Path.cwd().resolve()==R,'server control cwd required');require(digest(Path(__file__).read_bytes())==args.candidate_sha256,'candidate bytes differ');require(args.output_name and Path(args.output_name).name==args.output_name and args.output_name.endswith('.json'),'audit basename required');outpath=D/args.output_name;require(not outpath.exists(),'audit output already exists')
 ctx=dependencies();g,c=ctx['g'],ctx['c'];writer=g.no_links(R/'results/experiment_supervisor/.writer.lock');require(writer.is_file(),'existing shared writer lock missing')
 class QueryOnly(c.Slurm):
  def run(self,argv):require(argv and argv[0] in {'sacct','squeue','scontrol'},'scheduler mutation forbidden');return super().run(argv)
  def submit(self,argv):raise ValueError('sbatch forbidden in reconciliation')
 result={'schema':'formal_main_v2','kind':'known_ack_downstream_root_reconciliation','job_id':JOB,'candidate_sha256':args.candidate_sha256,'commit_requested':args.commit,'new_sbatch_calls':0,'scientific_results_claimed':False}
 try:
  with c.exclusive_lock(writer):
   before_sha=c.file_sha(R/g.STATE);state=c.read_json(R/g.STATE);require(c.file_sha(R/g.STATE)==before_sha,'state drift during read');owner,lease1=lease_evidence(g);validate_state(state,ctx,owner)
   require(not (R/AUDIT/'committed.json').exists() and not (R/AUDIT/'root_reconciliation_precommit_3043709.json').exists() and not (R/'results/formal_main_v2/submissions'/f'{JOB}.json').exists(),'prior registration/reconciliation publication exists; inspect manually')
   scheduler=QueryOnly();snapshot=scheduler.observe([*state['registered_jobs'],ctx['job']]);corroboration=g.corroborate_new_job(scheduler,ctx['job'],snapshot);proposal,caps=proposed_state(state,ctx,owner,snapshot,corroboration)
   owner2,lease2=lease_evidence(g);require(owner2==owner and lease2==lease1,'owner/lease changed during reconciliation');ctx['evidence'].unchanged();require(c.file_sha(R/g.STATE)==before_sha,'state drift before reconciliation CAS')
   result.update(status='passed_readonly_known_ack_reconciliation_not_committed',utc=datetime.now(timezone.utc).isoformat(),authorization=AUTH,plan=ctx['auth']['plan'],invocation={'path':INV,'sha256':INV_SHA},original_evidence=ctx['refs'],source_files={str(Path(__file__).relative_to(R)):args.candidate_sha256,'scripts/ops/formal_action_deployment_v1/gateway.py':GATEWAY_SHA,ctx['g'].CONTROLLER:ctx['g'].CONTROLLER_SHA},lease=lease2,state_before_sha256=before_sha,proposed_state_sha256=digest(canon(proposal)+b'\n'),job=ctx['job'],scheduler_observation=snapshot,scontrol_corroboration=corroboration,capacity=caps,pending_preserved_in_check_only=True,state_written=False)
   if args.commit:
    # Root only. No new Slurm request; original failure and pending evidence persist.
    g.record(R/AUDIT/'root_reconciliation_precommit_3043709.json',result)
    g.record(R/AUDIT/'submitted_job_observation.json',dict(job_id=JOB,request_token=ctx['token'],observation=snapshot,scontrol_corroboration=corroboration,capacity=caps,origin='root_known_ack_reconciliation',original_failure_sha256=PINS['failed_transaction.json']))
    g.record(R/'results/formal_main_v2/submissions'/f'{JOB}.json',ctx['job'])
    c.atomic_json(R/g.STATE,proposal,before_sha)
    after_sha=c.file_sha(R/g.STATE);require(after_sha==result['proposed_state_sha256'],'committed state bytes differ')
    g.record(R/AUDIT/'committed.json',dict(schema=g.ROUND,kind='formal_downstream_server_committed',status='submitted_once_reconciled_by_root',job=ctx['job'],state_sha256=after_sha,request_token=ctx['token'],reservation_consumed=True,automatic_retry=False,original_failure_sha256=PINS['failed_transaction.json'],new_sbatch_calls=0))
    result.update(status='known_existing_job_registered_by_root_reconciliation',state_written=True,state_after_sha256=after_sha,pending_preserved_in_check_only=False)
   g.record(outpath,result)
  print(json.dumps({'status':result['status'],'job_id':JOB,'state_written':result['state_written'],'new_sbatch_calls':0,'receipt':str(outpath.relative_to(R)),'receipt_sha256':g.stable(outpath)['sha256']},sort_keys=True))
 except BaseException as exc:
  if not outpath.exists():g.record(outpath,{**result,'status':'stopped_no_retry','error_type':type(exc).__name__,'error':str(exc),'current_state_sha256':c.file_sha(R/g.STATE)})
  raise
if __name__=='__main__':main()
