from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T1038'
AR={'path':'configs/experiments/formal_main_v2_spatial_cuda_continuous_3043399_v2.json','sha256':'1cdb14995f275d03557d86be1b565f615a005d911b994ce8c17a3d229e989411'}
AD='results/formal_main_v2/spatial_continuous_admissions/3043399/'+AR['sha256']
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel,pin=None):
 p=R/rel
 if pin:assert h(p)==pin
 return json.loads(p.read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
g=load('scripts/ops/formal_spatial_cuda_continuous_admission_v2/gateway.py','4f552abcc05d72ff84975e360ea28a624a4744febb8518e2fc71839fe47d5864','reconcileSpatial0238')
c=load(g.CONTROLLER,g.CONTROLLER_SHA,'reconcileSpatial0238ctl');d=load(g.IDENTITY,g.IDENTITY_SHA,'reconcileSpatial0238identity')
auth,e=g.validate_authorization(R,AR)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/g.a.STATE;before=h(statepath);state=rd(g.a.STATE);old=copy.deepcopy(state);pending=state['pending_submission']
 assert pending['known_job_id']=='3044479' and pending['status']=='submitted_identifier_observed' and pending['retry_permitted'] is False
 assert pending['authorization']==AR and pending['audit_relative']==AD and pending['request_token']=='cti-spatial-continuous-v1:'+AR['sha256']
 assert pending['pair_key']==g.a.PAIR and pending['target_updates']==5000 and pending['requested_gpus']==1 and pending['version']==g.a.VERSION
 pre=rd(AD+'/preflight.json','b45dfaef2ba1fd3e75ff4ff79b7c7f364f46c87617edadb5a9a3930dbb58bbdd')
 ack=rd(AD+'/sbatch_result.json','aee4f36256ed22b40f5190c69fd6d6ec51dfe27f27a9662c6296cdbb4cdbe8c2')
 fail=rd(AD+'/failed_transaction.json','4620a58b0b67dfd2e6663d2a464c5c7af00f945d6a6c63fb675964f9806cdb85')
 assert fail['error']=='post-submit accounting incomplete' and fail['status']=='stopped_no_automatic_retry'
 assert ack['returncode']==0 and ack['stdout']=='3044479\n' and ack['stderr']=='' and ack['actual_sbatch_argv']==pending['actual_sbatch_argv']==pre['actual_sbatch_argv']
 assert pre['authorization']==AR and pre['pair_key']==g.a.PAIR and pre['reserved_slots_preserved']==state['autonomous_training_v1']['reserved_GPU_slots']==0
 assert pre['historical_GPU_seconds']==11958 and pre['controller_block_cleared'] is False
 assert [j['job_id'] for j in pre['full_registered_jobs']]==[j['job_id'] for j in state['registered_jobs']]
 variable={'status','elapsed_seconds','exit_code','node','allocation'}
 for a,b in zip(pre['full_registered_jobs'],state['registered_jobs']):
  assert {k:v for k,v in a.items() if k not in variable}=={k:v for k,v in b.items() if k not in variable}
 invrel=pending['invocation'];assert invrel==pre['invocation_relative']=='results/formal_main_v2/invocations/libero_spatial_train_k64_seed23_attempt05.json'
 raw=(R/invrel).read_bytes();assert raw==(P/invrel).read_bytes()==g.canonical(pre['invocation'])
 invsha=h(R/invrel);assert invsha==pending['invocation_sha256']==pre['invocation_sha256']=='6b940dc389e5ce6fbb0ae642aa4c388f33d39daae4f7f7fc76840a14b384479c'
 plan=dict(invocation=pre['invocation'],invocation_relative=invrel,wrapper=str(g.a.S/g.a.SLURM))
 argv,expectedraw,expectedsha,token=g.sbatch_argv(plan,AR)
 assert argv==pending['actual_sbatch_argv'] and expectedraw==raw and expectedsha==invsha and token==pending['request_token']
 assert g.a.PAIR in state['autonomous_training_v1']['blocked_pairs']
 assert not (R/'results/formal_main_v2/submissions/3044479.json').exists() and not (R/AD/'committed.json').exists()
 gateway=g.Gateway(R,c,d,None,None,None,auth,AR,e);job=gateway.job('3044479',plan,invsha,argv,token)
 assert not any(str(j['job_id'])=='3044479' for j in state['registered_jobs'])
 jobs=state['registered_jobs']+[job];scheduler=c.Slurm(timeout=45);snapshot=scheduler.observe(jobs)
 corroboration=d.corroborate_new_job(scheduler,job,snapshot)
 detail_argv=['scontrol','show','job','-o','3044479'];detail=scheduler.run(detail_argv)
 assert detail.returncode==0 and not detail.stderr.strip()
 assert 'JobState='+snapshot['rows']['3044479']['status'] in detail.stdout.split()
 caps=d.reconcile_submission(c,jobs,snapshot,job,token,auth['controller_job_id'],corroboration)
 owner=g.controller_owner(R,state,snapshot,auth);assert owner==pre['controller_owner']
 assert len(caps['occupied'])<=8 and '3044479' in caps['occupied'] and snapshot['rows']['3044479']['status'] in ['RUNNING','PENDING','CONFIGURING']
 assert snapshot['rows']['3034538']['status']=='RUNNING' and snapshot['rows']['3034538']['gpus']==0
 for field,value in [('JobId','3044479'),('JobName','cti-formal'),('WorkDir',str(P)),('Comment',token),('Requeue','0'),('Restarts','0'),('ExcNodeList','gpu4020'),('TimeLimit','2-00:00:00'),('Command',str(g.a.S/g.a.SLURM)),('StdOut',str(P/'results/slurm/cti-formal_3044479.out')),('StdErr',str(P/'results/slurm/cti-formal_3044479.err'))]:assert field+'='+value in detail.stdout.split()
 inventory=rd(g.a.INVENTORY,g.a.INV_SHA);assert len(inventory['files'])==173
 for rel,pin in inventory['files'].items():assert h(R/rel)==h(g.a.S/rel)==pin
 e.unchanged();assert h(statepath)==before
 state['registered_jobs'].append(job);state['pending_submission']=None
 tracking=state['formal_main_progress']['parallel_execution']['pair_tracking'];assert g.a.PAIR in tracking
 tracking[g.a.PAIR].update(active_job_id='3044479',segment_target=5000,continuous_admission=AR)
 state['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(caps['occupied'])
 seconds=sum(snapshot['rows'][str(j['job_id'])]['elapsed_seconds']*snapshot['rows'][str(j['job_id'])]['gpus'] for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 state['current_round_cost'].update(registered_jobs=sum(j.get('experiment')=='formal_main_v2' for j in state['registered_jobs']),allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 expected=copy.deepcopy(old);expected['registered_jobs'].append(job);expected['pending_submission']=None;expected['current_round_cost']=copy.deepcopy(state['current_round_cost'])
 expected['formal_main_progress']['parallel_execution']['pair_tracking'][g.a.PAIR]=copy.deepcopy(tracking[g.a.PAIR]);expected['formal_main_progress']['parallel_execution']['registered_requested_active_GPU_jobs']=len(caps['occupied'])
 assert state==expected and state['autonomous_training_v1']==old['autonomous_training_v1']
 receipt=dict(schema='formal_main_v2',status='exact_original_ACK_job_reconciled',utc=datetime.now(timezone.utc).isoformat(),pending_before=pending,state_before_sha256=before,job=job,scheduler=snapshot,scontrol_corroboration=corroboration,actual_scontrol_detail=dict(argv=detail_argv,returncode=detail.returncode,stdout=detail.stdout,stderr=detail.stderr),capacity=caps,controller_owner=owner,original_preflight=ref(AD+'/preflight.json'),original_ACK=ref(AD+'/sbatch_result.json'),original_failure=ref(AD+'/failed_transaction.json'),all173_R_and_S_match=True,new_submissions=0,automatic_retry=False,reservations_consumed=False,controller_block_preserved=True,final_release_authorized=False)
 g.record(R/B/'Spatial3044479_pending_reconciliation.json',receipt)
 g.record(R/AD/'submission_identity.json',dict(observation=snapshot,corroboration=corroboration,actual_scontrol_detail=dict(argv=detail_argv,returncode=detail.returncode,stdout=detail.stdout,stderr=detail.stderr),root_pending_reconciliation=ref(B+'/Spatial3044479_pending_reconciliation.json')))
 g.record(R/'results/formal_main_v2/submissions/3044479.json',job)
 c.atomic_json(statepath,state,before)
 g.record(R/AD/'committed.json',dict(status='submitted_once_reconciled_after_accounting_delay',job=job,state_sha256=h(statepath),automatic_retry=False,reservations_consumed=False,controller_admission_changed=False,root_reconciliation=ref(B+'/Spatial3044479_pending_reconciliation.json')))
 print(json.dumps(dict(status='registered_original_job_no_resubmission',job_id='3044479',active_GPU_jobs=len(caps['occupied']),pending=None,GPU_hours=seconds/3600,receipt=ref(B+'/Spatial3044479_pending_reconciliation.json'))))
