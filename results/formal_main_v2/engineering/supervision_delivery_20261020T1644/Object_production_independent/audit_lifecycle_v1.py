from pathlib import Path
from types import ModuleType
import os,sys,hashlib,json,time,traceback,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;OUT=D/'lifecycle';sys.dont_write_bytecode=True
C=R/'.local/object_bridge_production_20261020T1644/revision03/package/control.py';PIN='09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f';RESULTS=[]
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No actual scheduler/process/network permitted')
 if event=='open':
  name,mode,flags=args
  if isinstance(name,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(name));p=p if p.is_absolute() else Path.cwd()/p
   writing=isinstance(mode,str) and any(x in mode for x in 'wax+') or isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
   if writing and OUT not in p.parents:raise RuntimeError('CPU fixtures only under own audit:'+str(p))
   if p.suffix.lower() in ('.pt','.pth','.ckpt','.safetensors','.pkl','.init','.pruned_init') or any('sealed' in x.lower() for x in p.parts):raise RuntimeError('No payload/weights')
 if event in ('os.remove','os.rmdir','os.rename','os.replace'):
  for name in args[:2] if event in ('os.rename','os.replace') else args[:1]:
   if isinstance(name,(str,bytes,os.PathLike)):
    p=Path(os.fsdecode(name));p=p if p.is_absolute() else Path.cwd()/p
    if OUT not in p.parents:raise RuntimeError('Mutation outside private fixture denied')
sys.addaudithook(guard)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p,pin):
 assert sha(p)==pin;m=ModuleType('ind_lifecycle_'+p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def write(name,value):
 p=OUT/name
 with p.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
def run(name,fn,*args):
 b=f.Box(OUT/'fixtures'/str(len(RESULTS)))
 try:fn(b,*args)
 except BaseException as e:
  RESULTS.append({'test':name,'passed':False,'error':str(e),'traceback':traceback.format_exc()});raise
 RESULTS.append({'test':name,'passed':True,'simulated_submit_calls':b.submits,'simulated_scontrol_calls':b.controls})
def main():
 global f
 OUT.mkdir(exist_ok=False);t=time.monotonic();c=load(C,PIN);g=c.gateway_module()
 author=R/'.local/action_downstream_gateway_0809/test_gateway.py';f=load(author,'8c7cbb12afbbfd5b69252a38741de6c482a06b17c2160c969df46d06a2dd398f');f.g=g
 # Original transaction fixture and fault tests now exercise the candidate-derived
 # Gateway/NativeIO namespace. FakeScience/FakeSlurm are explicit stand-ins;
 # no production authorization, state, or Slurm interaction occurs.
 run('read_only_no_writes',f.test_check_only_zero_write_and_all_registered_query)
 run('pending_before_publication_ACK_registration',f.test_success_pending_precedes_publication_preserves_history)
 for fault in ['eight','missing','unknown','cpu_gpu','duplicate_pair','pending','reservation','hold','terminal_drift','active_stage','old_invocation']:run('preflight '+fault,f.test_preflight_blocked_no_publication,fault)
 run('missing_writer_lock_no_creation',f.test_missing_writer_lock_no_creation)
 for raw,rc in [('901\nextra',0),('901\n',1),('100\n',0),('901 \n',0),('',0)]:run('uncertain_ACK '+repr((raw,rc)),f.test_uncertain_ack_never_repeats_and_keeps_pending,raw,rc)
 run('timeout_raw_output_preserved',f.test_timeout_raw_output_preserved)
 for point in ['prepare','publish','submit']:run('CAS '+point,f.test_cas_drift_does_not_overwrite_or_retry,point)
 for fault in ['missing','wrong_queue_token','sacct_conflict']:run('post_ACK '+fault,f.test_acknowledged_but_unverified_stays_known_pending,fault)
 run('exact_scontrol_corroboration',f.test_new_job_without_queue_needs_actual_scontrol)
 for field in ['JobId=901','JobName=cti-formal-downstream','Comment=cti-downstream-gateway-v1:']:run('scontrol_bad '+field,f.test_scontrol_mismatch_blocks_commit,field)
 run('active_queue_actual_token',f.test_active_accounting_empty_queue_token_real_shape)
 run('missing_token_rejected',f.test_active_both_comments_absent_is_not_admission)
 run('fixed_one_GPU_norequeue_scope',f.test_command_scope_no_scientific_args_modified)
 q=load(R/'.local/action_gateway_consumers_independent_0809/test_gateway_independent.py','4997bc4f3acfb1124876acb4730340f6f81d3d31b1f7add56d6bfdc139a2cc46');q.f=f;q.g=g;q.c=f.c
 for fault in ['cpu_missing','cpu_unknown','queue_foreign','queue_status','foreign_cpu_unobserved','foreign_CPU_claim','formal_legacy_int_zero','reservation_other']:run('extra_denial '+fault,q.test_independent_preflight_denial_is_zero_write,fault)
 run('publication_failure_keeps_pending',q.test_publication_failure_keeps_prepared_pending_and_all_history)
 run('requested_GPU_counts_pending',q.test_new_CPU_sized_pending_GPU_request_counts_as_slot)
 for fault in ['name','unknown','queue_absent_with_wrong_scontrol']:run('post_ACK_extra '+fault,q.test_post_ack_failure_keeps_known_pending_not_committed,fault)
 run('CAS_preserves_external_controller',q.test_CAS_after_ack_preserves_external_controller_field)
 run('running_request_GPU_slot',q.test_running_request_actual_zero_not_exempted_as_CPU)
 write('report.json',{'status':'passed_independent_CPU_lifecycle_faults','candidate_sha256':PIN,'cases':len(RESULTS),'results':RESULTS,'source_provenance':{'original_fixture':{'path':author.relative_to(R).as_posix(),'sha256':sha(author)},'prior_independent_faults':{'path':'.local/action_gateway_consumers_independent_0809/test_gateway_independent.py','sha256':'4997bc4f3acfb1124876acb4730340f6f81d3d31b1f7add56d6bfdc139a2cc46'}},'actual_Slurm_calls':0,'actual_GPU':False,'production_state_writes':False,'science_and_authorization_standins':True,'candidate_gateway_operational_functions_exercised':True,'CPU_wall_seconds':time.monotonic()-t})
 print(json.dumps({'status':'passed_independent_CPU_lifecycle_faults','cases':len(RESULTS),'actual_Slurm_calls':0}))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  if OUT.exists():write('failure.json',{'error':str(e),'traceback':traceback.format_exc(),'results':RESULTS,'actual_Slurm_calls':0})
  raise
