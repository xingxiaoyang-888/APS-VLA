"""ROOT-ONLY DRAFT: one exact independently ready k64s23 development dispatch.
Uses the original gateway lifecycle. Never retry or clear pending on any failure.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0349'
G=R/'scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py';PIN='873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p,pin,name):
 if sha(p)!=pin:raise ValueError('pinned code changed '+str(p))
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def main(argv=None):
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--suite',choices=['Spatial','Object'],required=True)
 for key in ('authorization','post-readiness-review'):
  ap.add_argument('--'+key,required=True);ap.add_argument('--'+key+'-sha256',required=True)
 ap.add_argument('--root-reviewed-source-sha256',required=True);ap.add_argument('--execute-exact-dispatch',action='store_true',required=True);a=ap.parse_args(argv)
 if not(a.execute_exact_dispatch and sha(Path(__file__))==a.root_reviewed_source_sha256 and Path.cwd().resolve()==R):raise ValueError('exact reviewed root dispatch approval required')
 g=load(G,PIN,'root_k64s23_dispatch_gateway');c=load(R/g.CONTROLLER,g.CONTROLLER_SHA,'root_k64s23_dispatch_controller');require=g.require;e=g.Evidence(R)
 suite='libero_'+a.suite.lower();allowed=g.SCOPED_DEVELOPMENT_PLANS[suite];C=str(Path(allowed['path']).parent)
 ar={'path':a.authorization,'sha256':a.authorization_sha256};pr={'path':a.post_readiness_review,'sha256':a.post_readiness_review_sha256}
 require(ar['path']==C+'/submission_authorization.json','exact pair authorization path required');post=e.ref(pr)
 require(post.get('schema')==g.ROUND and post.get('kind')=='exact_k64s23_post_readiness_independent_review' and post.get('status')=='passed' and post.get('suite')==suite and not post.get('blockers') and post.get('authorization')==ar and post.get('actual_full_P_wrapper_verifications')==1,'exact independent actual-P post readiness missing')
 receipt_ref={'path':str((B/(a.suite+'64s23_runtime_readiness_root.json')).relative_to(R)),'sha256':sha(B/(a.suite+'64s23_runtime_readiness_root.json'))};receipt=e.ref(receipt_ref)
 require(receipt.get('schema')==g.ROUND and receipt.get('kind')=='exact_k64s23_runtime_readiness_root' and receipt.get('status')=='passed_exact_pre_execution_checks_pending_live_capacity' and receipt.get('suite')==suite and receipt.get('authorization')==ar and receipt.get('actual_full_P_wrapper_verifications')==1 and receipt.get('state_unchanged') is True and receipt.get('new_GPU_submissions')==[],'root exact actual-P receipt missing')
 out=B/(a.suite+'64s23_dispatch');require(not out.exists(),'dispatch transaction already exists; reconcile, never re-enter')
 started=False
 try:
  with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
   sp=R/g.STATE;before=sha(sp);state=c.read_json(sp);ctl=state['autonomous_training_v1']
   require(state['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None,'prior pending/reservation/hold unresolved')
   require(ar['sha256'] not in ctl.get('downstream_reservations_consumed',{}),'exact request already consumed')
   auth,ev,plan,science,prepared=g.validate_authorization(R,ar)
   require(post.get('effective_plan')==auth['plan'] and post.get('prepared_invocation')==auth['prepared_invocation'] and post.get('explicit_source_control')==auth['explicit_source_control'],'post readiness exact plan/bridge/prepared mismatch')
   require(receipt['readiness']==auth['runtime_readiness'] and receipt['reservation']==auth['root_reservation'] and receipt['prepared_invocation']==auth['prepared_invocation'],'root receipt exact authorization mismatch')
   projected=copy.deepcopy(state);projected['autonomous_training_v1']['reserved_GPU_slots']=1;projected['autonomous_training_v1']['reservation_root_record']=auth['root_reservation']
   observed=c.Slurm().observe(state['registered_jobs']);caps,cpus,live=g.capacity_gate(c,projected,observed,auth,plan)
   bundle=g.FrozenPlan(R,auth,ev,plan,science,prepared).prepare(live)
   ready=ev.ref(auth['runtime_readiness']);bundle['readiness_files']={**ready['runtime_publication_files'],auth['runtime_readiness']['path']:auth['runtime_readiness']['sha256']}
   g.NativeIO(R).preflight(bundle);ev.unchanged();e.unchanged();require(sha(sp)==before,'state drift before reservation')
   out.mkdir(exist_ok=False);started=True;g.immutable(out/'state_before.json',sp.read_bytes())
   g.record(out/'reservation_intent.json',{'schema':g.ROUND,'status':'root_exact_request_reservation_intent','authorization':ar,'post_readiness_review':pr,'root_readiness_receipt':receipt_ref,'reservation':auth['root_reservation'],'observation':observed,'capacity':caps,'state_before':before,'automatic_retry':False})
   c.atomic_json(sp,projected,expected_sha=before)
   g.record(out/'reservation.json',{'schema':g.ROUND,'status':'one_slot_reserved_for_exact_authorization','authorization':ar,'reservation':auth['root_reservation'],'state_before':before,'state_after':sha(sp),'utc':datetime.now(timezone.utc).isoformat(),'automatic_retry':False})
  command=[sys.executable,'-B',str(G),'--authorization',ar['path'],'--authorization-sha256',ar['sha256'],'--gateway-sha256',PIN]
  checked=subprocess.run(command,cwd=R,capture_output=True,timeout=360)
  g.immutable(out/'preflight_stdout.json',checked.stdout);g.immutable(out/'preflight_stderr.txt',checked.stderr)
  require(checked.returncode==0,'original gateway preflight failed; reservation retained for explicit reconciliation')
  check=json.loads(checked.stdout);require(check.get('status')=='read_only_checks_passed_not_submitted' and len(check['capacity']['occupied'])<8,'original exact preflight did not pass')
  result=subprocess.run(command+['--submit','--root-reviewed-submit'],cwd=R,capture_output=True,timeout=360)
  g.immutable(out/'submit_stdout.json',result.stdout);g.immutable(out/'submit_stderr.txt',result.stderr)
  require(result.returncode==0,'original gateway submission stopped; pending/ACK must be reconciled, no retry')
  value=json.loads(result.stdout);require(value.get('status')=='submitted_once','original gateway did not report one exact submission')
  g.record(out/'completion.json',{'schema':g.ROUND,'status':'submitted_once','suite':suite,'authorization':ar,'post_readiness_review':pr,'root_readiness_receipt':receipt_ref,'job_id':value['job']['job_id'],'stage_key':value['job']['stage_key'],'state_sha256':value['state_sha256'],'automatic_retry':False,'root_script_sha256':sha(Path(__file__))})
  print(json.dumps({'suite':suite,'job_id':value['job']['job_id'],'status':'submitted_once','completion':str((out/'completion.json').relative_to(R)),'completion_sha256':sha(out/'completion.json')}))
 except BaseException as error:
  if started:
   failure={'status':'stopped_requires_root_reconciliation_no_retry','error_type':type(error).__name__,'error':str(error),'traceback':traceback.format_exc(),'state_sha256':sha(R/g.STATE),'automatic_retry':False}
   for key in ('stdout','stderr'):
    val=getattr(error,key,None)
    if val is not None:failure[key]=val.decode(errors='replace') if isinstance(val,bytes) else str(val)
   g.record(out/'failure.json',failure)
  raise
if __name__=='__main__':main()
