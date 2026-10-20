from pathlib import Path
from types import SimpleNamespace
import copy,hashlib,importlib.util,json,os,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');B=R/'results/formal_main_v2/preflight/heartbeat_20261021T0349';PIN='873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb';AUTH='79d22ee8370f95551c259894ad7deccffa7bebc4a1ffecab1c9d567d393cf855';JID='3053875'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def load(p,pin,name):
 assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
g=load(R/'scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py',PIN,'collectreconcilegateway');c=load(R/g.CONTROLLER,g.CONTROLLER_SHA,'collectreconcilecontroller');ar={'path':'results/formal_main_v2/execution/spatial64seed23_source_control_v1_20261020T1949/submission_authorization.json','sha256':AUTH}
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);assert before=='13ceb3c9789d93a42c63e7fdc10757744438b7cd51301e47f4527718da531c9a';s=read(sp);baseline=copy.deepcopy(s);pending=s['pending_submission'];D=R/pending['audit_relative']
 assert pending['status']=='submitted_identifier_observed' and pending['known_job_id']==JID and pending['authorization']==ar and pending['automatic_retry'] is False
 token='cti-downstream-gateway-v1:'+AUTH;assert pending['request_token']==token
 failure=read(D/'failed_transaction.json');assert failure['error']=='post-submit accounting incomplete' and failure['state_sha256']==before
 pre=read(D/'preflight.json');ack=read(D/'sbatch_result.json');assert pre['registered_jobs']==s['registered_jobs'] and pre['request_token']==token and ack['actual_sbatch_argv']==pending['actual_sbatch_argv']==pre['actual_sbatch_argv']
 assert g.parse_ack(SimpleNamespace(**{k:ack[k] for k in ['returncode','stdout','stderr']}),{str(j['job_id']) for j in s['registered_jobs']})==JID
 auth,e,plan,science,prepared=g.validate_authorization(R,ar);ctl=s['autonomous_training_v1'];assert ctl['reserved_GPU_slots']==1 and ctl['reservation_root_record']==auth['root_reservation'] and AUTH not in ctl.get('downstream_reservations_consumed',{})
 assert not (D/'committed.json').exists() and not (R/('results/formal_main_v2/submissions/'+JID+'.json')).exists()
 assert (R/plan['invocation_relative']).read_bytes()==(P/plan['invocation_relative']).read_bytes()==(R/auth['prepared_invocation']['path']).read_bytes() and h(R/plan['invocation_relative'])==pending['invocation_sha256']
 approved_before_pending=copy.deepcopy(s);approved_before_pending['pending_submission']=None
 assert hashlib.sha256(c.canonical(approved_before_pending)+b'\n').hexdigest()==pre['state_sha256']
 assert h(D/'preflight.json')=='82f9b835caa6e85f7ff23ce0607f1dcf3ec9b4584299e1c8c6ffcccbd9bd65c6'
 assert pre['status']=='read_only_checks_passed_not_submitted' and pre['authorization']==ar and pre['plan']==auth['plan'] and pre['scientific_plan']==auth['scientific_plan'] and pre['prepared_invocation']==auth['prepared_invocation']
 assert pre['invocation_relative']==plan['invocation_relative']==pending['invocation'] and pre['invocation_sha256']==pending['invocation_sha256'] and pending['plan_sha256']==plan['plan_sha256']
 assert pre['runtime_preflight']['missing_publications']==[] and len(pre['runtime_preflight']['checked_files'])==218 and len(pre['read_evidence_sha256'])==551
 for rel,pin in pre['read_evidence_sha256'].items():e.watch(rel,pin)
 for absolute,row in pre['runtime_preflight']['checked_files'].items():
  q=g.no_links(Path(absolute));assert q.is_relative_to(P) and g.stable(q)==row
 ready=e.ref(auth['runtime_readiness']);publications={**plan['publish_files'],**ready['runtime_publication_files'],auth['runtime_readiness']['path']:auth['runtime_readiness']['sha256']}
 for rel,pin in publications.items():assert h(g.no_links(R/rel))==h(g.no_links(P/rel))==pin
 # Reconcile the immutable original preflight proof; the fresh-submission planner correctly forbids replanning an existing invocation.
 bundle={'plan':plan,'invocation':prepared,'invocation_bytes':(R/auth['prepared_invocation']['path']).read_bytes()}
 assert g.submission_argv(bundle,token)==ack['actual_sbatch_argv']
 gateway=g.Gateway(R,c,c.Slurm(),None,None,auth,ar,e);job=gateway._job(JID,bundle,token,ack['actual_sbatch_argv'])
 scheduler=c.Slurm();observed=scheduler.observe([*s['registered_jobs'],job]);corroboration=g.corroborate_new_job(scheduler,job,observed)
 caps=g.reconcile_submission(c,[*s['registered_jobs'],job],observed,job,token,auth['controller_job_id'],corroboration)
 assert observed['rows'][JID]['status'] in c.TERMINAL|c.KNOWN_LIVE
 assert (JID in caps['occupied'])==(observed['rows'][JID]['status'] not in c.TERMINAL)
 e.unchanged();assert h(sp)==before
 g.record(D/'root_reconciled_submission_observation.json',{'schema':'formal_main_v2','job_id':JID,'request_token':token,'observation':observed,'scontrol_corroboration':corroboration,'capacity':caps,'original_failure_retained':True,'submission_calls_this_reconciliation':0,'state_before':before})
 g.record(R/('results/formal_main_v2/submissions/'+JID+'.json'),job)
 s['registered_jobs'].append(job);s['pending_submission']=None;ctl['reserved_GPU_slots']=0;ctl.setdefault('downstream_reservations_consumed',{})[AUTH]={'job_id':JID,'reservation':auth['root_reservation'],'request_token':token}
 cost=s.setdefault('current_round_cost',{});cost['registered_jobs']=sum(j.get('experiment')=='formal_main_v2' for j in s['registered_jobs']);cost['allocated_gpu_seconds']=sum(observed['rows'][str(j['job_id'])]['elapsed_seconds']*observed['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2');cost['allocated_gpu_hours']=cost['allocated_gpu_seconds']/3600;cost['final']=False
 s['formal_main_progress'].setdefault('parallel_execution',{})['registered_requested_active_GPU_jobs']=len(caps['occupied'])
 assert s['registered_jobs'][:-1]==baseline['registered_jobs'] and s['formal_main_progress']['completed_final_trials']==0 and s['formal_main_progress']['global_release_created'] is False
 beforectl=copy.deepcopy(baseline['autonomous_training_v1']);afterctl=copy.deepcopy(ctl)
 for k in ['reserved_GPU_slots','downstream_reservations_consumed']:beforectl.pop(k,None);afterctl.pop(k,None)
 assert beforectl==afterctl
 c.atomic_json(sp,s,expected_sha=before)
 receipt={'schema':'formal_main_v2','kind':'formal_downstream_server_committed','status':'submitted_once_reconciled_known_ack','job':job,'state_sha256':h(sp),'request_token':token,'reservation_consumed':True,'automatic_retry':False,'submitted_once_original_ACK':True,'submission_calls_this_reconciliation':0,'original_failure_retained':True,'utc':datetime.now(timezone.utc).isoformat()};g.record(D/'committed.json',receipt);g.record(B/'Spatial64s23_pending_reconciliation.json',receipt);print(json.dumps({'job_id':JID,'status':receipt['status'],'pending':None,'reserved_slots':0,'occupied':caps['occupied'],'new_submission_calls':0}))

 check=read(B/'Spatial64s23_runtime_readiness_root.json');post={'path':'.local/k64_seed23_bridges_independent_20261020T1949/post_readiness/Spatial/post_readiness_independent.json','sha256':'31ef1a9894d37d9a07d99351fc07121d0397fedcc6d7e119ae3df8f66bfcb8de'};assert h(R/post['path'])==post['sha256'] and read(R/post['path'])['authorization']==ar
 g.record(B/'Spatial64s23_dispatch'/'completion.json',{'schema':'formal_main_v2','status':'submitted_once','suite':'libero_spatial','authorization':ar,'post_readiness_review':post,'root_readiness_receipt':{'path':str((B/'Spatial64s23_runtime_readiness_root.json').relative_to(R)),'sha256':h(B/'Spatial64s23_runtime_readiness_root.json')},'job_id':JID,'stage_key':job['stage_key'],'state_sha256':h(sp),'automatic_retry':False,'root_script_sha256':h(Path(__file__)),'submitted_once_original_ACK':True,'submission_calls_this_reconciliation':0,'original_failure_retained':True,'reconciliation':{'path':str((B/'Spatial64s23_pending_reconciliation.json').relative_to(R)),'sha256':h(B/'Spatial64s23_pending_reconciliation.json')}})
