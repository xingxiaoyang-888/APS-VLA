from pathlib import Path
from types import SimpleNamespace
import ast,copy,hashlib,importlib.util,json,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
OUT=R/'.local/spatial588_ack_independent_20261020T2253'
HELP='.local/reconcile_spatial588_3054201_20261020T2253.py'
HP='8a4c04313d0134330b9c18663e8b98a5aa330ef7fbf9cf1654f3209c74b482ba'
AUTH='d0143bc88b855ad9f4d6b6008e8373272d55c953d36bba88fbd8840a1090f7d5'
AR={'path':'results/formal_main_v2/execution/spatial588_pre_dispatch_v1/submission_authorization_v2.json','sha256':AUTH}
STATE='182fd8474eb0919f094e9266ca4af487e6f356da34dbbac41e1d291cb6ced55b'
DG=R/'results/formal_main_v2/downstream_gateway'/AUTH
checks=[];watched={}
def hbytes(b):return hashlib.sha256(b).hexdigest()
def check(label,test):
 if not test: raise AssertionError(label)
 checks.append(label)
def readbytes(p,pin=None):
 p=Path(p);b=p.read_bytes();actual=hbytes(b)
 if pin is not None:check('sha256:'+str(p),actual==pin)
 watched[str(p)]={'sha256':actual,'bytes':len(b)}
 return b
def js(p,pin=None):return json.loads(readbytes(p,pin))
def ref(p):
 p=Path(p);return {'path':p.relative_to(R).as_posix(),'sha256':hbytes(p.read_bytes())}
def load(rel,pin,name):
 path=R/rel;readbytes(path,pin)
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def write(name,obj):
 data=(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
 with (OUT/name).open('xb') as f:f.write(data)
 return ref(OUT/name)
raw=readbytes(R/HELP,HP);src=raw.decode();tree=ast.parse(src)
calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
check('no_FrozenPlan_reference',not any(isinstance(n,ast.Name) and n.id=='FrozenPlan' or isinstance(n,ast.Attribute) and n.attr=='FrozenPlan' for n in ast.walk(tree)))
check('no_submit_run_or_subprocess_call',not any(x.endswith(('.submit','.run','.Popen','.check_call','.check_output')) for x in calls))
for call in ['g.parse_ack','g.validate_authorization','g.submission_argv','gateway._job','scheduler.observe','g.corroborate_new_job','g.reconcile_submission','c.atomic_json']:
 check('one_exact_call:'+call,calls.count(call)==1)
ac=next(n for n in ast.walk(tree) if isinstance(n,ast.Call) and ast.unparse(n.func)=='c.atomic_json')
check('atomic_json_exact_expected_SHA',any(k.arg=='expected_sha' and ast.unparse(k.value)=='before' for k in ac.keywords))
check('exclusive_shared_writer_lock',"with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock')" in src)
check('original_ACK_record_not_overwritten',"g.record(D/'sbatch_result.json'" not in src)
check('state_hash_guard_exact',STATE in src)
check('no_new_submission_calls_in_receipts',src.count("'submission_calls_this_reconciliation':0")==3)
check('reconcile_before_registry_append',src.index('g.reconcile_submission(')<src.index("s['registered_jobs'].append(job)"))
check('unique_ACK_before_pending_clear',src.index('g.parse_ack(')<src.index("s['pending_submission']=None"))
check('reservation_consumed_once_after_observe',src.index('scheduler.observe(')<src.index("ctl.setdefault('downstream_reservations_consumed',{})[AUTH]"))
check('cost_once_per_registered_identity',"sum(observed['rows'][str(j['job_id'])]['elapsed_seconds']*observed['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')" in src)
check('no_legacy_cost_addition',not any(isinstance(n,ast.AugAssign) for n in ast.walk(tree)))
check('preserve_failures_and_hold',"'original_failure_retained':True" in src and "['global_release_created'] is False" in src)
g=load('scripts/ops/formal_action_deployment_posttraining_spatial588_v1/gateway.py','aba5868a8dc4e480262177785b2e62123d014046624f37924248721a9575c99c','ack_audit_gateway')
c=load(g.CONTROLLER,g.CONTROLLER_SHA,'ack_audit_controller')
s=js(R/'results/experiment_supervisor/state.json',STATE)
pre=js(DG/'preflight.json','77de2bf6f02d5ea8ca7629a286898105f5c0358c66e2b397717f64ea318254b1')
ack=js(DG/'sbatch_result.json','cba65b7776348747bc6dfa62f4b336643fac38f880e1e6a375df0dfc3b25f52f')
failure=js(DG/'failed_transaction.json','18897d313b1460cf14bbef535171090ff3a72bd29adf03018a65bd02ec1525ff')
pending=s['pending_submission'];token='cti-downstream-gateway-v1:'+AUTH
check('exact_pending_ACK_identity',pending['status']=='submitted_identifier_observed' and pending['known_job_id']=='3054201' and pending['authorization']==AR and pending['automatic_retry'] is False and pending['request_token']==token)
check('only_original_accounting_delay',failure['error']=='post-submit accounting incomplete' and failure['state_sha256']==STATE and failure['automatic_retry'] is False)
check('all_registry_ids_unique',len(s['registered_jobs'])==len({str(j['job_id']) for j in s['registered_jobs']}))
check('job_not_registered',all(str(j['job_id'])!='3054201' for j in s['registered_jobs']))
check('immutable_preflight_registry_exact',pre['registered_jobs']==s['registered_jobs'])
check('argv_identity_exact',ack['actual_sbatch_argv']==pending['actual_sbatch_argv']==pre['actual_sbatch_argv'])
check('original_ACK_parses_uniquely',g.parse_ack(SimpleNamespace(**{k:ack[k] for k in ['returncode','stdout','stderr']}),{str(j['job_id']) for j in s['registered_jobs']})=='3054201')
auth,e,plan,science,prepared=g.validate_authorization(R,AR)
ctl=s['autonomous_training_v1']
check('one_original_reservation_unconsumed',ctl['reserved_GPU_slots']==1 and ctl['reservation_root_record']==auth['root_reservation'] and AUTH not in ctl.get('downstream_reservations_consumed',{}))
check('no_duplicate_committed_or_job_file',not (DG/'committed.json').exists() and not (R/'results/formal_main_v2/submissions/3054201.json').exists())
inv=readbytes(R/plan['invocation_relative'],pending['invocation_sha256'])
check('exact_original_invocation_R_P_prepared',inv==readbytes(P/plan['invocation_relative'])==readbytes(R/auth['prepared_invocation']['path']))
before_pending=copy.deepcopy(s);before_pending['pending_submission']=None
check('original_preflight_state_reconstructs',hbytes(c.canonical(before_pending)+b'\n')==pre['state_sha256'])
check('preflight_auth_plan_prepared_exact',pre['status']=='read_only_checks_passed_not_submitted' and pre['authorization']==AR and pre['plan']==auth['plan'] and pre['scientific_plan']==auth['scientific_plan'] and pre['prepared_invocation']==auth['prepared_invocation'])
check('preflight_invocation_and_plan_digest_exact',pre['invocation_relative']==plan['invocation_relative']==pending['invocation'] and pre['invocation_sha256']==pending['invocation_sha256'] and pending['plan_sha256']==plan['plan_sha256'])
check('preflight_229_374_no_missing',len(pre['runtime_preflight']['checked_files'])==229 and len(pre['read_evidence_sha256'])==374 and pre['runtime_preflight']['missing_publications']==[])
for rel,pin in pre['read_evidence_sha256'].items():e.watch(rel,pin);readbytes(R/rel,pin)
for absolute,row in pre['runtime_preflight']['checked_files'].items():
 q=g.no_links(Path(absolute));check('P_runtime_metadata:'+absolute,q.is_relative_to(P) and g.stable(q)==row)
ready=e.ref(auth['runtime_readiness'])
publication={**plan['publish_files'],**ready['runtime_publication_files'],auth['runtime_readiness']['path']:auth['runtime_readiness']['sha256']}
for rel,pin in publication.items():check('R_P_publication:'+rel,hbytes(readbytes(R/rel))==hbytes(readbytes(P/rel))==pin)
bundle={'plan':plan,'invocation':prepared,'invocation_bytes':inv}
check('pure_argv_reconstruction_matches_ACK',g.submission_argv(bundle,token)==ack['actual_sbatch_argv'])
gateway=g.Gateway(R,c,None,None,None,auth,AR,e)
job=gateway._job('3054201',bundle,token,ack['actual_sbatch_argv'])
check('job_row_exact_unique_identity',str(job['job_id'])=='3054201' and job['experiment']=='formal_main_v2')
check('post_readiness_exact',js(R/'.local/spatial_gateway_independent_20261020T2253/post_readiness_independent_review.json','8eb2e5b90395ee22d1528699008d5ed21b45ecf6e37a5592661a60a757837554')['authorization']==AR)
e.unchanged()
check('state_unchanged_no_write',hbytes((R/'results/experiment_supervisor/state.json').read_bytes())==STATE)
before=write('original_state_snapshot.json',s)
pr=write('reconstructed_registered_job.json',job)
readproof=write('read_only_evidence.json',{'checks':checks,'watched_files':watched,'original_preflight':ref(DG/'preflight.json'),'P_runtime_metadata_checked':229,'original_R_evidence_checked':374,'publication_files':len(publication),'no_Slurm_queries':True})
report={'schema':'formal_main_v2','kind':'Spatial588_known_ACK_reconciliation_independent_review','status':'passed','reviewed_by':'independent','helper':ref(R/HELP),'job_id':'3054201','authorization':AR,'original_ACK':ref(DG/'sbatch_result.json'),'original_preflight':ref(DG/'preflight.json'),'original_failure':ref(DG/'failed_transaction.json'),'original_pending_state_sha256':STATE,'original_state_snapshot':before,'reconstructed_job':pr,'read_only_evidence':readproof,'checks_passed':len(checks),'blockers':[],'source_preflight_reused_not_replanned':True,'new_FrozenPlan_created':False,'new_GPU_submissions':0,'Slurm_queries':0,'state_mutations':0,'P_mutations':0,'Git_operations':0,'root_execution_performed':False,'reservation_unconsumed_at_review':True,'new_scheduling_authorization':False,'scope':'Static transaction audit plus exact existing ACK/pending/original preflight and complete R/P read-only metadata checks. Root must freshly corroborate real job 3054201 against all registered jobs under writer lock before CAS. This report does not claim registration or current Slurm state.','required_root_checks':['Keep unique original ACK; never resubmit.','Run pinned helper once with exact pending-state CAS; real Slurm observe/corroborate/reconcile must pass.','Consume only existing reservation and append exact job once; retain all failures and cost once.','If root helper fails any immutable evidence or accounting check, preserve pending/ACK and diagnose; no automatic retry.'],'final_release':False,'retained_compatible_legacy_trials':12,'remaining_current_trials':588,'historical_GPU_seconds':395,'scientific_results_admitted':0,'utc':datetime.now(timezone.utc).isoformat()}
rp=write('independent_review.json',report)
print(json.dumps({'status':'passed','report':rp,'checks':len(checks),'new_GPU_submissions':0,'Slurm_queries':0}))
