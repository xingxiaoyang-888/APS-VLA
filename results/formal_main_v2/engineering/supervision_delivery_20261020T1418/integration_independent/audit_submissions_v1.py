from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,os,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/integration_independent_20261020T1418'
checks=[];inputs={};started=time.perf_counter()
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect'):raise RuntimeError('No network/process/Slurm in independent audit')
 if event=='open':
  n,m,f=args
  if isinstance(n,(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(n));p=p if p.is_absolute() else Path.cwd()/p
   if any('sealed' in x.lower() or x.lower() in ('weights','checkpoints') for x in p.parts) or p.suffix.lower() in ('.pt','.pth','.bin','.safetensors','.ckpt','.pkl','.pickle','.init','.pruned_init'):raise RuntimeError('No weight/final values')
   w=isinstance(m,str) and any(c in m for c in 'wax+') or isinstance(f,int) and bool(f&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_APPEND|os.O_TRUNC))
   if w and D not in p.parents:raise RuntimeError('Private audit writes only')
sys.addaudithook(guard)
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(rel,pin=None,base=R):
 p=base/rel;assert p.is_file() and not p.is_symlink(),str(p);b=p.read_bytes();h=sha(b)
 assert pin is None or h==pin,(str(p),h,pin)
 if str(p) in inputs:assert inputs[str(p)]['sha256']==h,'Evidence drift '+str(p)
 inputs[str(p)]=dict(path=str(p),sha256=h,bytes=len(b));return b
def rd(rel,pin=None,base=R):return json.loads(raw(rel,pin,base))
def rr(r,base=R):return rd(r['path'],r['sha256'],base)
def ref(rel,base=R):b=raw(rel,base=base);return dict(path=rel,sha256=sha(b))
def test(n,v):assert v,n;checks.append(dict(name=n,status='passed'))
def out(name,v):
 p=D/name;b=(json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return dict(path=p.relative_to(R).as_posix(),sha256=sha(b),bytes=len(b))
def main():
 postref=dict(path='.local/devplans_independent_20261020T1418/post_readiness/post_readiness_independent_review.json',sha256='9e360d5a1c28348056a4ff8334584384cc3a19545229f28898dc6afa51475eb3')
 post=rr(postref);test('three_original_P_independent_verifications',post['status']=='passed' and post['actual_full_P_wrapper_verifications']==3 and post['Slurm_submissions']==0 and not post['actual_GPU_runtime_chain_verified'])
 state=rd('results/experiment_supervisor/state.json');auto=state['autonomous_training_v1'];f=state['formal_main_progress'];jobs=state['registered_jobs']
 test('no_final_opening',not f['test_opened'] and not f['global_release_created'] and f['completed_final_trials']==0)
 test('controller_identity',auto['controller_job_id']=='3034538' and auto['owner_id']=='6b3beba5cdeb41df9d749b0b2054d485')
 expected=['libero_spatial_k256_seed23','libero_spatial_k256_seed41','libero_object_k256_seed41'];test('three_clean_groups', [x['group_key'] for x in post['plans']]==expected)
 facts=[]
 for pp in post['plans']:
  group=pp['group_key'];ar=pp['authorization'];a=rr(ar);token='cti-downstream-gateway-v1:'+ar['sha256'];matches=[j for j in jobs if j.get('downstream_gateway',{}).get('request_token')==token]
  test(group+'_exact_one_job',len(matches)==1);j=matches[0];jid=str(j['job_id']);ad='results/formal_main_v2/downstream_gateway/'+ar['sha256']
  pref=rd(ad+'/preflight.json');ack=rd(ad+'/sbatch_result.json');committed=rd(ad+'/committed.json');rec=rr(committed['root_reconciliation']);failed=rd(ad+'/failed_transaction.json')
  plan=rr(a['plan']);science=rr(a['scientific_plan']);ready=rr(a['runtime_readiness']);prepared=rr(a['prepared_invocation']);reservation=rr(a['root_reservation']);invref=dict(path=j['invocation'],sha256=j['invocation_sha256']);inv=rr(invref);raw(invref['path'],invref['sha256'],P);submission=rd('results/formal_main_v2/submissions/'+jid+'.json')
  test(jid+'_single_use_development_authorization',a['maximum_attempts']==1 and not a['automatic_retry'] and a['controller_job_id']=='3034538' and not a['final_release_authorized_by_gateway'] and a['status']=='approved_for_exactly_one_registered_downstream_submission' and a['plan_arguments']['stage']=='development' and a['plan_arguments']['freeze_directory'] is None and a['plan_arguments']['profile_panel'] is None and a['plan_arguments']['stop_after'] is None)
  test(jid+'_same_reviewed_plans',a['plan']==pp['effective_plan'] and a['scientific_plan']==pp['scientific_plan'] and plan['plan_sha256']==pp['plan_sha256'] and a['runtime_readiness']==pp['readiness'] and a['prepared_invocation']==pp['prepared_invocation'])
  test(jid+'_same_prepared_R_P_invocation',inv==prepared==dict(plan['invocation'],registered_utc=prepared['registered_utc'],plan_sha256=plan['plan_sha256'],runtime_readiness=a['runtime_readiness']) and inv['stage']=='development' and inv['method_ids']==pp['methods'] and inv['suite']==pp['suite'] and not inv['resume'] and not inv['prior_job_ids'] and not inv['final_values_read_locally'] and not inv['scientific_settings_changed'])
  test(jid+'_same_readiness_and_both_reviews',ready['status']=='passed' and ready['expected_trials']==200 and ready['unique_development_initial_states']==100 and ready['allowed_stages']==['development'] and ready['method_ids']==pp['methods'] and ready['root_review']==pp['root_review'] and ready['independent_review']==pp['independent_review'] and not ready['final_evaluation_enabled'] and not ready['O2A_enabled'] and not ready['global_freeze_enabled'])
  for r in [ready['root_review'],ready['independent_review'],a['runtime_readiness'],a['plan'],a['scientific_plan'],inv['action_execution_contract']]:rr(r);raw(r['path'],r['sha256'],P)
  test(jid+'_original_ACK_and_delay_retained',ack['returncode']==0 and ack['stdout']==jid+'\n' and failed['error']=='post-submit accounting incomplete' and failed['status']=='stopped_requires_root_reconciliation_no_retry' and not failed['automatic_retry'] and ack['actual_sbatch_argv']==pref['actual_sbatch_argv'])
  for key,name in [('original_ACK','sbatch_result.json'),('original_failure','failed_transaction.json'),('original_preflight','preflight.json')]:test(jid+'_'+key,rec[key]==ref(ad+'/'+name))
  test(jid+'_no_resubmission',rec['status']=='exact_original_ACK_job_reconciled' and rec['new_submissions']==0 and not rec['automatic_retry'] and rec['pending_before']['known_job_id']==jid and rec['pending_before']['request_token']==token and rec['pending_before']['authorization']==ar and rec['pending_before']['invocation']==invref['path'] and rec['pending_before']['invocation_sha256']==invref['sha256'])
  test(jid+'_committed_original_job',committed['job']==rec['job']==submission and committed['request_token']==token and committed['reservation_consumed'] and committed['status']=='submitted_once_reconciled_after_accounting_delay')
  dynamic={'node','exit_code','status','allocation','elapsed_seconds'};test(jid+'_registry_immutable_identity',{k:v for k,v in j.items() if k not in dynamic}=={k:v for k,v in submission.items() if k not in dynamic})
  test(jid+'_unique_stage',sum(x.get('stage_key')==j['stage_key'] for x in jobs)==1 and sum(str(x['job_id'])==jid for x in jobs)==1)
  test(jid+'_slot_once_consumed',reservation['reserved_slots']==1 and reservation['capacity_limit_all_GPU_modes']==8 and reservation['stage_key']==inv['stage_key'] and reservation['authorization_path']==ar['path'] and rec['exact_reservation_consumed']==a['root_reservation'] and auto['downstream_reservations_consumed'][ar['sha256']]==dict(job_id=jid,request_token=token,reservation=a['root_reservation']))
  test(jid+'_owner_source_preserved',rec['lifecycle_lease_held'] and rec['all173_R_and_S_match'] and rec['unrelated_controller_fields_unchanged'] and not rec['final_release_authorized'] and rec['controller_owner']['owner_id']==auto['owner_id'])
  argv=ack['actual_sbatch_argv'];test(jid+'_single_GPU_original_command',argv.count('--no-requeue')==1 and '--gres=gpu:l40:1' in argv and '--comment='+token in argv and '--time=04:00:00' in argv and argv[-2]=='--wrap' and str(P/invref['path']) in argv[-1] and invref['sha256'] in argv[-1] and str(P/inv['wrapper']) in argv[-1])
  detail=rec['actual_scontrol_detail'];test(jid+'_captured_scheduler_identity',detail['returncode']==0 and detail['argv']==['scontrol','show','job','-o',jid] and 'JobId='+jid+' ' in detail['stdout'] and 'Comment='+token in detail['stdout'] and 'Requeue=0' in detail['stdout'] and 'Restarts=0' in detail['stdout'] and 'WorkDir='+str(P) in detail['stdout'])
  pre=pref['capacity'];postcap=rec['capacity'];test(jid+'_captured_capacity_valid',not pre['unknown'] and not pre['findings'] and not postcap['unknown'] and not postcap['findings'] and len(pre['occupied'])<8 and len(postcap['occupied'])<=8 and set(postcap['occupied'])==set(pre['occupied'])|{jid})
  test(jid+'_fresh_output_guard',pref['runtime_preflight']['output_exists'] is False and not pref['runtime_preflight']['missing_publications'] and pref['invocation_relative']==invref['path'] and pref['invocation_sha256']==invref['sha256'])
  facts.append(dict(group_key=group,job_id=jid,suite=pp['suite'],budget=pp['budget'],seed=pp['seed'],method_ids=pp['methods'],planned_trials=200,new_accepted_trials_claimed=0,authorization=ar,invocation=invref,root_reconciliation=committed['root_reconciliation'],submission=ref('results/formal_main_v2/submissions/'+jid+'.json'),preoccupied=len(pre['occupied']),postoccupied=len(postcap['occupied']),original_delay_preserved=True,duplicate_submission=False))
 inventory=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');test('inventory_exact173',len(inventory['files'])==173)
 for name,pin in inventory['files'].items():raw(name,pin);raw(name,pin,S)
 evidence=out('submission_check_evidence.json',dict(schema='formal_main_v2',checks=checks,input_refs=list(inputs.values()),new_scheduler_queries=0,state_read_once=True,shared_state_modified=False))
 report=out('submission_independent_review.json',dict(schema='formal_main_v2',kind='independent_actual_submission_review',status='passed',reviewer='/root/devplans_audit_20261020_1418',utc=datetime.now(timezone.utc).isoformat(),source=ref(str(Path(__file__).relative_to(R))),check_evidence=evidence,checks_passed=len(checks),jobs=facts,planned_trials=600,new_trials_accepted=0,new_scheduler_queries=0,new_GPU_seconds=0,new_GPU_jobs=0,state_Git_Slurm_modified=False,source173_R_S_unchanged=True,final_release=False,sealed_values_read=False,checkpoint_bytes_read=False,CPU_wall_seconds=time.perf_counter()-started,limitations=['Captured scheduler evidence only, no fresh polling.','Submission integrity only; terminal science is not accepted here.']))
 print(json.dumps(dict(status='passed',report=report,checks=len(checks),jobs=[x['job_id'] for x in facts])))
if __name__=='__main__':
 try:main()
 except Exception as e:
  out('submission_failure_v1.json',dict(error_type=type(e).__name__,error=str(e),traceback=traceback.format_exc(),checks=checks,production_modified=False,new_GPU_seconds=0));raise
