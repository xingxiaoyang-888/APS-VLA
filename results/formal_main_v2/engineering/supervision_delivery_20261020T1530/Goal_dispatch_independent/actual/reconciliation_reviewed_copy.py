"""Reconcile the one acknowledged held Goal probe. This source cannot submit a job."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,sys,fcntl
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2330/Goal_t0_dispatch';JID='3050711';PIN='016ddbdc5d638e6271debb124d305dfdd7ccd3ef3d5f9816ac9fe13f4c3a3dda'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
old=load('.local/goal_t0_dispatch_20261020T1530.py','45dc2e6483578c8f332820d03386ca0cc20f3b7736ec74ad50d2e46b4d538b5d','goal_original_dispatch_1530')
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','goal_reconcile_1530c')
g=load('scripts/ops/formal_action_deployment_v1/gateway.py','8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a','goal_reconcile_1530g')
def fields(text):
 # This fixed-name job has no whitespace in any field used below. ':' and '/' are legal scheduler keys.
 result={}
 for token in text.split():
  if '=' not in token:continue
  k,v=token.split('=',1);assert k not in result,('duplicate field',k);result[k]=v
 return result
def verify(v,token,held):
 for k,x in {'JobId':JID,'JobName':old.NAME,'Comment':token,'Requeue':'0','Restarts':'0','TimeLimit':'00:30:00','Partition':'L40','Account':'p_p15016','QOS':'cpu-500_core-l40-8_card-a800-8_card','ExcNodeList':'gpu4020','TresPerNode':'gres:gpu:l40:1','Command':str(P/old.BASE/'source/candidate.slurm'),'WorkDir':str(P)}.items():assert v.get(k)==x,(k,v.get(k),x)
 if held:assert v['JobState']=='PENDING' and v['Reason']=='JobHeldUser' and v['RunTime']=='00:00:00'
 else:assert v['JobState'] in ['PENDING','RUNNING','CONFIGURING'] and v['Reason']!='JobHeldUser'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--review',required=True);ap.add_argument('--review-sha256',required=True);ap.add_argument('--root-reviewed-release',action='store_true');a=ap.parse_args();assert a.root_reviewed_release
 rp=R/a.review;assert rp.resolve().is_relative_to(R/'.local/goal_t0_dispatch_independent_20261020T1530') and h(rp)==a.review_sha256
 review=json.loads(rp.read_bytes());assert review['status']=='passed' and review['entrypoint_sha256']==h(Path(__file__)) and not review.get('blockers')
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  sp=R/old.STATE;before=h(sp);s=old.read(sp);orig=copy.deepcopy(s);ctl=s['autonomous_training_v1'];p=s['pending_submission']
  assert p['job_id']==JID and p['status']=='acknowledged_held_job_not_released' and p['stage_key']==old.STAGE and p['request_token']=='cti-goal-t0-probe-v1:'+PIN
  assert p['authorization']==dict(path=old.AUTH,sha256=PIN) and old.read(R/B/'submission_result.json')==dict(returncode=0,stderr='',stdout='3050711\n',utc='2026-10-20T15:55:22.667575+00:00')
  assert p['actual_sbatch_argv']==old.read(R/B/'pending.json')['actual_sbatch_argv'] and p['reservation']==dict(path=B+'/reservation.json',sha256=h(R/B/'reservation.json'))
  assert ctl['reserved_GPU_slots']==1 and ctl['reservation_root_record']==p['reservation'] and ctl['root_submission_hold'] is None
  assert not any(str(j['job_id'])==JID or j.get('stage_key')==old.STAGE for j in s['registered_jobs'])
  assert not (R/B/'job_record.json').exists() and not (R/B/'release_command.json').exists() and not (R/B/'reconciliation_intent.json').exists() and not (P/old.BASE/'attempt01').exists()
  assert h(R/old.AUTH)==h(P/old.AUTH)==PIN
  for name,pin in old.SOURCES.items():assert h(P/old.BASE/'source'/name)==pin
  for role in ['root_review','independent_review']:
   rr=old.read(R/old.AUTH)[role];assert h(Path(rr['path']))==rr['sha256']
  owner=old.read(R/'results/formal_main_v2/autonomous_training/run_v1/owner.json');assert owner['owner_id']==ctl['owner_id'] and str(owner['coordinator_job_id'])==ctl['controller_job_id']=='3034538'
  lease=Path(owner['lock']);assert lease==R/'results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock'
  with lease.open('rb') as f:
   held=False
   try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
   except BlockingIOError:held=True
  assert held
  sl=c.Slurm(timeout=45);q=sl.run(['scontrol','show','job','-o',JID]);assert q.returncode==0
  v=fields(q.stdout);verify(v,p['request_token'],True)
  job=dict(job_id=JID,name=old.NAME,experiment='formal_main_v2',mode='engineering',stage_key=old.STAGE,suite='libero_goal',visual_tokens=256,training_seed=17,status='PENDING',gpus=1,source_root=str(old.S),source_sha256='dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e',run_root=str(P/old.BASE/'attempt01'),invocation=old.AUTH,invocation_sha256=PIN,submitted_utc=p['created_utc'],maximum_attempts=1,automatic_retry=False,wall_limit_seconds=1800,scientific_trials=0,final_states_opened=False,purpose='Bounded Goal task2/index42 engineering t0 diagnosis; original200 HOLD',downstream_gateway=dict(version='root-bounded-engineering-v1',request_token=p['request_token'],actual_sbatch_argv=p['actual_sbatch_argv'],automatic_retry=False),root_reservation=p['reservation'],dispatch_review=dict(path=a.review,sha256=a.review_sha256))
  obs=sl.observe(s['registered_jobs']+[job]);cap=c.capacity(s['registered_jobs']+[job],obs,'3034538')
  assert not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8 and JID in cap['occupied']
  assert obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0
  for jid in cap['occupied']:
   j=next(x for x in s['registered_jobs']+[job] if str(x['job_id'])==jid);g.check_observed_identity(j,obs['rows'][jid],obs['queue'].get(jid),c.TERMINAL)
  old.immutable(R/B/'reconciliation_intent.json',dict(kind='exact_ACK_reconciliation_no_new_submission',job_id=JID,review=dict(path=a.review,sha256=a.review_sha256),state_before_sha256=before,scheduler=obs,capacity=cap,scontrol_held=q.stdout,utc=old.utc()))
  old.immutable(R/B/'job_record.json',job);s['registered_jobs'].append(job);ctl['reserved_GPU_slots']=0;ctl['reservation_consumed_by_job']=JID;ctl.setdefault('engineering_probe_reservations_consumed',[]).append(dict(job_id=JID,reservation=p['reservation']))
  p['status']='registered_held_pending_release';c.atomic_json(sp,s,before);before=h(sp)
  release=sl.run(['scontrol','release',JID]);old.immutable(R/B/'release_command.json',dict(returncode=release.returncode,stdout=release.stdout,stderr=release.stderr,utc=old.utc()));assert release.returncode==0
  q=sl.run(['scontrol','show','job','-o',JID]);old.immutable(R/B/'released_identity.json',dict(returncode=q.returncode,stdout=q.stdout,stderr=q.stderr,utc=old.utc()));assert q.returncode==0;v=fields(q.stdout);verify(v,p['request_token'],False)
  job['status']=v['JobState'];s['pending_submission']=None;ctl['occupied_job_ids']=cap['occupied']
  assert s['formal_main_progress']==orig['formal_main_progress'] and ctl['blocked_pairs']==orig['autonomous_training_v1']['blocked_pairs'] and s['current_round_cost']==orig['current_round_cost']
  c.atomic_json(sp,s,before)
  out=dict(schema='formal_main_v2',kind='root_single_engineering_dispatch_exact_ack_reconciliation',status='registered_and_release_verified',job_id=JID,new_submissions=0,request_token=job['downstream_gateway']['request_token'],authorization=dict(path=old.AUTH,sha256=PIN),original_parser_failure_retained=True,parser_fix='space-delimited exact requested keys; observed AllocNode:Sid and TresPerNode gres:gpu:l40:1 retained',review=dict(path=a.review,sha256=a.review_sha256),job_record=old.ref(R/B/'job_record.json'),reserved_GPU_slots=0,occupied_jobs=cap['occupied'],maximum_gpu_occupancy=len(cap['occupied']),scientific_release=False,original200_still_HOLD=True,utc=old.utc(),state_after_sha256=h(sp))
  old.immutable(R/B/'receipt.json',out);print(json.dumps(out))
if __name__=='__main__':main()
