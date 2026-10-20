"""Independent read-only audit of four actual registered development requests. No GPU result access."""
from pathlib import Path
from types import SimpleNamespace
import json,hashlib,sys,os,importlib.util,traceback,time,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/dispatch_independent_20261020T1530';B='results/formal_main_v2/preflight/heartbeat_20261020T2330'
sys.dont_write_bytecode=True;checks=[];reads={}
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No process/network/Slurm')
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  writing=isinstance(args[1],str) and any(x in args[1] for x in 'wax+') or isinstance(args[2],int) and bool(args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
  if writing and D not in p.parents:raise RuntimeError('Private audit writes only')
  if p.suffix in ('.pt','.pth','.bin','.safetensors','.ckpt','.init','.pkl','.pickle','.pruned_init') or any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts):raise RuntimeError('No tensors or sealed initial values')
  if '/downstream/development/' in str(p) and p.suffix in ('.json','.jsonl','.npz'):raise RuntimeError('No development result reads during dispatch audit')
sys.addaudithook(guard)
def rd(rel,pin=None):
 p=Path(rel);p=p if p.is_absolute() else R/p;b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert pin is None or h==pin,(str(p),h);assert str(p) not in reads or reads[str(p)]==h;reads[str(p)]=h;return b
def js(rel,pin=None):return json.loads(rd(rel,pin))
def rf(ref):return js(ref['path'],ref['sha256'])
def ck(name,value):assert value,name;checks.append(name)
def dump(name,value):
 p=D/name;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return dict(path=p.relative_to(R).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(rel,pin,name):
 p=R/rel;raw=rd(p,pin);sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;exec(compile(raw,str(p),'exec'),m.__dict__);return m
def fields(raw):
 out={}
 for token in raw.split():
  if '=' in token:
   k,v=token.split('=',1);assert k not in out;out[k]=v
 return out
def main():
 t0=time.perf_counter();cpu=time.process_time()
 report=js(B+'/dispatch_root_report.json','82a65bd598a35cbaa49afeca1259c8b2ca39f20ca237fd282dd534c13546f8bf');prior=js('.local/nonLong64_development_independent_20261020T1530/post_readiness/post_readiness_independent_review.json','abc083c9d0fb7503299f80b1ee914e420160346399b1d563eba3cd00d7777bca')
 g=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','dispatch_audit_gw')
 c=load(g.CONTROLLER,g.CONTROLLER_SHA,'dispatch_audit_ctl')
 expected=[('libero_spatial_k64_seed17','3050870'),('libero_spatial_k64_seed41','3050890'),('libero_object_k64_seed17','3050901'),('libero_object_k64_seed41','3050916')]
 ck('four_exact_requests',[(x['group_key'],x['job_id']) for x in report['submissions']]==expected and len({x[0] for x in expected})==len({x[1] for x in expected})==4)
 ck('800_planned_zero_accepted',report['new_planned_trials']==800 and report['new_GPU_jobs']==4 and report['new_completed_trials']==0 and report['status']=='all_selected_requests_registered_once' and not report['scientific_settings_changed'] and not report['final_release'])
 inv=js(g.INVENTORY,g.INVENTORY_SHA);ck('173_frozen_inventory',len(inv['files'])==173)
 for root in [R,S]:
  for rel,pin in inv['files'].items():rd(root/rel,pin)
 state_raw=rd('results/experiment_supervisor/state.json');state=json.loads(state_raw);(D/'state_observed.json').write_bytes(state_raw)
 owner=js('results/formal_main_v2/autonomous_training/run_v1/owner.json');results=[]
 for row in report['submissions']:
  key=row['group_key'];jid=row['job_id'];pr=next(x for x in prior['plans'] if x['group_key']==key);ar=row['authorization'];a,e,plan,science,prepared=g.validate_authorization(R,ar);token='cti-downstream-gateway-v1:'+ar['sha256']
  ck(key+'_same_audited_plan',ar==pr['authorization'] and a['plan']==pr['effective_plan'] and a['scientific_plan']==pr['scientific_plan'] and a['runtime_readiness']==pr['readiness'] and a['prepared_invocation']==pr['prepared_invocation'])
  ck(key+'_same_scope',row['suite']==pr['suite'] and row['budget']==pr['budget']==64 and row['seed']==pr['seed'] and row['method_ids']==pr['methods'] and row['planned_trials']==row['unique_initial_states_per_suite']*2==200 and row['completed_trials_accepted']==0 and row['scientific_terminal_acceptance_pending'] and not row['automatic_retry'])
  raw=rd(row['invocation']['path'],row['invocation']['sha256']);ck(key+'_actual_R_P_prepared_same',raw==rd(P/row['invocation']['path'],row['invocation']['sha256'])==rd(a['prepared_invocation']['path'],a['prepared_invocation']['sha256']) and json.loads(raw)==prepared)
  ack=rf(row['exact_original_ACK']);fail=rf(row['original_accounting_delay']);rec=rf(row['root_reconciliation']);pre=rf(rec['original_preflight']);job=rf(row['submission']);ad=Path(row['exact_original_ACK']['path']).parent;comm=js(ad/'committed.json');observed=js(ad/'submitted_job_observation.json')
  ck(key+'_ACK_known_original_id',g.parse_ack(SimpleNamespace(**{k:ack[k] for k in ['returncode','stdout','stderr']}),{str(x['job_id']) for x in pre['registered_jobs']})==jid and ack['stderr']=='')
  ck(key+'_original_delay_not_resubmitted',fail['error']=='post-submit accounting incomplete' and fail['status']=='stopped_requires_root_reconciliation_no_retry' and fail['automatic_retry'] is False and rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0 and rec['automatic_retry'] is False and rec['original_ACK']==row['exact_original_ACK'] and rec['original_failure']==row['original_accounting_delay'])
  pb=rec['pending_before'];ck(key+'_pending_bound_to_original_ACK',pb['status']=='submitted_identifier_observed' and pb['known_job_id']==jid and pb['authorization']==ar and pb['request_token']==token and pb['requested_gpus']==1 and not pb['automatic_retry'])
  bundle=dict(plan=plan,invocation=prepared,invocation_bytes=raw);argv=g.submission_argv(bundle,token)
  ck(key+'_exact_original_sbatch_argv',argv==ack['actual_sbatch_argv']==pb['actual_sbatch_argv']==pre['actual_sbatch_argv']==job['downstream_gateway']['actual_sbatch_argv'])
  ck(key+'_frozen_resources',plan['resources']==g.RESOURCES and '--no-requeue' in argv and '--exclude=gpu4020' in argv and '--gres=gpu:l40:1' in argv and '--time=04:00:00' in argv)
  rebuilt=g.Gateway(R,c,None,None,None,a,ar,e)._job(jid,bundle,token,argv)
  ck(key+'_job_exact_original_factory',rebuilt==job==rec['job']==comm['job'])
  ck(key+'_original_science_deployment',job['mode']=='development' and job['method_ids']==pr['methods'] and job['scientific_plan']==pr['scientific_plan'] and job['action_execution_contract']==pr['action_execution_contract'] and job['runtime_readiness']==pr['readiness'] and job['gpus']==1 and not job['resume'] and job['prior_job_ids']==[])
  before_jobs=pre['registered_jobs'];obs0=pre['scheduler_observation'];caps0=c.capacity(before_jobs,obs0,a['controller_job_id'])
  ck(key+'_preflight_all_mode_capacity_recomputed',caps0==pre['capacity'] and not caps0['unknown'] and not caps0['findings'] and len(caps0['occupied'])<8 and set(obs0['rows'])=={str(j['job_id']) for j in before_jobs})
  ck(key+'_preflight_no_duplicate_target',all(str(j['job_id'])!=jid and j.get('stage_key')!=job['stage_key'] and not(j.get('suite')==row['suite'] and j.get('mode')=='development' and bool(set(j.get('method_ids',[]))&set(pr['methods']))) for j in before_jobs))
  for j in before_jobs:g.check_observed_identity(j,obs0['rows'][str(j['job_id'])],obs0['queue'].get(str(j['job_id'])),c.TERMINAL)
  jobs=before_jobs+[job];caps=g.reconcile_submission(c,jobs,rec['scheduler'],job,token,a['controller_job_id'],rec['scontrol_corroboration'])
  ck(key+'_reconciliation_all_mode_capacity_recomputed',caps==rec['capacity'] and not caps['unknown'] and not caps['findings'] and len(caps['occupied'])<=8 and jid in caps['occupied'])
  ck(key+'_recorded_controller_owner_lease',rec['controller_owner']==owner and rec['lifecycle_lease_held'] and owner['owner_id']==state['autonomous_training_v1']['owner_id'] and str(owner['coordinator_job_id'])==a['controller_job_id']=='3034538' and rec['scheduler']['rows']['3034538']['status']=='RUNNING' and rec['scheduler']['rows']['3034538']['gpus']==0)
  detail=rec['actual_scontrol_detail'];f=fields(detail['stdout']);ck(key+'_real_scontrol_command',detail['argv']==['scontrol','show','job','-o',jid] and detail['returncode']==0 and not detail['stderr'])
  wanted=dict(JobId=jid,JobName='cti-formal-downstream',Comment=token,Partition='L40',Requeue='0',Restarts='0',TimeLimit='04:00:00',ExcNodeList='gpu4020',TresPerNode='gres:gpu:l40:1',NumCPUs='7',MinMemoryNode='64G',NumTasks='1',Account='p_p15016',QOS='cpu-500_core-l40-8_card-a800-8_card',WorkDir=str(P))
  for k,v in wanted.items():ck(key+'_actual_allocation_'+k,f[k]==v)
  ck(key+'_actual_queue_identity',f['JobState']==rec['scheduler']['rows'][jid]['status']==row['observed_status_at_reconciliation'] and f['NodeList']!='gpu4020')
  ck(key+'_committed_exactly_once',comm['status']=='submitted_once_reconciled_after_accounting_delay' and comm['root_reconciliation']==row['root_reconciliation'] and comm['request_token']==token and comm['reservation_consumed'] and not comm['automatic_retry'] and observed['job_id']==jid and observed['request_token']==token and observed['observation']==rec['scheduler'] and observed['capacity']==caps)
  ck(key+'_reservation_identity',rec['exact_reservation_consumed']==a['root_reservation'] and not rec['final_release_authorized']);rf(a['root_reservation'])
  consumed=state['autonomous_training_v1']['downstream_reservations_consumed'][ar['sha256']];ck(key+'_registered_consumption',consumed==dict(job_id=jid,reservation=a['root_reservation'],request_token=token))
  matches=[j for j in state['registered_jobs'] if str(j['job_id'])==jid];ck(key+'_current_registry_unique',len(matches)==1 and sum(j.get('stage_key')==job['stage_key'] for j in state['registered_jobs'])==1)
  variable={'status','elapsed_seconds','exit_code','node','allocation'};ck(key+'_current_registered_identity_unchanged',{k:v for k,v in matches[0].items() if k not in variable}=={k:v for k,v in job.items() if k not in variable})
  ck(key+'_pending_not_stranded',state.get('pending_submission') is None or state['pending_submission'].get('known_job_id')!=jid)
  for name,pin in pre['read_evidence_sha256'].items():rd(name,pin)
  e.unchanged()
  results.append(dict(group_key=key,job_id=jid,exact_original_ACK=row['exact_original_ACK'],original_accounting_delay=row['original_accounting_delay'],root_reconciliation=row['root_reconciliation'],preflight_GPU_occupancy=len(caps0['occupied']),reconciled_GPU_occupancy=len(caps['occupied']),planned_trials=200,new_trials_accepted=0,stage='development',checkpoint_and_scientific_plan_unchanged=True,original_pending_and_ACK_reconciled=True,resubmissions=0))
 for p,pin in reads.items():
  if p!=str(R/'results/experiment_supervisor/state.json'):ck('stable_'+p,hashlib.sha256(Path(p).read_bytes()).hexdigest()==pin)
 dump('read_evidence_sha256.json',reads)
 out=dump('independent_review.json',dict(schema='formal_main_v2',kind='actual_four64_development_dispatch_independent_review',status='passed',reviewer='/root/devplans_audit_20261020_1418',root_dispatch=dict(path=B+'/dispatch_root_report.json',sha256='82a65bd598a35cbaa49afeca1259c8b2ca39f20ca237fd282dd534c13546f8bf'),checks=checks,check_count=len(checks),source=dict(path=Path(__file__).relative_to(R).as_posix(),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),submissions=results,total_planned_trials=800,new_accepted_trials=0,new_submissions_by_auditor=0,actual_GPU_results_read=False,controller_lease_reprobed=False,state_observation_sha256=hashlib.sha256(state_raw).hexdigest(),state_Slurm_Git_modified=False,final_release=False,scientific_settings_changed=False,CPU_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-t0,limitations=['Read-only recorded dispatch/registration evidence review; no scheduler polling or GPU-result acceptance.','Controller lifetime lease is attested by the root locked reconciliation evidence; independent audit does not acquire or alter it.'],blockers=[]))
 print(json.dumps(dict(status='passed',report=out,check_count=len(checks))))
if __name__=='__main__':
 try:main()
 except BaseException as ex:dump('failure_v1.json',dict(error_type=type(ex).__name__,error=str(ex),traceback=traceback.format_exc(),checks=checks,production_modified=False));raise
